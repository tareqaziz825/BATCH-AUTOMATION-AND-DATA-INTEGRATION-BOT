# ─────────────────────────────────────────────────────────────
#  diagnose_form.py
#  Run this ONCE to print every interactive element on the form
#  so we can map the correct IDs into selenium_bot.py
#
#  Usage:  python diagnose_form.py
# ─────────────────────────────────────────────────────────────

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

FORM_URL = "https://form.jotform.com/260231667243453"

opts = Options()
opts.add_argument("--window-size=1280,900")
driver = webdriver.Chrome(options=opts)

try:
    driver.get(FORM_URL)
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.TAG_NAME, "form"))
    )
    time.sleep(3)   # let dynamic content fully render

    print("\n" + "="*70)
    print("  FORM FIELD INSPECTOR")
    print("="*70)

    # ── All INPUT fields ──────────────────────────────────────
    print("\n── INPUT fields ──────────────────────────────────────────")
    inputs = driver.find_elements(By.TAG_NAME, "input")
    for el in inputs:
        print(f"  id={el.get_attribute('id')!r:40}  "
              f"name={el.get_attribute('name')!r:30}  "
              f"type={el.get_attribute('type')!r:12}  "
              f"placeholder={el.get_attribute('placeholder')!r}")

    # ── All SELECT (native dropdowns) ─────────────────────────
    print("\n── SELECT (native dropdown) fields ───────────────────────")
    selects = driver.find_elements(By.TAG_NAME, "select")
    for el in selects:
        print(f"  id={el.get_attribute('id')!r:40}  "
              f"name={el.get_attribute('name')!r:30}")
        options = el.find_elements(By.TAG_NAME, "option")
        for opt in options:
            print(f"      option value={opt.get_attribute('value')!r:20}  text={opt.text!r}")

    # ── All TEXTAREA fields ───────────────────────────────────
    print("\n── TEXTAREA fields ───────────────────────────────────────")
    textareas = driver.find_elements(By.TAG_NAME, "textarea")
    for el in textareas:
        print(f"  id={el.get_attribute('id')!r:40}  "
              f"name={el.get_attribute('name')!r}")

    # ── All CHECKBOX fields ───────────────────────────────────
    print("\n── CHECKBOX fields ───────────────────────────────────────")
    checkboxes = driver.find_elements(
        By.XPATH, "//input[@type='checkbox']"
    )
    for el in checkboxes:
        print(f"  id={el.get_attribute('id')!r:40}  "
              f"name={el.get_attribute('name')!r}")

    # ── Custom styled dropdowns (JotForm uses <ul> menus) ─────
    print("\n── Custom dropdown wrappers (div/ul with 'dropdown') ─────")
    custom = driver.find_elements(
        By.XPATH,
        "//*[contains(@class,'dropdown') or contains(@class,'select')]"
        "[@id]"
    )
    seen = set()
    for el in custom:
        eid = el.get_attribute('id')
        if eid and eid not in seen:
            seen.add(eid)
            cls = (el.get_attribute('class') or '')[:60]
            print(f"  id={eid!r:40}  class={cls!r}")

    # ── Submit button ─────────────────────────────────────────
    print("\n── Submit / Send button ──────────────────────────────────")
    for btn in driver.find_elements(By.XPATH,
            "//button | //input[@type='submit']"):
        print(f"  tag={btn.tag_name!r}  "
              f"id={btn.get_attribute('id')!r:30}  "
              f"type={btn.get_attribute('type')!r:12}  "
              f"text={btn.text!r}")

    print("\n" + "="*70)
    print("  Copy the output above and share it — fix will be applied.")
    print("="*70 + "\n")

    input("Press ENTER to close the browser …")

finally:
    driver.quit()
