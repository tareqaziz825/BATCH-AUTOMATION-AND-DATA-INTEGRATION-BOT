# ─────────────────────────────────────────────────────────────
#  bot/captcha_solver.py  –  Captcha solving in 3 modes:
#    "demo"  → dummy text (for UI/flow testing)
#    "ocr"   → Tesseract OCR on the captcha image
#    "api"   → 2Captcha or AntiCaptcha paid service
# ─────────────────────────────────────────────────────────────

import base64
import io
import time
import requests

import config

# Optional imports — only loaded when the mode needs them
try:
    from PIL import Image
    import pytesseract
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False


class CaptchaSolver:
    """
    Unified captcha solver.
    Instantiate once and call solve(driver) per form page.
    """

    def __init__(self, mode: str = None):
        self.mode = (mode or config.CAPTCHA_MODE).lower()

    # ── Public API ────────────────────────────────────────────

    def solve(self, driver, log_callback=None) -> str:
        """
        Attempt to read and solve the captcha on the current page.

        Parameters
        ----------
        driver       : Selenium WebDriver already on the form page
        log_callback : optional callable(str) to push messages to the GUI log

        Returns
        -------
        str  – the captcha text to type into the input field
        """
        def _log(msg):
            if log_callback:
                log_callback(msg)

        if self.mode == "demo":
            return self._demo_solve(_log)
        elif self.mode == "ocr":
            return self._ocr_solve(driver, _log)
        elif self.mode == "api":
            return self._api_solve(driver, _log)
        else:
            raise ValueError(f"Unknown captcha mode: {self.mode!r}. "
                             "Use 'demo', 'ocr', or 'api'.")

    # ── Mode: demo ────────────────────────────────────────────

    def _demo_solve(self, log) -> str:
        """
        Returns a hard-coded dummy string.
        Useful for testing the full UI flow without a real captcha.
        """
        log("[CAPTCHA] Demo mode → returning placeholder text.")
        return "DEMO123"

    # ── Mode: ocr ─────────────────────────────────────────────

    def _ocr_solve(self, driver, log) -> str:
        """
        Screenshots the captcha <img> element and runs Tesseract OCR on it.
        Requires:  pip install pytesseract Pillow
                   + Tesseract binary installed on the OS
        """
        if not _PIL_AVAILABLE:
            log("[CAPTCHA] pytesseract/Pillow not installed. Falling back to demo.")
            return self._demo_solve(log)

        log("[CAPTCHA] OCR mode → capturing captcha image …")
        try:
            # JotForm renders the captcha inside an <img> with class 'hasImg'
            # or inside the captcha widget iframe.  Try both selectors.
            captcha_img = self._find_captcha_element(driver)
            if captcha_img is None:
                log("[CAPTCHA] Could not locate captcha image element.")
                return ""

            # Grab a PNG screenshot of just that element
            png_bytes = captcha_img.screenshot_as_png
            img = Image.open(io.BytesIO(png_bytes)).convert("L")  # greyscale

            # Light preprocessing to improve OCR accuracy
            img = img.point(lambda p: 255 if p > 140 else 0)      # binarise

            text = pytesseract.image_to_string(
                img,
                config="--psm 8 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
            ).strip()

            log(f"[CAPTCHA] OCR result: '{text}'")
            return text

        except Exception as exc:
            log(f"[CAPTCHA] OCR error: {exc}")
            return ""

    # ── Mode: api ─────────────────────────────────────────────

    def _api_solve(self, driver, log) -> str:
        """
        Sends the captcha image to 2Captcha or AntiCaptcha and
        polls for the solved text.
        Requires a valid API key in config.py.
        """
        log(f"[CAPTCHA] API mode ({config.API_SERVICE}) → uploading captcha …")
        try:
            captcha_img = self._find_captcha_element(driver)
            if captcha_img is None:
                log("[CAPTCHA] Could not locate captcha image element.")
                return ""

            png_bytes = captcha_img.screenshot_as_png
            b64_image = base64.b64encode(png_bytes).decode("utf-8")

            if config.API_SERVICE == "2captcha":
                return self._solve_2captcha(b64_image, log)
            elif config.API_SERVICE == "anticaptcha":
                return self._solve_anticaptcha(b64_image, log)
            else:
                log(f"[CAPTCHA] Unknown API service: {config.API_SERVICE}")
                return ""

        except Exception as exc:
            log(f"[CAPTCHA] API error: {exc}")
            return ""

    # ── 2Captcha integration ──────────────────────────────────

    def _solve_2captcha(self, b64_image: str, log) -> str:
        # Submit image
        resp = requests.post(
            "http://2captcha.com/in.php",
            data={
                "key":    config.TWOCAPTCHA_API_KEY,
                "method": "base64",
                "body":   b64_image,
                "json":   1,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != 1:
            log(f"[CAPTCHA] 2Captcha submit failed: {data}")
            return ""

        captcha_id = data["request"]
        log(f"[CAPTCHA] Submitted to 2Captcha (id={captcha_id}). Polling …")

        # Poll for result
        for _ in range(24):          # max ~120 s
            time.sleep(5)
            poll = requests.get(
                "http://2captcha.com/res.php",
                params={
                    "key":    config.TWOCAPTCHA_API_KEY,
                    "action": "get",
                    "id":     captcha_id,
                    "json":   1,
                },
                timeout=15,
            )
            poll.raise_for_status()
            pdata = poll.json()
            if pdata.get("status") == 1:
                text = pdata["request"]
                log(f"[CAPTCHA] 2Captcha solved: '{text}'")
                return text
            if pdata.get("request") != "CAPCHA_NOT_READY":
                log(f"[CAPTCHA] 2Captcha error: {pdata}")
                return ""

        log("[CAPTCHA] 2Captcha timeout.")
        return ""

    # ── AntiCaptcha integration ───────────────────────────────

    def _solve_anticaptcha(self, b64_image: str, log) -> str:
        # Create task
        resp = requests.post(
            "https://api.anti-captcha.com/createTask",
            json={
                "clientKey": config.ANTICAPTCHA_API_KEY,
                "task": {
                    "type":  "ImageToTextTask",
                    "body":  b64_image,
                    "case":  True,
                },
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("errorId", 1) != 0:
            log(f"[CAPTCHA] AntiCaptcha error: {data}")
            return ""

        task_id = data["taskId"]
        log(f"[CAPTCHA] Submitted to AntiCaptcha (id={task_id}). Polling …")

        for _ in range(24):
            time.sleep(5)
            poll = requests.post(
                "https://api.anti-captcha.com/getTaskResult",
                json={
                    "clientKey": config.ANTICAPTCHA_API_KEY,
                    "taskId":    task_id,
                },
                timeout=15,
            )
            poll.raise_for_status()
            pdata = poll.json()
            if pdata.get("status") == "ready":
                text = pdata["solution"]["text"]
                log(f"[CAPTCHA] AntiCaptcha solved: '{text}'")
                return text

        log("[CAPTCHA] AntiCaptcha timeout.")
        return ""

    # ── Shared helpers ────────────────────────────────────────

    def _find_captcha_element(self, driver):
        """
        Try several selectors to locate the captcha image element.
        Returns a WebElement or None.
        """
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        selectors = [
            (By.CSS_SELECTOR,  "img.hasImg"),
            (By.CSS_SELECTOR,  ".form-captcha img"),
            (By.XPATH,         "//img[contains(@class,'captcha')]"),
            (By.CSS_SELECTOR,  "[id*='captcha'] img"),
        ]
        for by, sel in selectors:
            try:
                el = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((by, sel))
                )
                return el
            except Exception:
                continue
        return None
