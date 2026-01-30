"""Diagnostic script to check Flipkart page structure"""

import requests
from bs4 import BeautifulSoup
import random

# Multiple user agents to rotate
user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
]

headers = {
    'User-Agent': random.choice(user_agents),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Cache-Control': 'max-age=0',
}

# Test different pages
pages_to_test = [1, 5, 20, 37, 40, 50]
base_url = "https://www.flipkart.com/iqoo-z10-5g-glacier-silver-128-gb/product-reviews/itm14d2be4da59ea?pid=MOBHDG7HR7BFNC4A&lid=LSTMOBHDG7HR7BFNC4AZKRLX8&marketplace=FLIPKART"

print("="*70)
print("FLIPKART PAGE DIAGNOSTIC")
print("="*70)

for page_num in pages_to_test:
    try:
        if page_num == 1:
            url = base_url
        else:
            url = f"{base_url}&page={page_num}"
        
        print(f"\n[Page {page_num}] Testing: {url[:80]}...")
        
        response = requests.get(url, headers=headers, timeout=15)
        print(f"  Status Code: {response.status_code}")
        print(f"  Content Length: {len(response.content)} bytes")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Check for different review container patterns
        review_patterns = [
            ('data-review-id', soup.find_all('div', attrs={'data-review-id': True})),
            ('_2wzgFH', soup.find_all('div', class_='_2wzgFH')),
            ('EPCmJX', soup.find_all('div', class_='EPCmJX')),
            ('_27M-vq', soup.find_all('div', class_='_27M-vq')),
            ('_1AtVbE', soup.find_all('div', class_='_1AtVbE')),
            ('col', soup.find_all('div', class_=lambda x: x and 'col' in x)),
        ]
        
        found_any = False
        for pattern_name, elements in review_patterns:
            if elements:
                print(f"  ✓ Found {len(elements)} elements with pattern: {pattern_name}")
                found_any = True
        
        if not found_any:
            print(f"  ⚠ No review containers found!")
            
            # Check for anti-bot detection
            if "access denied" in response.text.lower() or "blocked" in response.text.lower():
                print(f"  🚫 DETECTED: Page contains blocking message")
            
            # Save HTML for inspection
            filename = f"page_{page_num}_debug.html"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(response.text)
            print(f"  💾 Saved HTML to: {filename}")
            
            # Show first 500 chars of page
            print(f"\n  First 500 chars of page content:")
            print(f"  {response.text[:500]}")
        
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")

print(f"\n{'='*70}")
print("DIAGNOSTIC COMPLETE")
print("="*70)
