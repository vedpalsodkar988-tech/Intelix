from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

def research_task(query):
    try:
        # Extract keyword for search
        keyword = query.lower().replace("research", "").replace("about", "").strip()
        if keyword == "":
            keyword = "latest technology"
        
        print("🔍 Research Query:", keyword)

        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        driver.get("https://www.google.com/search?q=" + keyword)

        time.sleep(3)

        # Collect summary from first result description
        results = driver.find_elements(By.CSS_SELECTOR, ".VwiC3b")
        summary = []

        for r in results[:4]:
            summary.append("• " + r.text)

        driver.quit()

        if not summary:
            summary = ["No research details found."]

        return {
            "status": "success",
            "title": f"Research Summary for: {keyword}",
            "data": summary
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}
