from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

def click_type_task(task):
    print("👉 Ability 2: Starting typing automation...")

    # Auto-open Chrome with stealth settings
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_experimental_option("detach", True)
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )
    
    # Hide automation indicators
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    try:
        # Always open Google
        driver.get("https://www.google.com")
        time.sleep(3)  # Wait longer

        search_box = driver.find_element(By.NAME, "q")
        search_box.send_keys(task)
        search_box.send_keys(Keys.ENTER)
        
        time.sleep(3)

        print("✅ Ability 2 executed successfully!")
        return {"status": "success", "action": "typed on google", "message": "Search completed"}

    except Exception as e:
        print("❌ Ability 2 Error:", e)
        return {"status": "error", "error": str(e)}