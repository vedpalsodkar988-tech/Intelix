# ability6_formfill.py

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time

def form_fill_task(task):
    print("🟦 Ability 6: Opening browser for form fill...")

    # Extract URL automatically from task
    url = ""
    for word in task.split():
        if word.startswith("http"):
            url = word.strip()
    if not url:
        return {"status": "error", "message": "No URL found"}

    options = webdriver.ChromeOptions()
    options.add_experimental_option("detach", True)  # DO NOT CLOSE
    # REMOVED headless – now visible in front

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    driver.get(url)
    time.sleep(3)

    # Fill ANY visible input fields
    inputs = driver.find_elements(By.TAG_NAME, "input")
    count = 0

    for field in inputs:
        try:
            field_type = field.get_attribute("type")

            if field_type in ["text", "email", "password", "tel", "number"]:
                field.send_keys("Test Data")
                count += 1

        except Exception:
            continue

    print(f"🟦 Filled {count} fields!")

    # POPUP in webpage asking for submit
    driver.execute_script("""
        let confirmSubmit = confirm("Do you want to submit this form?");
        window.confirm_result = confirmSubmit;
    """)

    time.sleep(3)

    result = driver.execute_script("return window.confirm_result;")

    if result:
        try:
            submit_buttons = driver.find_elements(By.XPATH, "//button[@type='submit']|//input[@type='submit']")
            if submit_buttons:
                submit_buttons[0].click()
                print("✔ Form submitted")
            else:
                print("⚠ No submit button found")
        except:
            print("❌ Submit failed")

    else:
        print("❌ User denied form submission")

    return {"status": "success", "message": "Ability 6 executed"}

