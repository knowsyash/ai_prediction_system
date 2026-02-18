"""Test script to check actual page structure"""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

# Setup Chrome
chrome_options = Options()
chrome_options.add_argument('--headless=new')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--window-size=1920,1080')

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

url = "https://www.flipkart.com/apple-iphone-15-black-128-gb/product-reviews/itm6ac6485515ae4?pid=MOBGTAGPTB3VS24W&lid=LSTMOBGTAGPTB3VS24WKFODHL&marketplace=FLIPKART"

print("Loading page...")
driver.get(url)
time.sleep(10)

# Scroll to load content
for _ in range(3):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1)

page_source = driver.page_source
soup = BeautifulSoup(page_source, 'html.parser')

print(f"\nPage size: {len(page_source)} bytes")
print(f"Has 'review': {'review' in page_source.lower()}")
print(f"Has 'rating': {'rating' in page_source.lower()}")

# Try different patterns
print("\n=== Looking for review containers ===")
patterns = [
    ('div with class containing "review"', soup.find_all('div', class_=lambda x: x and 'review' in x.lower())),
    ('div with class containing "col"', soup.find_all('div', class_=lambda x: x and 'col' in x.lower())),
    ('div with class "_27M-vq"', soup.find_all('div', class_='_27M-vq')),
    ('div with class "cPHDOP"', soup.find_all('div', class_='cPHDOP')),
    ('div with class "ZmyHeo"', soup.find_all('div', class_='ZmyHeo')),
]

for name, elements in patterns:
    print(f"{name}: {len(elements)} found")
    if elements and len(elements) > 0:
        print(f"  First element text preview: {elements[0].get_text()[:100]}")

# Look for rating elements
print("\n=== Looking for ratings ===")
rating_divs = soup.find_all('div', text=lambda x: x and x.strip() in ['1', '2', '3', '4', '5'])
print(f"Divs with rating text (1-5): {len(rating_divs)}")
if rating_divs:
    for i, div in enumerate(rating_divs[:3]):
        print(f"  Rating {i+1}: {div.get_text()} - Parent: {div.parent.name}")

# Save a sample of the HTML for manual inspection
with open('page_sample.html', 'w', encoding='utf-8') as f:
    f.write(page_source[:100000])  # First 100KB
print("\nFirst 100KB saved to page_sample.html for inspection")

driver.quit()
