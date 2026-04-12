import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def __static__(url: str) ->(str,int):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
        "Connection": "keep-alive"
    }

    response = requests.get(url, headers=headers)

    return (response.text,response.status_code)

def __dynamic__(url : str)->str:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options = options)

    driver.get(url)
    html = driver.page_source
    driver.quit()
    return html
