"""Google Sheets client wrapper.

Provides a minimal wrapper around gspread and service account credentials
using settings from project.config.settings.
"""
from typing import Optional, Any, List
from pathlib import Path
import gspread
from google.oauth2.service_account import Credentials
from project.config.settings import settings

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


class SheetsClient:
    def __init__(self, spreadsheet_id: Optional[str] = None, service_account_file: Optional[str] = None):
        self.spreadsheet_id = spreadsheet_id or settings.SPREADSHEET_ID
        self.service_account_file = service_account_file or settings.SERVICE_ACCOUNT_FILE
        self.gc = None
        self._open()

    def _open(self) -> None:
        if not self.spreadsheet_id:
            raise RuntimeError("SPREADSHEET_ID is not set in settings")
        creds = Credentials.from_service_account_file(self.service_account_file, scopes=SCOPES)
        self.gc = gspread.authorize(creds)
        self.sheet = self.gc.open_by_key(self.spreadsheet_id)

    def worksheet(self, name: str):
        return self.sheet.worksheet(name)

    def get_all_values(self, sheet_name: str) -> List[List[str]]:
        return self.worksheet(sheet_name).get_all_values()

    def append_row(self, sheet_name: str, row: List[Any], value_input_option: str = "USER_ENTERED") -> None:
        self.worksheet(sheet_name).append_row(row, value_input_option=value_input_option)

