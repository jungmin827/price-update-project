"""Parsing and networking helpers extracted from pricebot_v3.

Provides price parsing, shipping parsing, DOM extraction helpers, and
an HTTP GET with retries/backoff. These functions are designed to be
imported by the runner.
"""
from typing import Optional, Iterable, Tuple
import re
import time
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup
import requests

from project.config.settings import settings

# Timezone for logging (KST)
KST = timezone(timedelta(hours=9))


def current_time_str() -> str:
    return datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")


def to_int_price(text: Optional[str]) -> Optional[int]:
    if not text:
        return None
    digits = re.sub(r"[^0-9]", "", text)
    return int(digits) if digits else None


def parse_price(text: Optional[str]) -> Optional[int]:
    if not text:
        return None
    digits = re.sub(r"[^0-9]", "", text)
    return int(digits) if digits else None


def parse_shipping(text: Optional[str]) -> Optional[int]:
    if text is None:
        return None
    stripped = text.strip()
    if not stripped:
        return None
    lowered = stripped.lower()
    for kw in ("무료", "포함", "무배"):
        if kw in lowered:
            return 0
    if "원" not in stripped:
        return None
    m = re.search(r"([\d,]+)\s*원", stripped)
    if m:
        num = m.group(1).replace(",", "")
        try:
            return int(num)
        except ValueError:
            return None
    return None


def extract_text(soup: BeautifulSoup, selectors: Iterable[str]) -> Optional[str]:
    for css in selectors:
        if not css:
            continue
        try:
            el = soup.select_one(css)
        except Exception:
            el = None
        if el:
            text = el.get_text(strip=True)
            if text:
                return text
    return None


def extract_price_with_coupon(
    soup: BeautifulSoup, coupon_selectors: Iterable[str], price_selectors: Iterable[str]
) -> Optional[int]:
    for css in coupon_selectors:
        if not css:
            continue
        try:
            el = soup.select_one(css)
        except Exception:
            el = None
        if el:
            price = parse_price(el.get_text(strip=True))
            if price is not None:
                return price
    for css in price_selectors:
        if not css:
            continue
        try:
            el = soup.select_one(css)
        except Exception:
            el = None
        if el:
            price = parse_price(el.get_text(strip=True))
            if price is not None:
                return price
    return None


def extract_shipping_cost(soup: BeautifulSoup, ship_selectors: Iterable[str]):
    ship_text = extract_text(soup, ship_selectors)
    ship_value = parse_shipping(ship_text)
    return ship_text, ship_value


def determine_stock(price_val: Optional[int], stock_text: Optional[str]) -> str:
    if price_val is None:
        return "OutOfStock"
    if stock_text:
        lower = stock_text.lower()
        if any(keyword in lower for keyword in ["품절", "sold out", "out of stock", "재고없음", "일시품절"]):
            return "OutOfStock"
        if any(keyword in lower for keyword in ["구매", "재고", "있음", "in stock", "available"]):
            return "InStock"
    return "InStock"


def sleep_ms(ms: int) -> None:
    time.sleep(ms / 1000.0)


def http_get(url: str, ua: str, timeout: int, retry: int, backoff_ms: int) -> Tuple[str, int]:
    last_error = None
    headers = {"User-Agent": ua} if ua else settings.DEFAULT_HEADERS
    for attempt in range(retry + 1):
        try:
            r = requests.get(url, headers=headers, timeout=timeout)
            status = r.status_code
            if status == 200:
                return r.text, status
            elif status in (403, 429, 503):
                last_error = f"HTTP {status}"
                sleep_ms(backoff_ms * (attempt + 1))
            else:
                return "", status
        except Exception as exc:
            last_error = str(exc)
            sleep_ms(backoff_ms * (attempt + 1))
    raise RuntimeError(f"HTTP GET failed: {last_error}")

