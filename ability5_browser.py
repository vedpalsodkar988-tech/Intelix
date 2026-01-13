from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time

def smart_browser_task(task):
    """
    Ability 5 — Smart Browser Actions
    Opens Google, searches the user's task, and scrolls the page.
    NO DEBUG MODE - Auto opens Chrome!
    """

    print("🌐 Starting Ability 5 Browser Automation...")

    # Auto-open Chrome (no debug mode!)
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_experimental_option("detach", True)  # Keep browser open

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

    try:
        driver.get("https://www.google.com")
        time.sleep(2)

        search_box = driver.find_element(By.NAME, "q")
        search_box.clear()
        search_box.send_keys(task)
        search_box.submit()

        time.sleep(3)

        # Scroll for realism
        driver.execute_script("window.scrollBy(0, 500);")
        time.sleep(1)
        driver.execute_script("window.scrollBy(0, 500);")

        print("🌐 Ability 5 completed successfully!")
        return {"status": "success", "message": "Browser automation completed"}
    
    except Exception as e:
        print("❌ Ability 5 Error:", e)
        return {"status": "error", "error": str(e)}