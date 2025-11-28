Project module skeleton for pricebot refactor

This folder contains an initial refactor skeleton for the price tracking
project. It is intentionally lightweight and designed to be expanded.

Structure:
- config: centralized settings using pydantic
- sheets: Google Sheets helper wrapper
- scraper: static and browser scrapers
- rules: domain rule loader
- ui: Streamlit control panel (minimal)
- agent: AI/LLM automation skeleton
- jobs: scheduler wrapper

How to try:
1. Create a virtualenv and install requirements:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r project/requirements.txt
```

2. Create a `.env` in the repository root with SPREADSHEET_ID and
SERVICE_ACCOUNT_FILE set (or set the environment variables).

3. Run the CLI info command:

```bash
python3 -m project.cli info
```

Next steps:
- Wire the existing `pricebot_v3.py` logic into `project` modules.
- Add unit tests for parsers and rule matching.
- Implement Playwright-based scraper and integrate into run flow.
# sheets package
# ...existing code...

