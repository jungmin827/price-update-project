"""Browser-based scraper skeleton (Playwright preferred).

This module provides a thin wrapper that will use Playwright if
available. Installing and configuring Playwright is outside the scope of
this skeleton. The implementation is intentionally minimal to avoid a
hard dependency at this stage.
"""


class BrowserScraper:
    def __init__(self, headless: bool = True):
        self.headless = headless

    def fetch_page_html(self, url: str) -> str:
        """Fetch rendered HTML using Playwright if available.

        Raises RuntimeError if Playwright is not installed.
        """
        try:
            from playwright.sync_api import sync_playwright
        except Exception as e:
            raise RuntimeError("Playwright is not installed; install with `pip install playwright` and run `playwright install`")
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=self.headless)
            page = browser.new_page()
            page.goto(url, wait_until="networkidle")
            html = page.content()
            browser.close()
            return html
