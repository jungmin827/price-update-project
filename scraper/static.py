"""Static (requests + BeautifulSoup) scraping utilities."""
from typing import Tuple, Optional, Iterable
import requests
from bs4 import BeautifulSoup


class StaticScraper:
    def __init__(self, user_agent: str, timeout: int = 12, retry: int = 2, backoff_ms: int = 600):
        self.headers = {"User-Agent": user_agent}
        self.timeout = timeout
        self.retry = retry
        self.backoff_ms = backoff_ms

    def http_get(self, url: str) -> Tuple[str, int]:
        last_err = None
        for attempt in range(self.retry + 1):
            try:
                r = requests.get(url, headers=self.headers, timeout=self.timeout)
                if r.status_code == 200:
                    return r.text, r.status_code
                last_err = f"HTTP {r.status_code}"
            except Exception as e:
                last_err = str(e)
        raise RuntimeError(f"http_get failed: {last_err}")

    def fetch_soup(self, url: str) -> Tuple[BeautifulSoup, int]:
        html, status = self.http_get(url)
        soup = BeautifulSoup(html, "html.parser")
        return soup, status

    def extract_text(self, soup: BeautifulSoup, selectors: Iterable[str]) -> Optional[str]:
        from bs4 import BeautifulSoup as _BS
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

