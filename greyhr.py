from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from datetime import datetime, time as dt_time
import pytz
import os
import time
import traceback
import requests

# Telegram Bot Token and Chat ID from environment variables
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        print("Telegram message sent successfully.")
    else:
        print(f"Failed to send Telegram message: {response.text}")

# Credentials stored in environment variables for security
username = os.getenv('GREYTHR_USERNAME')
password = os.getenv('GREYTHR_PASSWORD')
url = "https://hgtl.greythr.com"

# Check if credentials are set
if not username or not password:
    print("Error: GREYTHR_USERNAME and GREYTHR_PASSWORD environment variables are not set.")
    exit()

# Set up the Chrome driver in headless mode
chrome_options = Options()
chrome_options.add_argument("--headless")  # Enable headless mode
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")  # Required for headless mode in some systems

# Define time ranges for attendance
morning_start = dt_time(9, 30)  # 9:30 AM
morning_end = dt_time(11, 30)  # 11:30 AM
night_start = dt_time(18, 0)   # 6:00 PM
night_end = dt_time(23, 0)     # 11:00 PM

# Get current time in IST
ist = pytz.timezone("Asia/Kolkata")
current_time = datetime.now(ist).time()

# Initialize driver to None
driver = None

try:
    # Check if the script is running within the allowed time range
    is_morning = morning_start <= current_time <= morning_end
    is_night = night_start <= current_time <= night_end

    if not is_morning and not is_night:
        print("Current time is outside allowed attendance times. Exiting...")
        exit()

    # Initialize the WebDriver with headless options
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)

    wait = WebDriverWait(driver, timeout=10)

    # Perform login
    wait.until(EC.visibility_of_element_located((By.NAME, "username"))).send_keys(username)
    wait.until(EC.visibility_of_element_located((By.NAME, "password"))).send_keys(password)
    wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/app-root/uas-portal/div/div/main/div/section/div[1]/o-auth/section/div/app-login/section/div/div/div/form/button'))).click()

    # Locate the attendance button
    button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.btn-container > .hydrated')))

    # Check the button text
    button_text = button.text.strip()
    print(f"Current button state: {button_text}")

    # Determine the action based on the time and button state
    if is_morning:
        print("Checking morning attendance...")
        if "Sign In" in button_text:
            print("Button state is Sign In. Clicking button...")
            button.click()
            send_telegram_message("Good morning! Just signed in successfully.")
        elif "Sign Out" in button_text:
            print("Button state is Sign Out. No action needed.")
            send_telegram_message("Good morning! Already signed in. No action needed.")
        else:
            print(f"Unknown button state: {button_text}")

    elif is_night:
        print("Checking evening attendance...")
        if "Sign Out" in button_text:
            print("Button state is Sign Out. Clicking button...")
            button.click()
            send_telegram_message("Oh dear, just now I've signed out. Don't worry!")
        elif "Sign In" in button_text:
            print("Button state is Sign In. No action needed.")
            send_telegram_message("Oh dear, already got your sign-out done. Don't worry!")
        else:
            print(f"Unknown button state: {button_text}")

    print("Attendance action completed!")

    # Optional: Wait to observe the changes
    time.sleep(5)

except Exception as ex:
    print("An error occurred:")
    traceback.print_exc()
    send_telegram_message("An error occurred while processing attendance. Check logs for details.")

finally:
    # Quit the driver only if it was initialized
    if driver:
        driver.quit()
