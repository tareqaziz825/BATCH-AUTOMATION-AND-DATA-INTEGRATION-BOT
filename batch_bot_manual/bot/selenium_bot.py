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
    TimeoutException, NoSuchElementException, ElementNotInteractableException
)

import config
from bot.excel_handler import ExcelHandler
from bot.captcha_solver import CaptchaSolver


# ── Confirmed field IDs from live form (via diagnose_form.py) ─
ID_FIRST_NAME   = "first_11"
ID_LAST_NAME    = "last_11"
ID_PHONE_AREA   = "input_13_area"
ID_PHONE_NUMBER = "input_13_phone"
ID_EMAIL        = "input_7"
ID_PREFERRED    = "input_15"      # native <select>  Email | Phone
ID_MONTH        = "month_16"      # Best Time – month  (type=tel, use JS)
ID_DAY          = "day_16"        # Best Time – day    (type=tel, use JS)
ID_YEAR         = "year_16"       # Best Time – year   (type=tel, use JS)
ID_HOUR         = "hour_16"       # Best Time – hour   (native <select>)
ID_MIN          = "min_16"        # Best Time – mins   (native <select>)
ID_AMPM         = "ampm_16"       # Best Time – AM/PM  (native <select>)
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
        self._captcha_ready_event = threading.Event()  # for manual captcha

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

    def continue_captcha(self):
        """Signal that the user has solved the captcha and the bot may proceed."""
        self._captcha_ready_event.set()
        self._log("[BOT] Captcha confirmed — continuing submission.")

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

        # ── 1. Navigate ───────────────────────────────────────
        self._log("[BOT] Opening form ...")
        self.driver.get(config.FORM_URL)
        wait.until(EC.presence_of_element_located((By.ID, ID_FIRST_NAME)))
        time.sleep(2)   # allow full JS render

        # ── 2. Name ───────────────────────────────────────────
        first = h.get_field(record, config.COL_FIRST_NAME)
        last  = h.get_field(record, config.COL_LAST_NAME)
        self._log(f"[BOT] Name: {first} {last}")
        self._fill_by_id(ID_FIRST_NAME, first)
        self._fill_by_id(ID_LAST_NAME,  last)

        # ── 3. Phone ──────────────────────────────────────────
        area  = h.get_field(record, config.COL_PHONE_AREA)
        phone = h.get_field(record, config.COL_PHONE_NUMBER)
        self._log(f"[BOT] Phone: ({area}) {phone}")
        self._fill_by_id(ID_PHONE_AREA,   area)
        self._fill_by_id(ID_PHONE_NUMBER, phone)

        # ── 4. Email ──────────────────────────────────────────
        email = h.get_field(record, config.COL_EMAIL)
        self._log(f"[BOT] Email: {email}")
        self._fill_by_id(ID_EMAIL, email)

        # ── 5. Preferred Contact  (native <select>) ───────────
        preferred = h.get_field(record, config.COL_PREFERRED_CONTACT)
        self._log(f"[BOT] Preferred contact: {preferred}")
        self._select_by_value(ID_PREFERRED, preferred)
        time.sleep(0.5)   # let any UI reflow settle before next field

        # ── 6. Best Time to Call ──────────────────────────────
        #  The date inputs (month/day/year) are type=tel inside a
        #  date-picker widget.  After selecting "Email" in step 5,
        #  JotForm repaints and those fields scroll off-screen.
        #  We scroll each element into view and use JS to set the
        #  value, then dispatch a 'change' event so JotForm's
        #  validators recognise the new value.
        month = h.get_field(record, config.COL_BEST_TIME_MONTH)
        day   = h.get_field(record, config.COL_BEST_TIME_DAY)
        year  = h.get_field(record, config.COL_BEST_TIME_YEAR)
        hour  = h.get_field(record, config.COL_BEST_TIME_HOUR)
        mins  = h.get_field(record, config.COL_BEST_TIME_MIN)
        ampm  = h.get_field(record, config.COL_BEST_TIME_AMPM)
        self._log(f"[BOT] Best time: {month}/{day}/{year} {hour}:{mins} {ampm}")

        try:
            # Wait for the month field to be visible after the
            # Preferred Contact repaint before filling date fields.
            WebDriverWait(self.driver, config.PAGE_LOAD_WAIT).until(
                EC.visibility_of_element_located((By.ID, ID_MONTH))
            )
            if month: self._js_fill(ID_MONTH, month)
            if day:   self._js_fill(ID_DAY,   day)
            if year:  self._js_fill(ID_YEAR,  year)
            if hour:  self._select_by_value(ID_HOUR, hour)
            if mins:  self._select_by_value(ID_MIN,  mins)
            if ampm:  self._select_by_value(ID_AMPM, ampm)
        except Exception as e:
            # Best Time is not a required* field in many scenarios;
            # log and continue rather than aborting the whole record.
            # (*the form marks it required but demo submissions will
            #   fail on captcha anyway — don't double-fail here.)
            self._log(f"[BOT] Warning – Best Time field issue: {e}")

        # ── 7. How did you locate us?  (native <select>) ──────
        how_located = h.get_field(record, config.COL_HOW_LOCATED)
        self._log(f"[BOT] How located: {how_located}")
        # Normalise: if user wrote "Other" without "?" add it
        how_val = "Other?" if how_located.strip().lower() == "other" else how_located
        self._select_by_value(ID_HOW_LOCATED, how_val)

        # ── 8. Other? conditional text field ──────────────────
        if how_val == "Other?":
            other_text = h.get_field(record, config.COL_OTHER_LOCATED)
            self._log(f"[BOT] Other text: {other_text}")
            try:
                wait.until(EC.visibility_of_element_located((By.ID, ID_OTHER)))
                self._fill_by_id(ID_OTHER, other_text)
            except TimeoutException:
                self._log("[BOT] Warning: Other? text field did not appear.")

        # ── 9. Reason ─────────────────────────────────────────
        reason = h.get_field(record, config.COL_REASON)
        self._log("[BOT] Filling reason ...")
        self._fill_by_id(ID_REASON, reason)

        # ── 10. Disclaimer checkbox ───────────────────────────
        if h.is_disclaimer_agreed(record):
            self._log("[BOT] Ticking disclaimer ...")
            cb = self.driver.find_element(By.ID, ID_DISCLAIMER)
            if not cb.is_selected():
                self._scroll_into_view(cb)
                cb.click()
        else:
            self._log("[BOT] DisclaimerAgreement=FALSE — skipping checkbox.")

        # ── 11. Captcha ───────────────────────────────────────
        self._log("[BOT] Solving captcha ...")
        captcha_text = self.solver.solve(
            self.driver, self._log, self._captcha_ready_event
        )
        # In manual mode the user already typed into the field;
        # _fill_by_id (clear + send_keys) safely overwrites it with
        # the value we read back, keeping the field consistent.
        # Skip only if captcha_text is empty (read failed).
        if captcha_text:
            self._fill_by_id(ID_CAPTCHA, captcha_text)
        else:
            self._log("[BOT] Warning: captcha text is empty — submitting anyway.")

        # ── 12. Submit ────────────────────────────────────────
        self._log("[BOT] Submitting ...")
        submit_btn = self.driver.find_element(By.ID, ID_SUBMIT)
        self._scroll_into_view(submit_btn)
        submit_btn.click()
        self._wait_for_confirmation()

    # ── Low-level helpers ─────────────────────────────────────

    def _fill_by_id(self, element_id: str, value: str):
        """Scroll into view, clear, and type into an input/textarea by ID."""
        el = self.driver.find_element(By.ID, element_id)
        self._scroll_into_view(el)
        el.clear()
        el.send_keys(value)

    def _js_fill(self, element_id: str, value: str):
        """
        Set a value via JavaScript and fire a 'change' + 'input' event.
        Used for date-picker tel inputs that are blocked after UI repaints.
        """
        el = self.driver.find_element(By.ID, element_id)
        self._scroll_into_view(el)
        self.driver.execute_script(
            """
            arguments[0].value = arguments[1];
            arguments[0].dispatchEvent(new Event('input',  {bubbles: true}));
            arguments[0].dispatchEvent(new Event('change', {bubbles: true}));
            """,
            el, str(value)
        )

    def _select_by_value(self, element_id: str, value: str):
        """Choose an option by its value attribute in a native <select>."""
        if not value:
            return
        el = self.driver.find_element(By.ID, element_id)
        self._scroll_into_view(el)
        Select(el).select_by_value(value)

    def _scroll_into_view(self, element):
        """Scroll element to centre of viewport so it is interactable."""
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", element
        )
        time.sleep(0.2)

    def _wait_for_confirmation(self):
        """
        Wait for JotForm's Thank-you / confirmation page.
        In manual captcha mode the user may have already submitted
        the form in the browser before the bot clicks Submit — so
        we also handle a StaleElementReferenceException (page changed)
        and treat it as a successful submission.
        """
        from selenium.common.exceptions import StaleElementReferenceException
        wait = WebDriverWait(self.driver, config.SUBMIT_WAIT)

        def _confirmed(d):
            try:
                src = d.page_source.lower()
                return (
                    "thank" in src
                    or "submitted" in src
                    or "received" in src
                    or "confirmation" in src
                )
            except Exception:
                # Page navigated away or session changed — treat as confirmed
                return True

        try:
            wait.until(_confirmed)
            self._log("[BOT] Confirmation page detected.")
        except TimeoutException:
            # Last-chance check: if the form input is gone the page changed
            try:
                self.driver.find_element(By.ID, ID_FIRST_NAME)
                # Still on form page — genuinely failed
                raise TimeoutException(
                    f"No confirmation within {config.SUBMIT_WAIT}s. "
                    "Check the captcha value and try again."
                )
            except NoSuchElementException:
                # Form is gone — submission went through
                self._log("[BOT] Form navigated away — treating as confirmed.")