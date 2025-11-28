from pathlib import Path
from dotenv import load_dotenv
import os
from types import SimpleNamespace

# Load local .env if present (development convenience)
env_path = Path(__file__).resolve().parents[1] / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Lightweight settings object reading directly from environment variables.
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)

_settings = {
    "SPREADSHEET_ID": os.getenv("SPREADSHEET_ID"),
    "SERVICE_ACCOUNT_FILE": os.getenv("SERVICE_ACCOUNT_FILE", "brand-resell-service-account.json"),
    "DEFAULT_USER_AGENT": os.getenv("DEFAULT_USER_AGENT", DEFAULT_USER_AGENT),
    "DEFAULT_TIMEOUT": int(os.getenv("DEFAULT_TIMEOUT", "12")),
    "DEFAULT_RETRY": int(os.getenv("DEFAULT_RETRY", "2")),
    "DEFAULT_BACKOFF_MS": int(os.getenv("DEFAULT_BACKOFF_MS", "600")),
    "DEFAULT_SPREAD_DIFF": int(os.getenv("DEFAULT_SPREAD_DIFF", "500")),
    "DEFAULT_HEADERS": {"User-Agent": os.getenv("DEFAULT_USER_AGENT", DEFAULT_USER_AGENT)},
}

settings = SimpleNamespace(**_settings)
