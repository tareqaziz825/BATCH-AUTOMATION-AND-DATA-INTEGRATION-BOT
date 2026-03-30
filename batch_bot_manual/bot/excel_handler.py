# ─────────────────────────────────────────────────────────────
#  bot/excel_handler.py  –  Read records from Excel/CSV and
#                           write Status updates back to disk.
# ─────────────────────────────────────────────────────────────

import pandas as pd
from pathlib import Path
import config


class ExcelHandler:
    """
    Loads an Excel (.xlsx) or CSV file into a DataFrame,
    exposes records for the bot to process, and writes
    Status updates back to the original file.
    """

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.df: pd.DataFrame = pd.DataFrame()
        self._load()

    # ── Loading ──────────────────────────────────────────────

    def _load(self):
        """Read the file into a DataFrame and normalise the Status column."""
        ext = self.file_path.suffix.lower()

        if ext in (".xlsx", ".xls"):
            self.df = pd.read_excel(self.file_path, dtype=str, engine="openpyxl")
        elif ext == ".csv":
            self.df = pd.read_csv(self.file_path, dtype=str)
        else:
            raise ValueError(f"Unsupported file type: {ext}. Use .xlsx or .csv")

        # Strip accidental whitespace from headers
        self.df.columns = self.df.columns.str.strip()

        # Ensure Status column exists
        if config.COL_STATUS not in self.df.columns:
            self.df[config.COL_STATUS] = "Pending"

        # FIX #1: Replace deprecated fillna(inplace=True) with direct assignment
        self.df[config.COL_STATUS] = self.df[config.COL_STATUS].fillna("Pending")
        self.df[config.COL_STATUS] = self.df[config.COL_STATUS].str.strip()

    def reload(self):
        """Re-read file from disk (useful after external edits)."""
        self._load()

    # ── Accessors ─────────────────────────────────────────────

    def get_all_records(self) -> list[dict]:
        """Return every row as a list of dicts."""
        return self.df.to_dict(orient="records")

    def get_pending_records(self) -> list[tuple[int, dict]]:
        """
        Return (original_index, record) tuples for rows whose
        Status is not 'Success'.
        """
        pending = self.df[self.df[config.COL_STATUS] != "Success"]
        return list(pending.iterrows())

    def get_record_count(self) -> int:
        return len(self.df)

    def get_record(self, index: int) -> dict:
        return self.df.iloc[index].to_dict()

    # ── Status Updates ────────────────────────────────────────

    def mark_success(self, index: int):
        """Mark a row as successfully submitted."""
        self.df.at[index, config.COL_STATUS] = "Success"
        self._save()

    def mark_failed(self, index: int, reason: str = ""):
        """Mark a row as failed, optionally recording the reason."""
        msg = "Failed" + (f": {reason}" if reason else "")
        self.df.at[index, config.COL_STATUS] = msg
        self._save()

    def reset_status(self, index: int):
        """Reset a row back to Pending."""
        self.df.at[index, config.COL_STATUS] = "Pending"
        self._save()

    # ── Persistence ───────────────────────────────────────────

    def _save(self):
        """
        Write the DataFrame back to the original file.

        FIX #2: Always specify engine='openpyxl' for .xlsx/.xls so that
        openpyxl is used explicitly, preventing silent engine-mismatch
        errors on some pandas versions.
        """
        ext = self.file_path.suffix.lower()
        if ext in (".xlsx", ".xls"):
            self.df.to_excel(self.file_path, index=False, engine="openpyxl")
        elif ext == ".csv":
            self.df.to_csv(self.file_path, index=False)

    # ── Helpers ───────────────────────────────────────────────

    def get_field(self, record: dict, col_const: str, default: str = "") -> str:
        """
        Safely retrieve a value from a record dict using a
        config column-name constant.  Always returns a string.
        """
        val = record.get(col_const, default)
        if pd.isna(val) or val is None:
            return default
        return str(val).strip()

    def is_disclaimer_agreed(self, record: dict) -> bool:
        """Return True when DisclaimerAgreement is 'TRUE' (case-insensitive)."""
        raw = self.get_field(record, config.COL_DISCLAIMER, "false")
        return raw.lower() in ("true", "1", "yes")