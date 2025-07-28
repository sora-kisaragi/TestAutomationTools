"""Sample e2e script for test_case_id=1226.
現在は Google トップページを開いてタイトルに 'Google' が含まれるか確認するだけのダミーです。
本番では実際の画面遷移とアサーションに置き換えてください。
"""
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options


def test_google_title():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = Chrome(service=Service(ChromeDriverManager().install()), options=options)
    try:
        driver.get("https://www.google.com")
        assert "Google" in driver.title
    finally:
        driver.quit() 