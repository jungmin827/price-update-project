"""Higher-level sheet writers for change and runlog rows.

These helpers use the SheetsClient append_row interface and centralize
row layout so the runner stays focused on orchestration.
"""
from typing import Optional, Dict, Any
from project.sheets.client import SheetsClient

# sheet name constants (keep in sync with runner)
SHEET_CHANGES = "최저가변동"
SHEET_RUNLOG = "실행로그"


def append_change_row(sc: SheetsClient, *, timestamp: str, product_id: str, product_name: str, seller: str,
                      url: str, prev_price: Optional[int], curr_price: Optional[int], ship_cost: Optional[int],
                      diff_str: str, change_type: str, prev_stock: str, curr_stock: str, memo: str) -> None:
    shipping = ship_cost if ship_cost is not None else 0
    current_total = 0
    if curr_price is not None:
        current_total = curr_price + shipping
    row = [
        timestamp,
        product_id,
        product_name,
        seller,
        url,
        prev_price if prev_price is not None else "",
        curr_price if curr_price is not None else "",
        current_total if curr_price is not None else "",
        diff_str,
        change_type,
        prev_stock,
        curr_stock,
        shipping,
        memo,
    ]
    sc.append_row(SHEET_CHANGES, row, value_input_option="USER_ENTERED")


def append_runlog(sc: SheetsClient, info: Dict[str, Any]) -> None:
    row = [
        info.get("batch_id", ""),
        info.get("start_time", ""),
        info.get("end_time", ""),
        info.get("duration", ""),
        info.get("total", ""),
        info.get("success", ""),
        info.get("fail", ""),
        info.get("http_calls", ""),
        info.get("avg_response_ms", ""),
        info.get("err_429", ""),
        info.get("err_403", ""),
        info.get("err_timeout", ""),
        info.get("err_selector", ""),
        info.get("domain_summary", ""),
        info.get("memo", ""),
    ]
    sc.append_row(SHEET_RUNLOG, row, value_input_option="USER_ENTERED")
