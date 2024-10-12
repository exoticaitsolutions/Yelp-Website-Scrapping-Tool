import asyncio
from datetime import datetime
import inspect
import os
from screeninfo import get_monitors
import time
from threading import Event
from fake_useragent import UserAgent

current_directory = os.getcwd()
APP_TITLE = "Yelp Website Scraping"
APP_NAME = "Yelp Website Scraping"
FILE_TYPE = "xlsx"
HEADLESS = False
monitor = get_monitors()[0]
LOG_TYPE = "log"
WEBSITE_URL = "https://www.yelp.nl/amsterdam"
START_FROM_ROW = 527
LIMIT_NUMBER_OF_ROW = 200
SEARCH_PER_PAGE = 10
SEARCH_COUNT = 0
DRIVER_QUIT = 50
SEARCH_PER_PAGE = 10
ROW_LIMIT = 20
CSV_HEADERS = ['License Type', 'File Number', 'Primary Name', 'DBA Name', 'Prem Addr 1', 'Prem Addr 2', 'Prem City', 'Prem State', 'Prem Zip', 'Yelp Link', 'Yelp Name', 'Yelp Phone', 'Yelp Web Site', 'Yelp Rating']
EXCEL_FILE_PATH = "yelp_data.xlsx"
CSV_FILE_PATH = "data.csv"
ua = UserAgent()