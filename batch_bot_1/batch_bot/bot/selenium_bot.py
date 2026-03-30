# ─────────────────────────────────────────────────────────────
#  bot/selenium_bot.py  –  Selenium automation for JotForm
#  All field IDs confirmed via diagnose_form.py on live form.
# ─────────────────────────────────────────────────────────────

import time
import threading

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException
)

import config
from bot.excel_handler import ExcelHandler
from bot.captcha_solver import CaptchaSolver


# ── Confirmed field IDs from live form ────────────────────────
ID_FIRST_NAME   = "first_11"
ID_LAST_NAME    = "last_11"
ID_PHONE_AREA   = "input_13_area"
ID_PHONE_NUMBER = "input_13_phone"
ID_EMAIL        = "input_7"
ID_PREFERRED    = "input_15"      # native <select>
ID_MONTH        = "month_16"      # Best Time to Call – month
ID_DAY          = "day_16"        # Best Time to Call – day
ID_YEAR         = "year_16"       # Best Time to Call – year
ID_HOUR         = "hour_16"       # Best Time to Call – hour
ID_MIN          = "min_16"        # Best Time to Call – minutes
ID_AMPM         = "ampm_16"       # Best Time to Call – AM/PM
ID_HOW_LOCATED  = "input_17"      # native <select>
ID_OTHER        = "input_18"      # conditional text input
ID_REASON       = "input_3"       # textarea
ID_DISCLAIMER   = "input_20_0"    # checkbox
ID_CAPTCHA      = "input_4"       # captcha text input
ID_SUBMIT       = "input_1"       # submit button


class BatchBot:
    """
    Iterates over every pending row in the Excel file and
    submits the JotForm once per record.
    """

    def __init__(
        self,
        excel_handler: ExcelHandler,
        log_callback=None,
        progress_callback=None,
        done_callback=None,
    ):
        self.excel   = excel_handler
        self.solver  = CaptchaSolver()
        self.driver  = None

        self._log      = log_callback      or (lambda msg: print(msg))
        self._progress = progress_callback or (lambda cur, total: None)
        self._done     = done_callback     or (lambda: None)

        self._pause_event = threading.Event()
        self._pause_event.set()
        self._stop_event = threading.Event()

    # ── Browser lifecycle ─────────────────────────────────────

    def _init_driver(self):
        if config.BROWSER.lower() == "firefox":
            opts = FirefoxOptions()
            if config.HEADLESS:
                opts.add_argument("--headless")
            self.driver = webdriver.Firefox(options=opts)
        else:
            opts = ChromeOptions()
            if config.HEADLESS:
                opts.add_argument("--headless")
            opts.add_argument("--disable-gpu")
            opts.add_argument("--no-sandbox")
            opts.add_argument("--window-size=1280,900")
            self.driver = webdriver.Chrome(options=opts)
        self.driver.set_page_load_timeout(config.PAGE_LOAD_WAIT + 10)

    def _close_driver(self):
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None

    # ── Control interface ─────────────────────────────────────

    def pause(self):
        self._pause_event.clear()
        self._log("[BOT] Pausing after current record ...")

    def resume(self):
        self._pause_event.set()
        self._log("[BOT] Resumed.")

    def stop(self):
        self._stop_event.set()
        self._pause_event.set()
        self._log("[BOT] Stop requested.")

    # ── Main run loop ─────────────────────────────────────────

    def run(self):
        self._stop_event.clear()
        self._pause_event.set()

        try:
            self._init_driver()
            pending = self.excel.get_pending_records()
            total   = self.excel.get_record_count()

            if not pending:
                self._log("[BOT] No pending records found.")
                return

            self._log(f"[BOT] Starting batch — {len(pending)} record(s) to process.")

            for row_index, record in pending:
                if self._stop_event.is_set():
                    self._log("[BOT] Stopped by user.")
                    break

                self._pause_event.wait()
                if self._stop_event.is_set():
                    self._log("[BOT] Stopped by user.")
                    break

                self._progress(row_index + 1, total)
                self._log(f"\n[BOT] ── Record {row_index + 1}/{total} ──────────────")

                try:
                    self._process_record(record)
                    self.excel.mark_success(row_index)
                    self._log(f"[BOT] ✅ Record {row_index + 1} → Success")
                except Exception as exc:
                    reason = str(exc)[:120]
                    self.excel.mark_failed(row_index, reason)
                    self._log(f"[BOT] ❌ Record {row_index + 1} → Failed: {reason}")

                if not self._stop_event.is_set():
                    time.sleep(config.BETWEEN_RECORDS)

        finally:
            self._close_driver()
            self._log("[BOT] Browser closed.")
            self._done()

    # ── Per-record form filling ───────────────────────────────

    def _process_record(self, record: dict):
        h    = self.excel
        wait = WebDriverWait(self.driver, config.PAGE_LOAD_WAIT)

        # 1. Navigate
        self._log("[BOT] Opening form ...")
        self.driver.get(config.FORM_URL)
        wait.until(EC.presence_of_element_located((By.ID, ID_FIRST_NAME)))
        time.sleep(1.5)

        # 2. First / Last name
        first = h.get_field(record, config.COL_FIRST_NAME)
        last  = h.get_field(record, config.COL_LAST_NAME)
        self._log(f"[BOT] Name: {first} {last}")
        self._fill_by_id(ID_FIRST_NAME, first)
        self._fill_by_id(ID_LAST_NAME,  last)

        # 3. Phone
        area  = h.get_field(record, config.COL_PHONE_AREA)
        phone = h.get_field(record, config.COL_PHONE_NUMBER)
        self._log(f"[BOT] Phone: ({area}) {phone}")
        self._fill_by_id(ID_PHONE_AREA,   area)
        self._fill_by_id(ID_PHONE_NUMBER, phone)

        # 4. Email
        email = h.get_field(record, config.COL_EMAIL)
        self._log(f"[BOT] Email: {email}")
        self._fill_by_id(ID_EMAIL, email)

        # 5. Preferred Contact  (native <select>)
        preferred = h.get_field(record, config.COL_PREFERRED_CONTACT)
        self._log(f"[BOT] Preferred contact: {preferred}")
        self._select_by_id(ID_PREFERRED, preferred)

        # 6. Best Time to Call
        month = h.get_field(record, config.COL_BEST_TIME_MONTH)
        day   = h.get_field(record, config.COL_BEST_TIME_DAY)
        year  = h.get_field(record, config.COL_BEST_TIME_YEAR)
        hour  = h.get_field(record, config.COL_BEST_TIME_HOUR)
        mins  = h.get_field(record, config.COL_BEST_TIME_MIN)
        ampm  = h.get_field(record, config.COL_BEST_TIME_AMPM)
        self._log(f"[BOT] Best time: {month}/{day}/{year} {hour}:{mins} {ampm}")
        if month: self._fill_by_id(ID_MONTH, month)
        if day:   self._fill_by_id(ID_DAY,   day)
        if year:  self._fill_by_id(ID_YEAR,  year)
        if hour:  self._select_by_id(ID_HOUR, hour)
        if mins:  self._select_by_id(ID_MIN,  mins)
        if ampm:  self._select_by_id(ID_AMPM, ampm)

        # 7. How did you locate us?  (native <select>)
        how_located = h.get_field(record, config.COL_HOW_LOCATED)
        self._log(f"[BOT] How located: {how_located}")
        # Normalise: if user wrote "Other" add the "?" to match option value
        how_val = "Other?" if how_located.lower() == "other" else how_located
        self._select_by_value(ID_HOW_LOCATED, how_val)

        # 8. Other? conditional text field
        if how_located.lower() in ("other", "other?"):
            other_text = h.get_field(record, config.COL_OTHER_LOCATED)
            self._log(f"[BOT] Other text: {other_text}")
            # Wait for the field to become visible after selecting Other?
            try:
                wait.until(EC.visibility_of_element_located((By.ID, ID_OTHER)))
                self._fill_by_id(ID_OTHER, other_text)
            except TimeoutException:
                self._log("[BOT] Warning: Other? text field did not appear.")

        # 9. Reason
        reason = h.get_field(record, config.COL_REASON)
        self._log("[BOT] Filling reason ...")
        self._fill_by_id(ID_REASON, reason)

        # 10. Disclaimer checkbox
        if h.is_disclaimer_agreed(record):
            self._log("[BOT] Ticking disclaimer ...")
            cb = self.driver.find_element(By.ID, ID_DISCLAIMER)
            if not cb.is_selected():
                cb.click()
        else:
            self._log("[BOT] DisclaimerAgreement=FALSE — skipping checkbox.")

        # 11. Captcha
        self._log("[BOT] Solving captcha ...")
        captcha_text = self.solver.solve(self.driver, self._log)
        self._fill_by_id(ID_CAPTCHA, captcha_text)

        # 12. Submit
        self._log("[BOT] Submitting ...")
        self.driver.find_element(By.ID, ID_SUBMIT).click()
        self._wait_for_confirmation()

    # ── Low-level helpers ──────────────────────────────────────

    def _fill_by_id(self, element_id: str, value: str):
        """Clear and type into an input/textarea by exact ID."""
        el = self.driver.find_element(By.ID, element_id)
        el.clear()
        el.send_keys(value)

    def _select_by_id(self, element_id: str, visible_text: str):
        """Choose an option by visible text in a native <select> by ID."""
        if not visible_text:
            return
        Select(self.driver.find_element(By.ID, element_id)).select_by_visible_text(visible_text)

    def _select_by_value(self, element_id: str, value: str):
        """Choose an option by its value attribute in a native <select> by ID."""
        if not value:
            return
        Select(self.driver.find_element(By.ID, element_id)).select_by_value(value)

    def _wait_for_confirmation(self):
        """Wait for JotForm's 'Thank you' confirmation page."""
        wait = WebDriverWait(self.driver, config.SUBMIT_WAIT)
        try:
            wait.until(lambda d:
                "thank" in d.page_source.lower()
                or "submitted" in d.page_source.lower()
                or "received" in d.page_source.lower()
                or "confirmation" in d.page_source.lower()
            )
            self._log("[BOT] Confirmation page detected.")
        except TimeoutException:
            raise TimeoutException(
                f"No confirmation page within {config.SUBMIT_WAIT}s — "
                "captcha answer may be wrong (demo mode used)."
            )
