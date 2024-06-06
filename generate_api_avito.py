import sqlite3
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from celery import Celery

# Инициализируем Celery приложение
celery = Celery('tasks', broker='redis://localhost:6379')

class DatabaseManager:
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()

    def update_user_data(self, user_id, api_link, link_avito):
        self.cursor.execute('SELECT transformed_linkavito, past_linkavito FROM settings WHERE user_id=?', (user_id,))
        row = self.cursor.fetchone()
        if row:
            self.cursor.execute(
                "UPDATE settings SET transformed_linkavito = ?, past_linkavito = ? WHERE user_id = ?",
                (api_link, link_avito, user_id))
            self.conn.commit()

    def close_connection(self):
        self.conn.close()

class WebScraper:
    def __init__(self, driver_path, options):
        self.driver = webdriver.Chrome(options=options, service=Service(driver_path))
        self.wait = WebDriverWait(self.driver, 10)

    def add_cookies(self, cookies):
        for cookie in cookies:
            self.driver.add_cookie(cookie)
        self.driver.refresh()

    def click_button(self, selector):
        button = self.wait.until(EC.presence_of_element_located((By.XPATH, selector)))
        button.click()

    def get_api_link(self):
        api_link = None
        for entry in self.driver.execute_script("return window.performance.getEntries()"):
            if 'api/11/items' in entry['name']:
                if 'page=1' in entry['name'] or ('lastStamp' in entry['name'] and 'display' in entry['name'] and 'limit' in entry['name']):
                    api_link = entry['name']
                    break
        return api_link

    def scrape(self, web):
        self.driver.get(web)
        try:
            self.click_button('//*[@id="app"]/div/div[1]/div/div/div[1]/div[2]/div[1]/div[2]/button[2]')
            self.click_button('button[data-marker="search-form/apply"]')
            return self.get_api_link()
        except TimeoutException:
            print("Не удалось найти элемент. Увеличьте время ожидания или проверьте селектор.")
        except ElementClickInterceptedException:
            print("ElementClickInterceptedException, попробуем еще раз.")
        finally:
            self.driver.quit()

@celery.task
def generate_avito_data(link_avito, user_id):
    options = webdriver.ChromeOptions()
    options.add_argument('--user-agent=Mozilla/5.0 (Linux; Android 9; SAMSUNG SM-G960F) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/15.0 Chrome/90.0.4430.82 Mobile Safari/537.36')
    # дополнительные настройки
    options.add_argument("--disable-extensions")
    options.add_argument('--disable-application-cache')
    options.add_argument('--disable-gpu')
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-setuid-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-geolocation")
    options.add_argument("--disable-logging")
    options.add_argument("--disable-crash-reporter")
    options.add_argument("--disable-default-apps")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver_path = 'C:/Users/user/PycharmProjects/sigmaparserbot/chromedriver.exe'
    scraper = WebScraper(driver_path, options)
    cookies = [
        # Список куки
    ]
    scraper.add_cookies(cookies)

    db_manager = DatabaseManager('settings.db')
    api_link = None
    attempt_count = 0

    while api_link is None and attempt_count < 3:
        api_link = scraper.scrape(link_avito)
        attempt_count += 1

    if attempt_count == 3:
        api_link = 'не сгенерировалась'

    db_manager.update_user_data(user_id, api_link, link_avito)
    db_manager.close_connection()

    print(api_link)
    return api_link