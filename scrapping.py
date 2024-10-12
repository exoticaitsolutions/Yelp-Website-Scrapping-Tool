import random
import os
import time
import re
from PyQt5.QtWidgets import QDesktopWidget ,QMessageBox
import pandas as pd
from PyQt5.QtGui import QTextCursor
import csv
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from seleniumbase import Driver
from fake_useragent import UserAgent
from difflib import SequenceMatcher
from fuzzywuzzy import fuzz
from PyQt5.QtWidgets import QFileDialog
from config import *


def print_the_output_statement(output, message):
    output.append(f"<b>{message}</b> \n \n")
    # Print the message to the console
    output.moveCursor(QTextCursor.End)
    print(message)

def center_window(window):
    qr = window.frameGeometry()
    cp = QDesktopWidget().availableGeometry().center()
    qr.moveCenter(cp)
    window.move(qr.topLeft())
# Setup Chrome options
def create_driver():
    user_agent = ua.random
    try:
       
        driver = Driver(uc=True, headless=False)
        # Execute the user agent script after the driver is created
        driver.execute_script(f"Object.defineProperty(navigator, 'userAgent', {{get: function() {{ return '{user_agent}'; }} }});")
        
        # Open the URL with the driver
        driver.uc_open_with_reconnect('https://www.yelp.nl/amsterdam', 4)
        driver.uc_gui_click_captcha()
        
        time.sleep(random.uniform(0.1, 0.3))
        return driver
    except Exception as e:
        print(f"Error creating driver: {e}")
        return False

# Read Excel data with a row limit
def read_excel_data(file_path,start_row=0, row_limit=30):
    # data = pd.read_excel(file_path, nrows=row_limit)
    data = pd.read_excel(file_path, skiprows=start_row, nrows=row_limit)
    return data

# Function to perform search on Yelp
def perform_search(driver, search_term, location):
    try:
        search_box = driver.find_element(By.XPATH, "//input[@id='search_description']")
        search_box.send_keys(Keys.ESCAPE)
        search_box.clear()
        search_box.send_keys(search_term)
        time.sleep(random.uniform(0.5, 1))

        location_box = driver.find_element(By.XPATH, "//input[@id='search_location']")
        driver.execute_script("arguments[0].scrollIntoView();", location_box)
        location_box.send_keys(Keys.ESCAPE)
        location_box.clear() 
        location_box.send_keys(location)
        time.sleep(random.uniform(0.5, 1))

        search_button = driver.find_element(By.XPATH, '//*[@id="header_find_form"]/div[3]/button')
        search_button.click()
        time.sleep(random.uniform(1, 3))
        driver.save_screenshot('yelp_results.png')
        print("Screenshot saved as 'yelp_results.png'")

    except NoSuchElementException as e:
        print(f"Error during search: {e}")

# Extract restaurant data
def extract_restaurant_data(driver):
    try:
        
        try:
            yelp_url = driver.current_url
        except AttributeError:
            print("Failed to retrieve the current URL. Setting default URL.")
            yelp_url = "not url"
        print(f"Yelp URL: {yelp_url}")

        # Try fetching restaurant addresses
        try:
            restaurant_address = driver.find_elements(By.CSS_SELECTOR, '.y-css-1d42clu .y-css-erq9ob:nth-child(3)')
            if not restaurant_address:  
                restaurant_address = driver.find_elements(By.CSS_SELECTOR, '.y-css-1d42clu .y-css-erq9ob:nth-child(2)')

        except NoSuchElementException:
            restaurant_address = "Address Not Found"

        addresses = [address.text.strip().replace("Route berekenen", "").strip() if address else "N/A" for address in restaurant_address]

        for address in addresses:
            cleaned_address = re.sub(r'\s*\d{5}\s*Verenigde Staten', '', address).strip()

            # Scrape restaurant name
            try:
                restaurant_names = driver.find_elements(By.CSS_SELECTOR, ".headingLight__09f24__N86u1.y-css-d4sgf9 h1")
                restaurant_name = restaurant_names[0].text if restaurant_names else "N/A"
            except NoSuchElementException:
                restaurant_name = "N/A"

            # Scrape rating
            try:
                restaurant_ratings = driver.find_elements(By.CSS_SELECTOR, 'span.y-css-kw85nd[data-font-weight="semibold"]')
                rating_float = restaurant_ratings[0].text if restaurant_ratings else "N/A"
            except (NoSuchElementException, IndexError):
                rating_float = "N/A"

            # Scrape website URL
            try:
                site_url = ""
                restaurant_siteurls = driver.find_elements(By.XPATH, '//div[@class="y-css-ea0iu5"]/p[2]/a')
                if restaurant_siteurls:
                    site_url = "https://" + restaurant_siteurls[0].text
                else:
                    site_url = "not url"
            except NoSuchElementException:
                site_url = "N/A"

            # Scrape phone number
            try:
                restaurant_phoneno = driver.find_elements(By.CSS_SELECTOR, '.y-css-1d42clu .y-css-erq9ob:nth-child(2)')
                phone_text = restaurant_phoneno[0].text if restaurant_phoneno else "N/A"
                if len(phone_text) != 14:
                    restaurant_phoneno = driver.find_elements(By.CSS_SELECTOR, '.y-css-1d42clu .y-css-erq9ob:nth-child(1)')
                    phone_text = restaurant_phoneno[0].text if restaurant_phoneno else "N/A"
                if len(phone_text) == 14:
                    phone_text = phone_text
                else:
                    phone_text = ''
            except NoSuchElementException:
                phone_text = "N/A"

            restaurant_data = {
                'restaurant_data':True,
                'yelplink': yelp_url,
                'restaurant_name': restaurant_name,
                'phone': phone_text,
                'site_url': site_url,
                'rating': rating_float,
                'address':cleaned_address
            }

            return restaurant_data
            # else:
            #     print("No matching address found. Skipping this restaurant.")

    except NoSuchElementException as e:
        print(f"Error extracting restaurant data: {e}")
    except TypeError as te:
        print(te)
    restaurant_data = {
                    'restaurant_data':False,
                    'yelplink': '',
                    'restaurant_name': '',
                    'phone': '',
                    'site_url': '',
                    'rating': '',
                    'address':''
                }
    return restaurant_data

def fuzzy_match(address1, address2, threshold=0.9):
    ratio = SequenceMatcher(None, address1.lower(), address2.lower()).ratio()
    return ratio >= threshold

def fuzz_address_match_token(addr1, addr2, threshold=80):
    similarity = fuzz.token_set_ratio(addr1, addr2)
    return similarity >= threshold


def scrape_yelp_data(driver, search_term, location):
    global SEARCH_COUNT
    perform_search(driver, search_term, location)
    time.sleep(random.uniform(0.5, 1.0))

    # list_items = driver.find_elements(By.CSS_SELECTOR, '.y-css-je5tk4')
    list_items = driver.find_elements(By.XPATH,'//*[@data-traffic-crawl-id="OrganicBusinessResult"]')

    
    if list_items:
        temp_list = []
        for index, li in enumerate(list_items, start=1):
            matched_button = li.find_element(By.XPATH, f'.//a')
            temp_list.append(matched_button.get_attribute('href'))
            
            if index == SEARCH_PER_PAGE: 
                break
      
        for url in temp_list:
            driver.get(url)
            SEARCH_COUNT += 1

            time.sleep(random.uniform(0.1, 2))
            try:
                data = extract_restaurant_data(driver)  # Pass driver and location]
            except:
                continue
            print(search_term, location)
            
            if data['restaurant_data']:
                address = data['address']
                response = fuzz_address_match_token(location,address)
                if response:
                    return data
            
        return {"restaurant_data": False,"data":"no restaurant listings found"}

    else:
        SEARCH_COUNT += 1
        print(f"No restaurant listings found for {search_term} at {location} (row {SEARCH_COUNT})")
        return {"restaurant_data": False,"data":"no restaurant listings found"}
    

def init_csv():
    with open(CSV_FILE_PATH, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['License Type', 'File Number', 'Primary Name', 'DBA Name', 'Prem Addr 1', 'Prem Addr 2', 'Prem City', 'Prem State', 'Prem Zip', 'Yelp Link', 'Yelp Name', 'Yelp Phone', 'Yelp Web Site', 'Yelp Rating'])

def append_data_in_csv(data):
    with open(CSV_FILE_PATH, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(data)
            return True
    return False

# Function to convert CSV to Excel
def convert_csv_to_excel():
    try:
        # Read the CSV file and convert it to an Excel file
        read_file = pd.read_csv(CSV_FILE_PATH)
        read_file.to_excel(EXCEL_FILE_PATH, index=None, header=True)
        return True
    except Exception as e:
        print(f"Error converting CSV to Excel: {e}")
        return False

# Function to prompt file download
def prompt_file_download(output_text):
    options = QFileDialog.Options()
    options |= QFileDialog.DontUseNativeDialog
    folder_dialog = QFileDialog()
    folder_dialog.setFileMode(QFileDialog.Directory)
    folder_dialog.setOptions(options)
    
    # Prompt user to select a folder
    folder_path = folder_dialog.getExistingDirectory(None, "Select Folder to Save Excel File", "")
    
    if folder_path:
        excel_file_name = "yelp_data.xlsx"  
        excel_file_path = os.path.join(folder_path, excel_file_name)
        try:
            os.rename(EXCEL_FILE_PATH, excel_file_path)
            print(f"File saved successfully as {excel_file_path}")
            print_the_output_statement(
                output_text, f"Data saved successfully to {excel_file_path}"
                )
        except Exception as e:
            print(f"Error saving file: {e}")
