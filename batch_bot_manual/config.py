# ─────────────────────────────────────────────
#  config.py  –  Global settings for Batch Bot
# ─────────────────────────────────────────────

# ── Captcha Mode ──────────────────────────────
CAPTCHA_MODE = "demo"

# ── Manual Captcha (only used when CAPTCHA_MODE = "demo") ─────
# Set to True to pause and let the user solve the captcha manually
# in the browser, then press Enter in the terminal (or click
# "Continue" in the GUI) to resume.
MANUAL_CAPTCHA = True

# ── API Keys (only used when CAPTCHA_MODE = "api") ────────────────────────────
TWOCAPTCHA_API_KEY  = "YOUR_2CAPTCHA_KEY_HERE"
ANTICAPTCHA_API_KEY = "YOUR_ANTICAPTCHA_KEY_HERE"
API_SERVICE = "2captcha"

# ── Selenium Browser ──────────────────────────
BROWSER  = "chrome"
HEADLESS = False

# ── Form URL ──────────────────────────────────
FORM_URL = "https://form.jotform.com/260231667243453"

# ── Timing (seconds) ──────────────────────────
PAGE_LOAD_WAIT  = 10
SUBMIT_WAIT     = 8
BETWEEN_RECORDS = 2

# ── Excel column names ────────────────────────
COL_FIRST_NAME        = "FirstName"
COL_LAST_NAME         = "LastName"
COL_PHONE_AREA        = "PhoneAreaCode"
COL_PHONE_NUMBER      = "PhoneNumber"
COL_EMAIL             = "Email"
COL_PREFERRED_CONTACT = "PreferredContact"   # Email | Phone
COL_HOW_LOCATED       = "HowLocated"         # Referral|Google|Yahoo|Yelp|MSN|Other?
COL_OTHER_LOCATED     = "OtherLocated"       # filled only when HowLocated = Other?
COL_BEST_TIME_MONTH   = "BestTimeMonth"      # 1-12
COL_BEST_TIME_DAY     = "BestTimeDay"        # 1-31
COL_BEST_TIME_YEAR    = "BestTimeYear"       # e.g. 2025
COL_BEST_TIME_HOUR    = "BestTimeHour"       # 1-12
COL_BEST_TIME_MIN     = "BestTimeMin"        # 00 10 20 30 40 50
COL_BEST_TIME_AMPM    = "BestTimeAMPM"       # AM | PM
COL_REASON            = "Reason"
COL_DISCLAIMER        = "DisclaimerAgreement"  # TRUE | FALSE
COL_STATUS            = "Status"               # Pending | Success | Failed
