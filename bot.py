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
from datetime import datetime, timedelta

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
# Use test url for testing the telegram notification (has a Steam Deck in stock)
TEST_URL = "https://scaxcodes.github.io/steamdeck-dummy-page/"
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
        all_btn = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//*[@id='SaleSection_33131']"))
        )
        text = all_btn[0].text.lower()
        print(f"Checked at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: {text}")
        # If "add" is in the text, we assume the item is available.
        if "add" in text:
            message = "🔥 Steam Deck Available! 🔥\nGet it now: https://store.steampowered.com/sale/steamdeckrefurbished"
            send_telegram_message(message)
            return True
    except Exception as e:
        print(f"Error during stock check: {e}")
    return False

def get_next_daily_ping_time():
    now = datetime.now()
    # Set target for 7 AM today
    target = now.replace(hour=7, minute=0, second=0, microsecond=0)
    # If it's already past 7 AM, schedule for tomorrow
    if now >= target:
        target += timedelta(days=1)
    return target

def monitor_stock():
    count = 0
    driver = start_driver()
    time.sleep(10)
    print("🔍 Started Monitoring...")
    
    # Flag to track stock availability from the latest check
    steam_deck_available = False
    next_daily_ping = get_next_daily_ping_time()

    while True:
        try:
            if count < 11:
                # Update availability flag based on current check
                steam_deck_available = check_stock(driver)
                
                # Check if it's time for the daily ping (at or after 7 AM)
                now = datetime.now()
                if now >= next_daily_ping:
                    daily_message = (
                        f"✅ Daily Ping: System running.\n"
                        f"Steam Deck Available: {steam_deck_available}\n"
                        f"Checked at: {now.strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                    send_telegram_message(daily_message)
                    next_daily_ping = get_next_daily_ping_time()
                
                # Determine delay: if available, wait 2 hours; otherwise, random 5-10 minutes
                if steam_deck_available:
                    delay = 7200  # 2 hours in seconds
                else:
                    delay = randint(300, 600)
                    
                print(f"⏳ Next check in {delay} seconds.")
                send_telegram_message(f"⏳ Next check in {delay} seconds.")
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
            monitor_stock()  # Restart monitoring recursively

try:
    monitor_stock()
except Exception as e:
    send_telegram_message(f"❌ Bot crashed: {e}")
