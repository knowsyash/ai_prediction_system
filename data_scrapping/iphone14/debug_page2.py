import requests
from bs4 import BeautifulSoup

s = requests.Session()
cookies = [
    ('at-acbin',    'Atza|gQApRDzpAwEBAKHKpOfx9sj8OBhb-iGgDgwqn-HezwX5qN_HGbZkE7XskDXF9BIVNHRZXCAuAdWBFN-ZgTSQJZCco9TstqxlNaI6lRFxEc_X2fsV9AucK9vvUkQso9ka-35FCue_CXdPqlYBT-BQUWe08XMYmC-nB1EFJ79wTQuXTGUz7aFfTZ-ksFcSwZ910VG53_L10_xgpJk4oqxSIq8Muw9ZbKMeaIxHT8C6b7pJuc0DTHMb5ZbH8ojpEuFXjE4YhhsV-efe70DQlvJAsZK0b5IrkNdyJ25VocmENVgbiELDMuxOg63rmuppI6rz8s_vornM6tqWC90Cn4N1CRxnHlw6s5yHvdLKAGAquA', '.amazon.in'),
    ('session-id',  '522-0179626-6331825', '.amazon.in'),
    ('session-token','gV7GdwCnLiKpf3zlr8DejVFf6D1qo8vGTa9kcOBpMPQ6ZnLy+g4MxRb0p2k25EI8on7WJ0wBXl8VnHFcCjojyBc/NG2RqQg/lKiAg15TfJQC7rATVL8xqh/2ll8rZqw0g7CmprEH25gRJ8tWWxInbbXXUEdz+ewZNfscNtK+GOjWuCwaklV1bKGAXFjqrbmglWSeLKnTQBPn7MS7FRyTmFpmnSMONzafaU+2ZvmU/gsjyiC/ejrGdaiP9s82eE6XLsUyI3Iog8qxMhpGzTMQ/YamdfiJVqvT2fE/GcZGlBjREZUR2vbz8vPbLZMIRm2KgHbPRLRWNI4j3MupQlVypYkg6KnIg+d+j82oWqOUuwrWmmoTN9z/jM+J9dhpvK9v', '.amazon.in'),
    ('ubid-acbin',  '521-5890498-6216253', '.amazon.in'),
    ('x-acbin',     '"Plsud9HAH3@vsAlSKBai7ZsFRtT?xQFgqNJ5ZWapin5vWSCksTVCW3H3NQxMjxka"', '.amazon.in'),
]
for n, v, d in cookies:
    s.cookies.set(n, v, domain=d, path='/')

headers = {
    'User-Agent':   'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Accept':       'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-IN,en;q=0.9',
    'Referer':      'https://www.amazon.in/product-reviews/B0BDJS3MRM/ref=cm_cr_dp_d_show_all_btm?ie=UTF8&reviewerType=all_reviews',
}

url = 'https://www.amazon.in/product-reviews/B0BDJS3MRM/ref=cm_cr_getr_d_paging_btm_next_2?ie=UTF8&reviewerType=all_reviews&pageNumber=2'
print(f"Fetching: {url}")
r = s.get(url, headers=headers, timeout=30)
soup = BeautifulSoup(r.text, 'html.parser')

reviews = soup.find_all(attrs={'data-hook': 'review'})
print(f"Status  : {r.status_code}")
print(f"Final URL: {r.url}")
print(f"Reviews  : {len(reviews)}")

# Which page is selected in pagination?
active = soup.find('li', class_='a-selected')
print(f"Active page: {active.get_text(strip=True) if active else 'NOT FOUND'}")

# First 3 review titles
for rv in reviews[:3]:
    t = rv.find(attrs={'data-hook': 'review-title'})
    print(f"  Title: {t.get_text(strip=True)[:70] if t else 'no title'}")

# Save raw HTML for inspection
with open('page2_debug.html', 'w', encoding='utf-8') as f:
    f.write(r.text)
print("\nSaved raw HTML to page2_debug.html")
print(f"Signed in: {'ap/signin' not in r.url}")
