================================================================================
  BATCH AUTOMATION & DATA INTEGRATION BOT
  README & SETUP GUIDE
================================================================================

  Target Form : https://form.jotform.com/260231667243453
  Language    : Python 3.10+
  UI          : Desktop GUI (Tkinter)
  Automation  : Selenium (Chrome or Firefox)

--------------------------------------------------------------------------------
TABLE OF CONTENTS
--------------------------------------------------------------------------------

  1.  Project Overview
  2.  Project Structure
  3.  Prerequisites
  4.  Installation & Setup
        4a. Install Python
        4b. Install Google Chrome
        4c. Install Dependencies
        4d. (Optional) Tesseract OCR — for OCR captcha mode
  5.  Configuration (config.py)
        5a. Captcha Mode
        5b. Browser Settings
        5c. Timing Settings
  6.  Excel / CSV File Format
        6a. Required Columns
        6b. Column Value Rules
        6c. Status Column Behaviour
  7.  How to Run the Bot
        7a. Launch the GUI
        7b. Using the GUI Step-by-Step
        7c. Captcha Handling (Manual / OCR / API)
  8.  GUI Controls Reference
  9.  File Descriptions
  10. Troubleshooting
  11. Dependencies Reference


================================================================================
1. PROJECT OVERVIEW
================================================================================

This bot automates batch form submissions to a JotForm page. It reads user
records from an Excel (.xlsx) or CSV file, opens the form in a real browser
for each row, fills in all fields, handles the captcha, submits the form, and
writes the result (Success or Failed) back to the same file.

Key features:
  - Reads .xlsx or .csv input files
  - Maps every form field automatically from the spreadsheet columns
  - Three captcha modes: manual, OCR (Tesseract), or paid API service
  - Desktop GUI with file picker, data preview table, progress bar, and live log
  - Start / Pause / Resume / Stop controls
  - Per-record status written back to the Excel file in real time
  - Skips rows already marked "Success" so the batch can be safely resumed


================================================================================
2. PROJECT STRUCTURE
================================================================================

  batch_bot/
  |
  |-- main.py                  Entry point — launches the GUI
  |-- config.py                All global settings (captcha mode, timing, etc.)
  |-- requirements.txt         Python package dependencies
  |-- diagnose_form.py         Utility: prints all form field IDs (run once)
  |-- README.txt               This file
  |-- .gitignore               Excludes cache and temp files from version control
  |
  |-- data/
  |   |-- sample_data.xlsx     Sample Excel file with 5 test records
  |
  |-- bot/
  |   |-- __init__.py
  |   |-- selenium_bot.py      Core browser automation and form-filling logic
  |   |-- excel_handler.py     Excel/CSV read, write, and status update logic
  |   |-- captcha_solver.py    Captcha solving — demo / OCR / API modes
  |
  |-- gui/
      |-- __init__.py
      |-- app.py               Tkinter GUI — all controls, table, log, progress


================================================================================
3. PREREQUISITES
================================================================================

  - Python 3.10 or higher
      Download: https://www.python.org/downloads/
      Verify:   python --version

  - Google Chrome (recommended) or Mozilla Firefox
      Chrome:   https://www.google.com/chrome/
      Firefox:  https://www.mozilla.org/firefox/

  NOTE: You do NOT need to manually download ChromeDriver or GeckoDriver.
        The "webdriver-manager" package handles driver installation automatically.

  - pip (comes with Python)
      Verify: pip --version


================================================================================
4. INSTALLATION & SETUP
================================================================================

  ── 4a. Install Python ────────────────────────────────────────────────────────

  Download Python 3.10+ from https://www.python.org/downloads/
  During installation on Windows, check "Add Python to PATH".

  Verify installation:
      python --version
      pip --version


  ── 4b. Install Google Chrome ─────────────────────────────────────────────────

  Download from: https://www.google.com/chrome/
  The bot defaults to Chrome. To use Firefox instead, change BROWSER in
  config.py (see Section 5b).


  ── 4c. Install Python Dependencies ───────────────────────────────────────────

  Open a terminal (Command Prompt / PowerShell / bash) inside the batch_bot/
  folder and run:

      pip install -r requirements.txt

  This installs:
      selenium          — browser automation
      webdriver-manager — auto-downloads matching ChromeDriver / GeckoDriver
      pandas            — Excel/CSV data handling
      openpyxl          — read/write .xlsx files
      pytesseract       — OCR captcha solving (optional)
      Pillow            — image processing for OCR (optional)
      requests          — HTTP calls for API captcha services

  On Linux, if tkinter is missing:
      sudo apt install python3-tk


  ── 4d. (Optional) Install Tesseract OCR ──────────────────────────────────────

  Only required if CAPTCHA_MODE = "ocr" in config.py.

  Windows:
      Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
      During install, note the install path (e.g. C:\Program Files\Tesseract-OCR)
      Add that folder to your system PATH, or set it in code:
          pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

  macOS:
      brew install tesseract

  Linux:
      sudo apt install tesseract-ocr

  NOTE: OCR accuracy on JotForm's distorted captcha images is low. For real
        submissions, "demo" (manual) or "api" mode is strongly recommended.


================================================================================
5. CONFIGURATION (config.py)
================================================================================

  Open config.py to customise the bot's behaviour before running.


  ── 5a. Captcha Mode ──────────────────────────────────────────────────────────

  CAPTCHA_MODE = "demo"       # Change to "ocr" or "api" as needed

  "demo" (default / recommended for first-time use)
  ──────
    The bot pauses at the captcha step and opens the form in a visible browser
    window. You type the captcha manually, then click the "Continue" button in
    the GUI to resume. Most reliable option.

    MANUAL_CAPTCHA = True    ← keep this True for real submissions
    MANUAL_CAPTCHA = False   ← dry-run only; inserts dummy text "DEMO123"

  "ocr"
  ─────
    Uses Tesseract to read the captcha image automatically.
    Requires Tesseract installed (see Section 4d).
    Accuracy is low on JotForm's distorted images — not recommended for
    production use.

  "api"
  ─────
    Sends the captcha image to a paid solving service and gets the answer back.
    Requires a valid API key. Set the service and key in config.py:

      API_SERVICE         = "2captcha"          # or "anticaptcha"
      TWOCAPTCHA_API_KEY  = "your_key_here"
      ANTICAPTCHA_API_KEY = "your_key_here"

    Sign up:
      2Captcha    → https://2captcha.com
      AntiCaptcha → https://anti-captcha.com


  ── 5b. Browser Settings ──────────────────────────────────────────────────────

  BROWSER  = "chrome"    # Change to "firefox" to use Firefox instead
  HEADLESS = False       # Set to True to run without a visible browser window
                         # (not recommended when CAPTCHA_MODE = "demo")


  ── 5c. Timing Settings ───────────────────────────────────────────────────────

  PAGE_LOAD_WAIT  = 15   # seconds to wait for form elements to load
  SUBMIT_WAIT     = 12   # seconds to wait for confirmation page after submit
  BETWEEN_RECORDS = 5    # seconds to pause between consecutive submissions
                         # (keeps submissions below JotForm's rate-limit threshold)

  Increase PAGE_LOAD_WAIT and SUBMIT_WAIT on slow internet connections.


================================================================================
6. EXCEL / CSV FILE FORMAT
================================================================================

  ── 6a. Required Columns ──────────────────────────────────────────────────────

  Your spreadsheet must contain these column headers (exact spelling, case-
  sensitive) in any order:

  Column Name          Description
  -------------------  --------------------------------------------------------
  FirstName            First name of the person
  LastName             Last name of the person
  PhoneAreaCode        3-digit area code (e.g. 212)
  PhoneNumber          7-digit local number (e.g. 5550101)
  Email                Email address
  PreferredContact     How to contact: Email  or  Phone
  HowLocated           How they found you: Google | Referral | Yahoo |
                                           Yelp | MSN | Other?
  OtherLocated         Text description — only needed when HowLocated = Other?
                       Leave blank otherwise.
  BestTimeMonth        Month number 1–12
  BestTimeDay          Day number 1–31
  BestTimeYear         4-digit year (e.g. 2026)
  BestTimeHour         Hour 1–12
  BestTimeMin          Minutes: 00  10  20  30  40  50
  BestTimeAMPM         AM  or  PM
  Reason               Free-text reason for contacting (textarea)
  DisclaimerAgreement  TRUE  or  FALSE  (must agree to submit successfully)
  Status               Managed by the bot — set to Pending before first run


  ── 6b. Column Value Rules ────────────────────────────────────────────────────

  - PreferredContact  : must be exactly  "Email"  or  "Phone"
  - HowLocated        : must exactly match one of the dropdown options:
                        Google | Referral | Yahoo | Yelp | MSN | Other?
                        (the question mark is part of "Other?" — include it)
  - BestTimeMin       : only the values 00, 10, 20, 30, 40, 50 are valid
  - DisclaimerAgreement: TRUE or FALSE (case-insensitive; 1/yes also accepted)
  - Phone numbers     : digits only, no dashes or spaces


  ── 6c. Status Column Behaviour ───────────────────────────────────────────────

  The bot reads and writes the Status column automatically:

  Pending   → Row has not been processed yet (or was reset manually)
  Success   → Form submitted and confirmation page was detected
  Failed: X → Submission failed; X contains the error reason

  IMPORTANT: Before the first run, all rows must have Status = "Pending".
             Rows already marked "Success" are skipped automatically, so
             a stopped batch can be safely resumed without re-submitting
             completed records.

  The sample file (data/sample_data.xlsx) already has all rows set to Pending.


================================================================================
7. HOW TO RUN THE BOT
================================================================================

  ── 7a. Launch the GUI ────────────────────────────────────────────────────────

  Open a terminal inside the batch_bot/ folder and run:

      python main.py

  The GUI window will open. No browser launches until you click "Start Batch".


  ── 7b. Using the GUI Step-by-Step ────────────────────────────────────────────

  Step 1 — Select your Excel file
      Click "Browse …" in the top bar and select your .xlsx or .csv file.
      The Data Preview table will populate with all records from the file.

  Step 2 — Review the data
      Check that all records look correct in the table. Columns shown are:
      FirstName, LastName, Email, PhoneNumber, PreferredContact,
      HowLocated, Status.

  Step 3 — Start the batch
      Click "▶ Start Batch".
      The bot opens Chrome, navigates to the JotForm, and begins filling
      records one by one.

  Step 4 — Handle the captcha (if CAPTCHA_MODE = "demo")
      When the bot reaches the captcha, the log will show:
          [CAPTCHA] Manual captcha mode — type the captcha in the browser,
                    then click 'Continue' in the GUI.
      - Look at the open Chrome window
      - Type the captcha characters into the captcha field on the form
      - Click "✅ Continue" in the GUI
      - The bot resumes and submits the form

  Step 5 — Monitor progress
      The progress bar and counter ("Processing record 2 of 5 — 40%") update
      after each record. The live log shows every action in real time.
      The Data Preview table updates the Status column after each submission.

  Step 6 — Completion
      When all records are processed the log shows "Batch finished." and
      the table reflects the final statuses. The updated statuses are also
      saved back to your original Excel file.


  ── 7c. Captcha Handling Modes ────────────────────────────────────────────────

  MANUAL (CAPTCHA_MODE = "demo", MANUAL_CAPTCHA = True)  ← default
      The bot pauses at each captcha. You read and type it in the browser,
      then click "Continue" in the GUI. Repeat for every record.

  DRY RUN (CAPTCHA_MODE = "demo", MANUAL_CAPTCHA = False)
      The bot inserts the dummy text "DEMO123" and submits. The form will
      likely fail validation. Use only to test the automation flow without
      real submissions.

  OCR (CAPTCHA_MODE = "ocr")
      Tesseract reads the captcha image automatically. No user interaction
      needed but accuracy is low on JotForm's images. Tesseract must be
      installed (Section 4d).

  API (CAPTCHA_MODE = "api")
      The captcha image is uploaded to 2Captcha or AntiCaptcha. A human
      solves it remotely and the answer is returned automatically. Most
      reliable automated option. Requires a paid API key (Section 5a).


================================================================================
8. GUI CONTROLS REFERENCE
================================================================================

  Button              State           Action
  ──────────────────  ──────────────  ─────────────────────────────────────────
  Browse …            Always active   Opens file picker to load Excel / CSV
  ▶  Start Batch      After file load Begins processing all Pending records
  ⏸  Pause            While running   Pauses after the current record finishes
  ▶  Resume           While paused    Continues from the next pending record
  ⏹  Stop             While running   Requests a stop; closes browser when done
  ✅  Continue         Captcha wait    Tells the bot the captcha has been solved

  Progress Bar        Shows % of records completed
  Counter Label       Shows "Processing record X of Y  (Z%)"
  Live Log            Colour-coded: green = success, red = error/fail,
                                    yellow = warning, blue = info
  Data Preview Table  Updates Status column live after each record


================================================================================
9. FILE DESCRIPTIONS
================================================================================

  main.py
      Entry point. Instantiates BatchBotApp and starts the Tkinter main loop.

  config.py
      Central settings file. Edit this to change captcha mode, browser,
      timing, API keys, and Excel column name mappings.

  bot/selenium_bot.py
      Core automation engine. Opens Chrome/Firefox, navigates to the form,
      fills every field for each record, handles captcha, submits, and checks
      for a confirmation page. Uses confirmed live field IDs from the form.

  bot/excel_handler.py
      Loads .xlsx or .csv files into a pandas DataFrame. Provides methods to
      read records, get pending rows, and write Success/Failed status back to
      the original file after each submission.

  bot/captcha_solver.py
      Unified captcha handler supporting demo (manual), OCR (Tesseract), and
      API (2Captcha / AntiCaptcha) modes. Called once per form submission.

  gui/app.py
      Tkinter desktop GUI. Builds the file bar, data preview table, progress
      bar, control buttons, and scrollable live log. Runs the bot in a
      background thread and updates the UI via thread-safe after() callbacks.

  diagnose_form.py
      Standalone utility. Opens the form in Chrome and prints every input,
      select, textarea, checkbox, and submit button with its HTML id and name.
      Run this if the form is updated and field IDs need to be re-confirmed:
          python diagnose_form.py

  data/sample_data.xlsx
      Ready-to-use sample file with 5 test records covering all field types,
      including one "Other?" HowLocated entry. All rows start as Pending.


================================================================================
10. TROUBLESHOOTING
================================================================================

  Problem: "No module named 'tkinter'"
  Solution (Linux): sudo apt install python3-tk

  Problem: ChromeDriver version mismatch error
  Solution: webdriver-manager handles this automatically. Make sure
            webdriver-manager is installed: pip install webdriver-manager
            If behind a proxy, set HTTP_PROXY / HTTPS_PROXY env variables.

  Problem: "No pending records found" — bot exits immediately
  Solution: Open your Excel file and check the Status column. If all rows
            say "Success", reset the ones you want to re-run to "Pending".

  Problem: Form submission fails with "No confirmation within 12s"
  Solution: The captcha answer was wrong or the page loaded slowly.
            - Increase SUBMIT_WAIT in config.py (e.g. to 20)
            - Use "demo" mode to solve captcha manually
            - Check your internet connection speed

  Problem: Fields are not being filled correctly
  Solution: JotForm may have updated its field IDs. Run:
                python diagnose_form.py
            Compare the printed IDs to the ID_ constants at the top of
            bot/selenium_bot.py and update any that have changed.

  Problem: Bot fills fields but the page keeps scrolling / elements not found
  Solution: Increase PAGE_LOAD_WAIT in config.py. On slow connections 15s
            may not be enough; try 20–25.

  Problem: "WebDriverException: Chrome not found"
  Solution: Make sure Google Chrome is installed. If using Firefox, set
            BROWSER = "firefox" in config.py and install Firefox.

  Problem: OCR captcha mode returns wrong or empty text
  Solution: OCR accuracy on distorted captchas is inherently limited.
            Switch to CAPTCHA_MODE = "demo" (manual) or "api" for
            reliable automated submissions.

  Problem: Bot submits too fast and JotForm shows an error
  Solution: Increase BETWEEN_RECORDS in config.py (default is 5 seconds).
            Try 8–10 seconds for large batches.


================================================================================
11. DEPENDENCIES REFERENCE
================================================================================

  Package              Version     Purpose
  ───────────────────  ──────────  ─────────────────────────────────────────
  selenium             >= 4.18.0   Browser automation (Chrome / Firefox)
  webdriver-manager    >= 4.0.0    Auto-downloads matching ChromeDriver/Gecko
  pandas               >= 2.2.0    Excel and CSV data handling
  openpyxl             >= 3.1.2    Read / write .xlsx files
  pytesseract          >= 0.3.10   OCR captcha solving (optional)
  Pillow               >= 10.2.0   Image processing for OCR (optional)
  requests             >= 2.31.0   HTTP calls to 2Captcha / AntiCaptcha API
  tkinter              built-in    Desktop GUI framework (ships with Python)

  Install all at once:
      pip install -r requirements.txt


================================================================================
  END OF README
================================================================================
