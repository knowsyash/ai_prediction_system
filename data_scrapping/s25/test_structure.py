import requests
from bs4 import BeautifulSoup

url = 'https://www.flipkart.com/samsung-galaxy-s25-ultra-5g-titanium-silverblue-256-gb/product-reviews/itm413a5c3f30151?pid=MOBH8K8U5FWQWD6G'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

print("Fetching page...")
r = requests.get(url, headers=headers)
print(f'Status: {r.status_code}')

if r.status_code == 200:
    soup = BeautifulSoup(r.text, 'html.parser')
    
    # Save HTML
    with open('page_structure.html', 'w', encoding='utf-8') as f:
        f.write(r.text)
    print('Saved HTML')
    
    # Check for reviews
    divs = soup.find_all('div')
    rating_divs = [d for d in divs if d.get_text().strip() and len(d.get_text().strip()) > 50 and any(c in d.get_text()[:20] for c in ['1', '2', '3', '4', '5'])]
    print(f'Found {len(rating_divs)} potential review divs')
    
    # Sample output
    if rating_divs:
        print("\nFirst review sample:")
        print(rating_divs[0].get_text()[:200])
else:
    print(f'ERROR: Status {r.status_code}')
