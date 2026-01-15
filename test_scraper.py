"""
Test script to check what we're actually extracting
"""
import requests
from bs4 import BeautifulSoup
import re

url = "https://www.flipkart.com/apple-iphone-15-black-128-gb/product-reviews/itm6ac6485515ae4?pid=MOBGTAGPTB3VS24W&lid=LSTMOBGTAGPTB3VS24WKFODHL&marketplace=FLIPKART"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.content, 'html.parser')

# Find actual review containers (not the summary)
review_containers = soup.find_all('div', class_=re.compile(r'col.*_390CkK|cPHDOP'))
if not review_containers:
    review_containers = soup.find_all('div', class_=re.compile(r'_1AtVbE|col-12-12'))

print(f"Found {len(review_containers)} review containers using regex\n")

# Filter to get actual reviews (skip first few that might be summary)
actual_reviews = [r for r in review_containers if len(r.get_text(strip=True)) > 100]
print(f"Actual reviews with content: {len(actual_reviews)}\n")

if actual_reviews:
    first_review = actual_reviews[0]
    print("First actual review HTML:")
    print("="*80)
    print(first_review.prettify()[:2000])
    print("="*80)
    
    # Look for rating in this review
    print("\n\nSearching for rating pattern...")
    all_divs = first_review.find_all(['div', 'span'])
    for elem in all_divs:
        text = elem.get_text(strip=True)
        classes = elem.get('class', [])
        # Look for star ratings (★) or numbers 1-5
        if '★' in text or (text.isdigit() and len(text) == 1 and int(text) <= 5):
            print(f"  Tag: {elem.name}, Classes: {classes}, Text: '{text}'")
