import time
import json
import logging
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from .models import FacebookSession

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _get_driver():
    """Initializes and returns a Selenium Chrome driver."""
    options = ChromeOptions()
    # options.add_argument('--headless=new') # Running in headless mode can be detected by Facebook
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-notifications")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def login_and_save_session(account_id, password):
    """
    Logs into Facebook using Selenium, extracts session cookies, and saves them
    to the database.

    Args:
        account_id (str): The Facebook username or email.
        password (str): The Facebook password.

    Returns:
        bool: True if login and session saving were successful, False otherwise.
    """
    driver = _get_driver()
    try:
        logger.info(f"Attempting to log in as {account_id}")
        driver.get('https://www.facebook.com')
        time.sleep(2) # Allow page to load

        # Find and fill login form
        email_input = driver.find_element(By.ID, 'email')
        pass_input = driver.find_element(By.ID, 'pass')
        email_input.send_keys(account_id)
        time.sleep(1)
        pass_input.send_keys(password)
        time.sleep(1)
        
        # Click login button
        login_button = driver.find_element(By.NAME, 'login')
        time.sleep(10)
        login_button.click()
        time.sleep(5) # Wait for login to process and redirect

        # Check for login success (a simple check, might need improvement)
        if "login/device-based/regular/password/" in driver.current_url:
            logger.error("Login failed. Check credentials or 2FA.")
            return False

        logger.info("Login successful. Extracting cookies.")

        # Extract cookies
        all_cookies = driver.get_cookies()
        session_cookies = {
            cookie['name']: cookie['value'] 
            for cookie in all_cookies 
            if cookie['name'] in ['c_user', 'xs', 'datr', 'fr', 'sb', 'wd']
        }

        if 'c_user' not in session_cookies or 'xs' not in session_cookies:
            logger.error("Could not find essential session cookies (c_user, xs). Login may have failed.")
            return False

        # Go to a page to get the f_value
        driver.get('https://www.facebook.com/marketplace/mexicocity')
        time.sleep(3)
        f_value = None
        try:
            script_element = driver.execute_script("return document.getElementById('__eqmc')")
            if script_element:
                data = driver.execute_script("return JSON.parse(arguments[0].innerHTML)", script_element)
                f_value = data.get('f')
        except Exception as e:
            logger.warning(f"Could not extract f_value: {e}")

        if not f_value:
            logger.warning("f_value not found. Some API calls might fail.")

        # Save to database
        session, created = FacebookSession.objects.update_or_create(
            account_id=account_id,
            defaults={
                'cookies': session_cookies,
                'f_value': f_value or ''
            }
        )
        logger.info(f"Facebook session for {account_id} has been {'created' if created else 'updated'}.")
        return True

    except Exception as e:
        logger.error(f"An error occurred during Facebook login: {e}")
        return False
    finally:
        driver.quit()

def get_driver_with_session(account_id):
    """
    Retrieves a saved Facebook session and initializes a Selenium driver with it.

    Args:
        account_id (str): The account_id of the session to load.

    Returns:
        webdriver.Chrome: An authenticated Selenium driver, or None if session not found.
    """
    try:
        session = FacebookSession.objects.get(account_id=account_id)
        logger.info(f"Found session for {account_id}. Initializing driver.")
    except FacebookSession.DoesNotExist:
        logger.error(f"No session found for account_id: {account_id}")
        return None

    driver = _get_driver()
    try:
        # Selenium requires visiting the domain before adding cookies
        driver.get("https://www.facebook.com/")
        time.sleep(1)

        for name, value in session.cookies.items():
            cookie = {'name': name, 'value': value, 'domain': '.facebook.com'}
            driver.add_cookie(cookie)
        
        logger.info("Cookies added to the driver. Refreshing page.")
        driver.refresh()
        time.sleep(3) # Wait for page to load with cookies

        # Verify login by checking for a key element, e.g., profile name
        try:
            profile_element = driver.find_element(By.XPATH, "//a[contains(@href, '/me/') or contains(@href, '/profile.php')]")
            logger.info(f"Session restored successfully. Profile element found: {profile_element.text}")
            return driver
        except:
            logger.error("Failed to verify session. The cookies might be expired or invalid.")
            driver.quit()
            return None

    except Exception as e:
        logger.error(f"An error occurred while loading the session into the driver: {e}")
        driver.quit()
        return None
