"""Test if curl_cffi actually gets different content on page 2"""
from curl_cffi import requests
from bs4 import BeautifulSoup
import time

ASIN = 'B0BDJS3MRM'

s = requests.Session(impersonate='chrome131')
cookies = [
    ('at-acbin',     'Atza|gQApRDzpAwEBAKHKpOfx9sj8OBhb-iGgDgwqn-HezwX5qN_HGbZkE7XskDXF9BIVNHRZXCAuAdWBFN-ZgTSQJZCco9TstqxlNaI6lRFxEc_X2fsV9AucK9vvUkQso9ka-35FCue_CXdPqlYBT-BQUWe08XMYmC-nB1EFJ79wTQuXTGUz7aFfTZ-ksFcSwZ910VG53_L10_xgpJk4oqxSIq8Muw9ZbKMeaIxHT8C6b7pJuc0DTHMb5ZbH8ojpEuFXjE4YhhsV-efe70DQlvJAsZK0b5IrkNdyJ25VocmENVgbiELDMuxOg63rmuppI6rz8s_vornM6tqWC90Cn4N1CRxnHlw6s5yHvdLKAGAquA', '.amazon.in'),
    ('session-id',   '522-0179626-6331825', '.amazon.in'),
    ('session-token','gV7GdwCnLiKpf3zlr8DejVFf6D1qo8vGTa9kcOBpMPQ6ZnLy+g4MxRb0p2k25EI8on7WJ0wBXl8VnHFcCjojyBc/NG2RqQg/lKiAg15TfJQC7rATVL8xqh/2ll8rZqw0g7CmprEH25gRJ8tWWxInbbXXUEdz+ewZNfscNtK+GOjWuCwaklV1bKGAXFjqrbmglWSeLKnTQBPn7MS7FRyTmFpmnSMONzafaU+2ZvmU/gsjyiC/ejrGdaiP9s82eE6XLsUyI3Iog8qxMhpGzTMQ/YamdfiJVqvT2fE/GcZGlBjREZUR2vbz8vPbLZMIRm2KgHbPRLRWNI4j3MupQlVypYkg6KnIg+d+j82oWqOUuwrWmmoTN9z/jM+J9dhpvK9v', '.amazon.in'),
    ('ubid-acbin',   '521-5890498-6216253', '.amazon.in'),
    ('x-acbin',      '"Plsud9HAH3@vsAlSKBai7ZsFRtT?xQFgqNJ5ZWapin5vWSCksTVCW3H3NQxMjxka"', '.amazon.in'),
    ('session-id-time','2082787201l', '.amazon.in'),
    ('lc-acbin',     'en_IN', '.amazon.in'),
    ('i18n-prefs',   'INR',   '.amazon.in'),
]
for n, v, d in cookies:
    s.cookies.set(n, v, domain=d, path='/')

h = {
    'User-Agent':       'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Accept':           'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language':  'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
    'sec-ch-ua':        '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest':   'document',
    'sec-fetch-mode':   'navigate',
    'sec-fetch-site':   'same-origin',
    'sec-fetch-user':   '?1',
    'Upgrade-Insecure-Requests': '1',
}

def titles(soup):
    out = []
    for rv in soup.find_all(attrs={'data-hook': 'review'}):
        t = rv.find(attrs={'data-hook': 'review-title'})
        if t:
            parts = [p.strip() for p in t.get_text('|').split('|')
                     if p.strip() and 'out of' not in p and len(p.strip()) > 2]
            out.append(parts[0] if parts else '?')
    return out

# --- Check if signed in ---
print("Checking auth...")
r0 = s.get(f'https://www.amazon.in/product-reviews/{ASIN}',
           headers={**h, 'Referer': 'https://www.amazon.in/'}, timeout=20)
signed_in = 'ap/signin' not in r0.url
print(f"  Signed in: {signed_in}  (status {r0.status_code})")
if not signed_in:
    print("  *** COOKIES EXPIRED — please refresh them from your browser ***")
    exit(1)

time.sleep(4)

# --- Page 1 ---
url1 = f'https://www.amazon.in/product-reviews/{ASIN}/ref=cm_cr_dp_d_show_all_btm?ie=UTF8&reviewerType=all_reviews'
r1   = s.get(url1, headers={**h, 'Referer': f'https://www.amazon.in/dp/{ASIN}'}, timeout=30)
s1   = BeautifulSoup(r1.text, 'html.parser')
t1   = titles(s1)
active1 = s1.find('li', class_='a-selected')
print(f"\nPage 1 ({len(t1)} reviews, active={active1.get_text(strip=True) if active1 else 'N/A'}):")
for t in t1: print(f"  {t}")

# Get the next-page href from the HTML itself
next_li = s1.find('li', class_='a-last')
next_href = (next_li.find('a') or {}).get('href') if next_li else None
print(f"\nNext href in HTML: {next_href}")

time.sleep(6)

# --- Page 2 using href from HTML ---
if next_href:
    url2 = 'https://www.amazon.in' + next_href
    r2   = s.get(url2, headers={**h, 'Referer': r1.url}, timeout=30)
    s2   = BeautifulSoup(r2.text, 'html.parser')
    t2   = titles(s2)
    active2 = s2.find('li', class_='a-selected')
    print(f"\nPage 2 using href ({len(t2)} reviews, active={active2.get_text(strip=True) if active2 else 'N/A'}):")
    t1_set = set(t1)
    for t in t2:
        tag = "DUP" if t in t1_set else "NEW"
        print(f"  [{tag}] {t}")
