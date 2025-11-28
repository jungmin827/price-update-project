# scraper package
# Exposes a simple high-level fetch() helper that chooses a backend later.
from .static import StaticScraper
from .browser import BrowserScraper

__all__ = ["StaticScraper", "BrowserScraper"]

