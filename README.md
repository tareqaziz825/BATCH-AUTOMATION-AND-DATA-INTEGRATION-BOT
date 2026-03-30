# ⚡ Batch Automation & Data Integration Bot

A desktop bot that automates bulk form submissions to a JotForm page by reading user records from an Excel or CSV file. It fills every field, handles the captcha, submits the form, and writes the result back to the spreadsheet — all from a clean Tkinter GUI.

**Target Form:** https://form.jotform.com/260231667243453

---

## 📋 Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Excel / CSV File Format](#excel--csv-file-format)
- [How to Run](#how-to-run)
- [GUI Controls](#gui-controls)
- [Captcha Modes](#captcha-modes)
- [Troubleshooting](#troubleshooting)
- [Dependencies](#dependencies)

---

## ✨ Features

- 📂 Reads `.xlsx` or `.csv` input files
- 🤖 Fully automated form filling for every record
- 🔒 Three captcha modes: **Manual**, **OCR (Tesseract)**, **Paid API (2Captcha / AntiCaptcha)**
- 🖥️ Desktop GUI with file picker, live data table, progress bar, and colour-coded log
- ⏸️ Start / Pause / Resume / Stop controls
- ✅ Per-record `Success` / `Failed` status written back to the Excel file in real time
- 🔁 Skips rows already marked `Success` — safe to resume a stopped batch

---

## 📁 Project Structure

```
batch_bot/
├── main.py                  # Entry point — launches the GUI
├── config.py                # All global settings
├── requirements.txt         # Python dependencies
├── diagnose_form.py         # Utility: prints live form field IDs
├── README.md
├── .gitignore
│
├── data/
│   └── sample_data.xlsx     # Sample file with 5 test records
│
├── bot/
│   ├── __init__.py
│   ├── selenium_bot.py      # Core browser automation & form-filling logic
│   ├── excel_handler.py     # Excel/CSV read, write & status update
│   └── captcha_solver.py    # Captcha solving — demo / OCR / API
│
└── gui/
    ├── __init__.py
    └── app.py               # Tkinter GUI — controls, table, log, progress
```

---

## ✅ Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.10+ | [Download](https://www.python.org/downloads/) |
| Google Chrome | Latest | [Download](https://www.google.com/chrome/) — or Firefox |
| pip | Latest | Bundled with Python |
| Tesseract OCR | Any | Only needed for OCR captcha mode |

> **Note:** You do **not** need to manually download ChromeDriver. The `webdriver-manager` package handles that automatically.

---

## 🚀 Installation

**1. Clone the repository**

```bash
git clone https://github.com/tareqaziz825/BATCH-AUTOMATION-AND-DATA-INTEGRATION-BOT.git
cd batch-bot
```

**2. Install Python dependencies**

```bash
pip install -r requirements.txt
```

**3. (Optional) Install Tesseract OCR** — only needed for `CAPTCHA_MODE = "ocr"`

| OS | Command |
|---|---|
| Windows | [Download installer](https://github.com/UB-Mannheim/tesseract/wiki) and add to PATH |
| macOS | `brew install tesseract` |
| Linux | `sudo apt install tesseract-ocr` |

**4. (Linux only) Install Tkinter if missing**

```bash
sudo apt install python3-tk
```

---

## ⚙️ Configuration

All settings live in **`config.py`**. Edit this file before running.

### Captcha Mode

```python
CAPTCHA_MODE = "demo"   # "demo" | "ocr" | "api"
```

| Mode | Description |
|---|---|
| `"demo"` | **Recommended.** Bot pauses at the captcha; you type it manually in the browser then click **Continue** in the GUI. |
| `"ocr"` | Tesseract reads the captcha automatically. Low accuracy on distorted images — not recommended for production. |
| `"api"` | Sends the captcha to 2Captcha or AntiCaptcha. Most reliable automated option. Requires a paid API key. |

For `"demo"` mode:
```python
MANUAL_CAPTCHA = True    # True = pause for manual solve (real submissions)
                         # False = insert dummy text "DEMO123" (dry-run only)
```

For `"api"` mode:
```python
API_SERVICE         = "2captcha"           # or "anticaptcha"
TWOCAPTCHA_API_KEY  = "YOUR_KEY_HERE"
ANTICAPTCHA_API_KEY = "YOUR_KEY_HERE"
```

### Browser Settings

```python
BROWSER  = "chrome"   # "chrome" or "firefox"
HEADLESS = False      # True = no visible browser window (not recommended with "demo" mode)
```

### Timing Settings

```python
PAGE_LOAD_WAIT  = 15   # seconds to wait for form elements to load
SUBMIT_WAIT     = 12   # seconds to wait for confirmation after submit
BETWEEN_RECORDS = 5    # seconds between consecutive submissions
```

> Increase `PAGE_LOAD_WAIT` and `SUBMIT_WAIT` on slow internet connections.

---

## 📊 Excel / CSV File Format

### Required Columns

| Column | Description | Accepted Values |
|---|---|---|
| `FirstName` | First name | Any text |
| `LastName` | Last name | Any text |
| `PhoneAreaCode` | 3-digit area code | e.g. `212` |
| `PhoneNumber` | 7-digit local number | e.g. `5550101` |
| `Email` | Email address | Valid email |
| `PreferredContact` | Contact preference | `Email` \| `Phone` |
| `HowLocated` | How they found you | `Google` \| `Referral` \| `Yahoo` \| `Yelp` \| `MSN` \| `Other?` |
| `OtherLocated` | Details if `Other?` | Any text (leave blank otherwise) |
| `BestTimeMonth` | Month | `1`–`12` |
| `BestTimeDay` | Day | `1`–`31` |
| `BestTimeYear` | Year | e.g. `2026` |
| `BestTimeHour` | Hour | `1`–`12` |
| `BestTimeMin` | Minutes | `00` `10` `20` `30` `40` `50` |
| `BestTimeAMPM` | AM or PM | `AM` \| `PM` |
| `Reason` | Reason for contact | Any text |
| `DisclaimerAgreement` | Agree to disclaimer | `TRUE` \| `FALSE` |
| `Status` | Managed by the bot | Set to `Pending` before first run |

### Status Column Behaviour

| Value | Meaning |
|---|---|
| `Pending` | Not yet processed — will be submitted |
| `Success` | Submitted successfully — will be **skipped** on next run |
| `Failed: <reason>` | Submission failed — will be retried on next run |

> ⚠️ Before the first run, make sure all rows have `Status = Pending`. The sample file (`data/sample_data.xlsx`) is already set up this way.

---

## ▶️ How to Run

**Launch the GUI:**

```bash
python main.py
```

**Step-by-step walkthrough:**

1. Click **Browse …** and select your `.xlsx` or `.csv` file
2. Review the records loaded in the Data Preview table
3. Click **▶ Start Batch** — the bot opens Chrome and starts filling forms
4. If using `"demo"` captcha mode:
   - Look at the open Chrome window
   - Type the captcha characters into the captcha field on the form
   - Click **✅ Continue** in the GUI to resume
5. Monitor progress via the progress bar, counter, and live log
6. When complete, the log shows **"Batch finished."** and all statuses are saved back to your file

---

## 🖥️ GUI Controls

| Button | Active When | Action |
|---|---|---|
| **Browse …** | Always | Opens file picker |
| **▶ Start Batch** | File loaded | Begins processing all Pending records |
| **⏸ Pause** | Running | Pauses after the current record finishes |
| **▶ Resume** | Paused | Continues from the next pending record |
| **⏹ Stop** | Running | Stops after current record; closes browser |
| **✅ Continue** | Captcha wait | Signals that the captcha has been solved |

**Live Log colours:**

- 🟢 Green — Success
- 🔴 Red — Error / Failed
- 🟡 Yellow — Warning / Paused
- 🔵 Blue — Info

---

## 🔒 Captcha Modes

### Manual (default)
```python
CAPTCHA_MODE = "demo"
MANUAL_CAPTCHA = True
```
Bot pauses at every captcha. You solve it in the browser, click **Continue**. Repeat per record.

### Dry Run (testing only)
```python
CAPTCHA_MODE = "demo"
MANUAL_CAPTCHA = False
```
Inserts dummy text `DEMO123`. Form will fail validation — use only to test the automation flow.

### OCR
```python
CAPTCHA_MODE = "ocr"
```
Tesseract reads the image automatically. Requires Tesseract installed. Low accuracy on JotForm's distorted images.

### API (most reliable automated option)
```python
CAPTCHA_MODE = "api"
API_SERVICE = "2captcha"          # or "anticaptcha"
TWOCAPTCHA_API_KEY = "your_key"
```
Uploads the captcha to a solving service and receives the answer. Requires a paid account.

---

## 🔧 Troubleshooting

| Problem | Solution |
|---|---|
| `No module named 'tkinter'` | Linux: `sudo apt install python3-tk` |
| ChromeDriver version mismatch | `pip install --upgrade webdriver-manager` |
| "No pending records found" | Check the Status column in your file — reset rows to `Pending` |
| Submission fails: "No confirmation within 12s" | Increase `SUBMIT_WAIT` in `config.py`; use `"demo"` mode for reliable captcha |
| Fields not filled / elements not found | Run `python diagnose_form.py` to check if form field IDs have changed |
| Page loads too slowly | Increase `PAGE_LOAD_WAIT` in `config.py` (try 20–25s) |
| OCR returns wrong text | Switch to `CAPTCHA_MODE = "demo"` or `"api"` |
| JotForm rate-limit errors | Increase `BETWEEN_RECORDS` in `config.py` (try 8–10s) |

### Re-diagnosing Form Field IDs

If JotForm updates the form and fields stop being filled correctly, run:

```bash
python diagnose_form.py
```

This prints every input, select, textarea, and button with its HTML `id`. Compare against the `ID_` constants at the top of `bot/selenium_bot.py` and update any that have changed.

---

## 📦 Dependencies

| Package | Version | Purpose |
|---|---|---|
| `selenium` | >= 4.18.0 | Browser automation |
| `webdriver-manager` | >= 4.0.0 | Auto-downloads ChromeDriver / GeckoDriver |
| `pandas` | >= 2.2.0 | Excel and CSV data handling |
| `openpyxl` | >= 3.1.2 | Read / write `.xlsx` files |
| `pytesseract` | >= 0.3.10 | OCR captcha solving *(optional)* |
| `Pillow` | >= 10.2.0 | Image processing for OCR *(optional)* |
| `requests` | >= 2.31.0 | HTTP calls for API captcha services |
| `tkinter` | built-in | Desktop GUI *(ships with Python)* |

Install all at once:

```bash
pip install -r requirements.txt
```

---

## 📄 License

This project was developed as a technical assignment. Feel free to adapt it for your own automation needs.
