import requests
from bs4 import BeautifulSoup
import re

url = "https://www.safetyinsurance.com/"
headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
try:
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # 1. Grab Logo
    imgs = soup.find_all('img')
    print("LOGOS:")
    for img in imgs:
        src = img.get('src')
        if src and ('logo' in src.lower() or 'safety' in src.lower()):
            if src.startswith('/'):
                src = "https://www.safetyinsurance.com" + src
            print(src)

    # 2. Grab Stylesheets
    print("\nSTYLESHEETS:")
    for link in soup.find_all('link', rel='stylesheet'):
        href = link.get('href')
        if href and href.startswith('/'):
            href = "https://www.safetyinsurance.com" + href
            print(href)

except Exception as e:
    print(e)
