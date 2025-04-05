import os
import time
import requests
from random import randint
from datetime import datetime, timedelta
import threading
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
# Use this URL for testing purposes (has a Steam Deck in stock)
TEST_URL = "https://scaxcodes.github.io/steamdeck-dummy-page/"
URL = "https://store.steampowered.com/sale/steamdeckrefurbished"

# Configure Selenium
browser_options = Options()
browser_options.add_argument("--headless=new")
browser_options.add_argument("--no-sandbox")
browser_options.add_argument("--disable-dev-shm-usage")
browser_options.add_argument("--disable-gpu")

# Global variables to share status between threads
current_availability = False
last_check_time = None
last_command_time = datetime.min  # for rate-limiting /check command

def send_telegram_message(message):
    notify_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}"
    try:
        requests.get(notify_url)
    except Exception as e:
        print(f"Error sending Telegram message: {e}")

def start_driver():
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=browser_options)
    driver.get(URL)
    return driver

def check_stock(driver):
    global current_availability, last_check_time
    try:
        all_btn = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//*[@id='SaleSection_33131']"))
        )
        text = all_btn[0].text.lower()
        last_check_time = datetime.now()
        print(f"Checked at {last_check_time.strftime('%Y-%m-%d %H:%M:%S')}: {text}")
        # If "add" is in the text, we assume the item is available.
        if "add" in text:
            if not current_availability:
                # Send notification only when availability changes
                message = "🔥 Steam Deck Available! 🔥\nGet it now: https://store.steampowered.com/sale/steamdeckrefurbished"
                send_telegram_message(message)
            current_availability = True
            return True
        else:
            current_availability = False
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
    
    next_daily_ping = get_next_daily_ping_time()

    while True:
        try:
            if count < 11:
                # Update availability flag based on current check
                stock = check_stock(driver)
                
                # Daily ping: check if it's time for the daily message (at 7 AM)
                now = datetime.now()
                if now >= next_daily_ping:
                    daily_message = (
                        f"✅ Daily Ping: System running.\n"
                        f"Steam Deck Available: {current_availability}\n"
                        f"Last check: {last_check_time.strftime('%Y-%m-%d %H:%M:%S') if last_check_time else 'N/A'}"
                    )
                    send_telegram_message(daily_message)
                    next_daily_ping = get_next_daily_ping_time()
                
                # Determine delay: if available, wait 2 hours; otherwise, random 5-10 minutes
                if stock:
                    delay = 7200  # 2 hours in seconds
                else:
                    delay = randint(300, 600)
                    
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
            monitor_stock()  # Restart monitoring recursively

def handle_telegram_commands():
    global last_command_time
    last_update_id = None
    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
            if last_update_id:
                url += f"?offset={last_update_id}"
            response = requests.get(url).json()
            if response.get("ok"):
                for update in response.get("result", []):
                    last_update_id = update["update_id"] + 1
                    message = update.get("message")
                    if message and "text" in message:
                        text = message["text"].strip()
                        chat_id_from = message["chat"]["id"]
                        # Process the /check command
                        if text == "/check":
                            now = datetime.now()
                            # Only allow the command if at least 10 minutes have passed
                            if (now - last_command_time) >= timedelta(minutes=10):
                                last_command_time = now
                                status_message = (
                                    f"✅ Check Status:\n"
                                    f"Steam Deck Available: {current_availability}\n"
                                    f"Last Check: {last_check_time.strftime('%Y-%m-%d %H:%M:%S') if last_check_time else 'N/A'}"
                                )
                                send_telegram_message(status_message)
            time.sleep(15)  # Poll every 15 seconds for new commands
        except Exception as e:
            print(f"Error in command handler: {e}")
            time.sleep(15)

# Start the command handler in a separate thread
command_thread = threading.Thread(target=handle_telegram_commands, daemon=True)
command_thread.start()

try:
    monitor_stock()
except Exception as e:
    send_telegram_message(f"❌ Bot crashed: {e}")
