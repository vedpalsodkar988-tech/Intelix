from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def ability3_extract(task):
    try:
        print("🔍 Ability3: Extracting Information")

        driver = webdriver.Chrome(ChromeDriverManager().install())
        driver.maximize_window()

        driver.get("https://news.google.com/")
        print("🌍 Opening Google News...")

        headlines = driver.find_elements(By.TAG_NAME, "h3")
        extracted = [h.text for h in headlines[:5]]

        driver.quit()

        if not extracted:
            return "⚠ No headlines found."

        result = "\n".join(f"• {x}" for x in extracted)
        print("📰 Headlines Extracted Successfully!")

        return result

    except Exception as e:
        print("❌ Error in ability3:", str(e))
        return f"Error extracting information: {e}"

