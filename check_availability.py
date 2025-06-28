import requests
import time
import re
import logging
import os
import traceback
from datetime import date
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException, TimeoutException, SessionNotCreatedException

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Configure logging
logging.basicConfig(
    filename='logs/sokol_checker.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Add console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
logging.getLogger().addHandler(console_handler)

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Run in headless mode
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    # Add these options to fix the DevToolsActivePort error
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--remote-debugging-port=9222')
    chrome_options.add_argument('--disable-extensions')
    
    if os.getenv('CHROME_BIN') is not None:
        chrome_options.binary_location = os.getenv('CHROME_BIN', '/usr/bin/chromium')
        service = Service(executable_path=os.getenv('CHROMEDRIVER_PATH', '/usr/bin/chromedriver'))
        return webdriver.Chrome(service=service, options=chrome_options)
    
    return webdriver.Chrome(options=chrome_options)

def check_availability(max_retries=3):
    retry_count = 0
    while retry_count < max_retries:
        driver = None
        try:
            driver = setup_driver()
            url = 'https://klubsokol.nakiedy.pl/'
            driver.get(url)
            
            wait = WebDriverWait(driver, 10)
           
            # Try to find the link by data-id
            # logging.info("Trying to find link with data-id=48203...")
            
            # Find link by data-id attribute
            link = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[data-id='48203']")))
            logging.info(f"Found link with data-id=48203 (Blazej Bravo): {link.text}, href: {link.get_attribute('href')}")
            
            link.click()
            
            # Wait for any <a> elements to appear and log their text
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "a")))
            all_links = driver.find_elements(By.TAG_NAME, "a")
            
            logging.info("Found links after click:")
            for link in all_links:
                try:
                    text = link.text.strip()
                    if text:  # Only log non-empty text
                        
                        time_pattern = r"\d{1,2}:\d{2}"
                        if re.match(time_pattern, text):
                            return True
                except Exception as e:
                    logging.error(f"Error processing link: {e}")
                    requests.post('https://ntfy.sh/sokol', data='Błąd linku.')
                    continue
            return False
        
        except (WebDriverException, SessionNotCreatedException) as e:
            retry_count += 1
            logging.error(f"Browser session error (attempt {retry_count}/{max_retries}): {str(e)}")
            if retry_count < max_retries:
                logging.info(f"Retrying in 30 seconds...")
                time.sleep(30)
            else:
                logging.error(f"Max retries reached. Could not establish browser session.")
                requests.post('https://ntfy.sh/sokol', data='Błąd sesji przeglądarki.')
                return False
                
        except Exception as e:
            logging.error(f"Unexpected error occurred: {str(e)}")
            logging.error(traceback.format_exc())
            requests.post('https://ntfy.sh/sokol', data='Nieoczekiwany Błąd! Sprawdź logi.')
            return False
        
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass  # Ignore errors when closing the driver

# Main loop to check periodically
while True:
    try:
        today = date.today()
        if today.weekday() in [2, 3, 4]:  # 2=Wednesday, 3=Thursday, 4=Friday
            requests.post('https://ntfy.sh/sokol', data='Zaczynam monitorowanie terminu.')
            found = False
            check_interval = 60  # Check every minute by default
            
            while not found:
                try:
                    if check_availability():
                        requests.post('https://ntfy.sh/sokol', data='Nowy termin Sokół!!!')
                        logging.info("Availability found!")
                        found = True
                    else:
                        logging.info("Availability not found.")
                    
                    # Wait before next check
                    time.sleep(check_interval)
                    
                except Exception as e:
                    logging.error(f"Error in check loop: {str(e)}")
                    logging.error(traceback.format_exc())
                    logging.info("Continuing after error...")
                    requests.post('https://ntfy.sh/sokol', data='Nieoczekiwany Błąd! Sprawdź logi.')
                    time.sleep(check_interval * 2)  # Wait longer after an error
            
            sleep_days = (6-today.weekday() + 1)
            logging.info(f"Taking a nap till Monday ({sleep_days} days)!")
            time.sleep(60 * 60 * 24 * sleep_days)
        else:
            logging.info(f"Today is {today.strftime('%A')}, not checking.")
            now = time.localtime()
            sleep_till = time.mktime((now.tm_year, now.tm_mon, now.tm_mday + 1, 10, 0, 0, 0, 0, 0))
            logging.info(f"Taking a nap till tomorrow. Will resume at: {time.ctime(sleep_till)}")
            time.sleep(sleep_till - time.mktime(now))
        
    except Exception as e:
        logging.error(f"Error in main loop: {str(e)}")
        logging.error(traceback.format_exc())
        logging.info("Restarting main loop after error...")
        requests.post('https://ntfy.sh/sokol', data='Nieoczekiwany Błąd! Retry za 5 minut.')
        time.sleep(300)  # Wait 5 minutes before restarting main loop
    
    time.sleep(60)
