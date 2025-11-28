"""Central runner module: migrated core logic from pricebot_v3 into a reusable function.

This module depends on project.parsers, project.rules.loader, and
project.sheets.client.SheetsClient. It mirrors the original script's
behaviour but keeps state local to the run_once() function.
"""
from typing import Optional, Dict, Any
from datetime import datetime

from project.config.settings import settings
from project.sheets.client import SheetsClient
from project import parsers
from project.rules import load_rules_from_rows, select_rule
from project.sheets import writer as sheets_writer
from bs4 import BeautifulSoup

# Worksheet names (same as original)
SHEET_PRODUCTS = "1.상품리스트"
SHEET_SETTINGS = "설정"
SHEET_CHANGES = "최저가변동"
SHEET_RUNLOG = "실행로그"

# Starting row for product list (1-indexed)
START_ROW = 6

# Column indices (1-indexed) for product sheet
COL_E_ID = 5   # 관리번호
COL_F_NAME = 6  # 상품명
COL_I_PREV = 9  # 이전가 (기존 최저가; 배송비 포함)
COL_J_SELLER = 10  # 판매처 (기존)
COL_K_URL = 11  # 조사 URL


# NOTE: append helpers moved to project.sheets.writer


def run_once() -> None:
    sc = SheetsClient()
    ws_products = sc.worksheet(SHEET_PRODUCTS)
    ws_settings = sc.worksheet(SHEET_SETTINGS)
    ws_changes = sc.worksheet(SHEET_CHANGES)
    ws_runlog = sc.worksheet(SHEET_RUNLOG)

    # Load settings
    rows = ws_settings.get_all_values()
    rules_map, _header = load_rules_from_rows(rows)

    product_rows = ws_products.get_all_values()
    total_rows = len(product_rows)

    total = success = fail = 0
    http_calls = 0
    err_429 = err_403 = err_timeout = err_selector = 0
    price_changes = 0
    stock_changes = 0

    start_ts = datetime.now().timestamp()

    try:
        existing_changes = ws_changes.get_all_values()
    except Exception:
        existing_changes = []
    start_row_index = len(existing_changes) + 1
    current_row_index = start_row_index

    for r in range(START_ROW - 1, total_rows):
        row = product_rows[r]
        product_id = row[COL_E_ID - 1].strip() if len(row) >= COL_E_ID else ""
        product_name = row[COL_F_NAME - 1].strip() if len(row) >= COL_F_NAME else ""
        prev_price_str = row[COL_I_PREV - 1].strip() if len(row) >= COL_I_PREV else ""
        prev_seller = row[COL_J_SELLER - 1].strip() if len(row) >= COL_J_SELLER else ""
        url = row[COL_K_URL - 1].strip() if len(row) >= COL_K_URL else ""
        if not (product_id or product_name or url):
            continue
        total += 1
        if not url:
            sheets_writer.append_change_row(
                sc,
                timestamp=parsers.current_time_str(),
                product_id=product_id,
                product_name=product_name,
                seller=prev_seller,
                url="",
                prev_price=parsers.to_int_price(prev_price_str),
                curr_price=None,
                ship_cost=None,
                diff_str="",
                change_type="",
                prev_stock="InStock",
                curr_stock="OutOfStock",
                memo="URL 없음/접속불가",
            )
            if prev_price_str:
                stock_changes += 1
            success += 1
            continue

        rule = select_rule(rules_map, url)

        # Resolve rule fallbacks
        timeout = rule.get("timeout") or settings.DEFAULT_TIMEOUT
        retry = rule.get("retry") or settings.DEFAULT_RETRY
        backoff_ms = rule.get("backoff_ms") or settings.DEFAULT_BACKOFF_MS
        ua = rule.get("ua") or settings.DEFAULT_HEADERS.get("User-Agent")
        gap_ms = rule.get("gap_ms") or 0

        if gap_ms > 0:
            parsers.sleep_ms(gap_ms)

        try:
            html, status_code = parsers.http_get(url=url, ua=ua, timeout=timeout, retry=retry, backoff_ms=backoff_ms)
            http_calls += 1
            soup = BeautifulSoup(html, "html.parser")

            price_val = parsers.extract_price_with_coupon(soup, rule.get("coupon_css", []), rule.get("price_css", []))
            ship_text, ship_val = parsers.extract_shipping_cost(soup, rule.get("ship_css", []))
            stock_text = parsers.extract_text(soup, rule.get("stock_css", []))
            curr_stock = parsers.determine_stock(price_val, stock_text)
            prev_price_val = parsers.to_int_price(prev_price_str) if prev_price_str else None
            effective_ship = ship_val if ship_val is not None else 0
            curr_total = (price_val if price_val is not None else 0) + effective_ship

            price_changed = False
            change_type = ""
            diff_str = ""
            if prev_price_val is not None and price_val is not None:
                diff = curr_total - prev_price_val
                threshold = rule.get("spread") or settings.DEFAULT_SPREAD_DIFF
                if abs(diff) >= threshold:
                    price_changed = True
                    change_type = "가격상승" if diff > 0 else "가격하락"
                    diff_str = f"{diff:+d}"
            elif price_val is None:
                change_type = "품절"

            stock_changed = False
            if prev_price_val is not None:
                if curr_stock == "OutOfStock":
                    stock_changed = True
                    change_type = (change_type + ", " if change_type else "") + "입고→품절"

            if price_changed or stock_changed or price_val is None:
                memo_parts = []
                if price_val is None:
                    memo_parts.append("가격파싱실패")
                if ship_text is None:
                    memo_parts.append("배송비추출실패")
                memo = "; ".join(memo_parts)
                sheets_writer.append_change_row(
                    sc,
                    timestamp=parsers.current_time_str(),
                    product_id=product_id,
                    product_name=product_name,
                    seller=rule.get("shop", prev_seller),
                    url=url,
                    prev_price=prev_price_val,
                    curr_price=price_val,
                    ship_cost=ship_val,
                    diff_str=diff_str,
                    change_type=change_type,
                    prev_stock="InStock",
                    curr_stock=curr_stock,
                    memo=memo,
                )
                try:
                    if diff_str:
                        cell_a1 = f"I{current_row_index}"
                        if diff_str.startswith("-"):
                            ws_changes.format(cell_a1, {"textFormat": {"bold": True, "foregroundColor": {"red": 0.0, "green": 0.0, "blue": 1.0}}})
                        elif diff_str.startswith("+"):
                            ws_changes.format(cell_a1, {"textFormat": {"bold": True, "foregroundColor": {"red": 1.0, "green": 0.0, "blue": 0.0}}})
                except Exception:
                    # Formatting may not be supported; ignore
                    pass

                if price_changed:
                    price_changes += 1
                if stock_changed or price_val is None:
                    stock_changes += 1
                current_row_index += 1
            success += 1
        except RuntimeError as e:
            err_msg = str(e)
            if "429" in err_msg:
                err_429 += 1
            elif "403" in err_msg:
                err_403 += 1
            elif "timeout" in err_msg.lower():
                err_timeout += 1
            else:
                err_selector += 1
            sheets_writer.append_change_row(
                sc,
                timestamp=parsers.current_time_str(),
                product_id=product_id,
                product_name=product_name,
                seller=prev_seller,
                url=url,
                prev_price=parsers.to_int_price(prev_price_str),
                curr_price=None,
                ship_cost=None,
                diff_str="",
                change_type="",
                prev_stock="InStock",
                curr_stock="OutOfStock",
                memo=f"접속오류:{err_msg}",
            )
            fail += 1
        except Exception as e:
            sheets_writer.append_change_row(
                sc,
                timestamp=parsers.current_time_str(),
                product_id=product_id,
                product_name=product_name,
                seller=prev_seller,
                url=url,
                prev_price=parsers.to_int_price(prev_price_str),
                curr_price=None,
                ship_cost=None,
                diff_str="",
                change_type="",
                prev_stock="InStock",
                curr_stock="OutOfStock",
                memo=f"예외:{e}",
            )
            fail += 1

    end_ts = datetime.now().timestamp()
    duration_s = round(end_ts - start_ts, 2)
    runlog_entry = {
        "batch_id": datetime.now().astimezone(parsers.KST).strftime("%Y%m%d-%H%M%S"),
        "start_time": datetime.fromtimestamp(start_ts, tz=parsers.KST).strftime("%Y-%m-%d %H:%M:%S"),
        "end_time": datetime.fromtimestamp(end_ts, tz=parsers.KST).strftime("%Y-%m-%d %H:%M:%S"),
        "duration": duration_s,
        "total": total,
        "success": success,
        "fail": fail,
        "http_calls": http_calls,
        "avg_response_ms": "",
        "err_429": err_429,
        "err_403": err_403,
        "err_timeout": err_timeout,
        "err_selector": err_selector,
        "domain_summary": "",
        "memo": f"가격변동:{price_changes} / 재고변동:{stock_changes}",
    }
    sheets_writer.append_runlog(sc, runlog_entry)

    try:
        header_row = ws_changes.get('A1:1')[0] if ws_changes.get('A1:1') else []
        num_cols = len(header_row) if header_row else 14
        blank_row = ["" for _ in range(num_cols)]
        ws_changes.append_row(blank_row, value_input_option="USER_ENTERED")
    except Exception:
        pass


if __name__ == "__main__":
    run_once()
    print("Price tracking run completed.")
