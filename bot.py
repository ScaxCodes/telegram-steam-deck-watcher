import os
import time
import requests
from random import randint
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
URL = "https://store.steampowered.com/sale/steamdeckrefurbished"

# Configure Selenium
browser_options = Options()
browser_options.add_argument("--headless=new")
browser_options.add_argument("--no-sandbox")
browser_options.add_argument("--disable-dev-shm-usage")
browser_options.add_argument("--disable-gpu")

def send_telegram_message(message):
    notify_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}"
    requests.get(notify_url)

def start_driver():
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=browser_options)
    driver.get(URL)
    return driver

def check_stock(driver):
    try:
        all_btn = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, "//*[@id='SaleSection_33131']")))
        text = all_btn[0].text.lower()
        print(f"Checked: {text}")
        if "add" in text:
            message = "🔥 Steam Deck Available! 🔥\nGet it now: https://store.steampowered.com/sale/steamdeckrefurbished"
            send_telegram_message(message)
            return True
    except Exception as e:
        print(f"Error: {e}")
    return False

def monitor_stock():
    count = 0
    driver = start_driver()
    time.sleep(10)
    print("🔍 Started Monitoring...")

    while True:
        try:
            if count < 11:
                if check_stock(driver):
                    break
                delay = randint(10, 60)
                print(f"⏳ Next check in {delay} seconds.")
                time.sleep(delay)
                count += 1
                driver.refresh()
            else:
                print("🔄 Restarting browser...")
                driver.quit()
                time.sleep(20)
                count = 0
                driver = start_driver()
        except Exception as e:
            print(f"⚠️ Error: {e}")
            driver.quit()
            time.sleep(20)
            monitor_stock()

try:
    monitor_stock()
except Exception as e:
    send_telegram_message(f"❌ Bot crashed: {e}")
