from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Global driver reference
_global_driver = None

def _get_or_create_driver():
    """
    Try to reuse existing browser, or create new one
    """
    global _global_driver
    
    if _global_driver is None:
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_experimental_option("detach", True)
        
        _global_driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
    
    return _global_driver


def safe_submit_task() -> dict:
    """
    Ability 8:
    - Use existing Chrome window or open new one
    - Find a 'Submit' / 'Pay' / 'Register' button or input[type=submit]
    - Click it
    """
    try:
        driver = _get_or_create_driver()
    except Exception as e:
        return {
            "status": "error",
            "message": f"Could not open Chrome for submit: {e}",
        }

    try:
        # Try common submit patterns
        submit_el = None

        # 1) <button type="submit">
        try:
            submit_el = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        except Exception:
            submit_el = None

        # 2) <input type="submit">
        if submit_el is None:
            try:
                submit_el = driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
            except Exception:
                submit_el = None

        # 3) Any button with "submit"/"pay"/"register" text
        if submit_el is None:
            buttons = driver.find_elements(By.TAG_NAME, "button")
            for b in buttons:
                txt = (b.text or "").lower()
                if any(word in txt for word in ["submit", "pay", "register", "place order"]):
                    submit_el = b
                    break

        if submit_el is None:
            return {
                "status": "error",
                "message": "Could not find a submit/pay/register button on the page.",
            }

        driver.execute_script(
            "arguments[0].scrollIntoView({behavior:'smooth', block:'center'});",
            submit_el,
        )
        submit_el.click()

        return {
            "status": "success",
            "message": "Form submitted successfully by Intelix AI (Ability 8).",
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Error while clicking submit: {e}",
        }