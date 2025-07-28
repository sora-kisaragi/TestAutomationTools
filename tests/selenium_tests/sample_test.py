"""Sample Selenium test to verify environment setup.
Run with:  pytest tests/selenium/sample_test.py  -s
"""
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options


def test_google_title():
    """Open Google and assert title contains 'Google'."""
    options = Options()
    # headless mode (Chrome 109+). Remove '--headless=new' if GUI is needed.
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = Chrome(service=Service(ChromeDriverManager().install()), options=options)
    try:
        driver.get("https://www.google.com")
        assert "Google" in driver.title
    finally:
        driver.quit() 