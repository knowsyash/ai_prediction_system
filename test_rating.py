import requests
from bs4 import BeautifulSoup
import re

url = "https://www.flipkart.com/apple-iphone-15-black-128-gb/product-reviews/itm6ac6485515ae4?pid=MOBGTAGPTB3VS24W&lid=LSTMOBGTAGPTB3VS24WKFODHL&marketplace=FLIPKART"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.content, 'html.parser')

# Find review containers
review_containers = soup.find_all('div', class_=re.compile(r'col.*_390CkK|cPHDOP'))
if not review_containers:
    review_containers = soup.find_all('div', class_=re.compile(r'_1AtVbE|col-12-12'))

print(f"Found {len(review_containers)} containers\n")

if review_containers:
    for i, review in enumerate(review_containers[:3]):  # Check first 3 reviews
        print(f"Review {i+1}:")
        print("="*60)
        
        # Try to find rating
        rating_div = review.find('div', class_=re.compile(r'MKifS6'))
        print(f"  Rating div found: {rating_div is not None}")
        if rating_div:
            print(f"  Rating text: '{rating_div.get_text(strip=True)}'")
            print(f"  Rating classes: {rating_div.get('class')}")
        else:
            # Show all divs with a single digit
            all_divs = review.find_all('div')
            print(f"  Searching {len(all_divs)} divs for rating...")
            for div in all_divs:
                text = div.get_text(strip=True)
                if text and len(text) <= 3 and any(c.isdigit() for c in text):
                    print(f"    Found div: class={div.get('class')}, text='{text}'")
        print()
