"""Sample e2e script for test_case_id=1227.
このスクリプトはデモ用です。実際のテスト内容に合わせて書き換えてください。
"""
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options


def test_google_title():
    """Open Google and assert title contains 'Google'."""
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")

    driver = Chrome(service=Service(ChromeDriverManager().install()), options=opts)
    try:
        driver.get("https://www.google.com")
        assert "Google" in driver.title
    finally:
        driver.quit() 