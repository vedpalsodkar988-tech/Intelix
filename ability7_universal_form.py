from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time

def ability7_universal_form_task(task: str):
    """
    Ability 7: Universal smart form filling
    NO DEBUG MODE - Auto opens Chrome!
    """
    print("🟦 Ability 7: Universal smart form filling...")

    # Extract URL from task
    url = ""
    for word in task.split():
        if word.startswith("http"):
            url = word
            break

    if url == "":
        return {"status": "error", "message": "No valid form URL found in task."}

    # Auto-open Chrome (no debug mode!)
    options = Options()
    options.add_argument("--start-maximized")
    options.add_experimental_option("detach", True)  # Keep browser open
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    try:
        driver.get(url)
        time.sleep(3)

        print("🟦 Scanning form fields...")

        input_tags = driver.find_elements(By.CSS_SELECTOR, "input")

        demo_value = {
            "name": "Rahul Verma",
            "email": "rahul@gmail.com",
            "address": "MG Road, Mumbai",
            "city": "Mumbai",
            "state": "Maharashtra",
            "zip": "400001",
            "phone": "9876543210",
            "password": "Secret@123",
            "card": "5555 4444 3333 1111",
            "cvv": "777",
            "expiry": "11/30"
        }

        count = 0
        for field in input_tags:
            try:
                field_type = field.get_attribute("type") or ""
                placeholder = field.get_attribute("placeholder") or ""
                name_attr = field.get_attribute("name") or ""

                # Try matching field by placeholder or name
                for key in demo_value:
                    if key.lower() in placeholder.lower() or key.lower() in name_attr.lower():
                        field.clear()
                        field.send_keys(demo_value[key])
                        print(f"🟩 Filled: {key}")
                        count += 1
                        break

            except Exception as e:
                print("⚠️ Couldn't fill a field:", e)

        print(f"🎯 Filled {count} fields automatically!")

        return {"status": "success", "message": f"Ability7 executed. ({count} fields filled)"}
    
    except Exception as e:
        print("❌ Ability 7 Error:", e)
        return {"status": "error", "error": str(e)}