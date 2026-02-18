from bs4 import BeautifulSoup
import re, requests, time

s = requests.Session()
cookies = [
    ('at-acbin',     'Atza|gQApRDzpAwEBAKHKpOfx9sj8OBhb-iGgDgwqn-HezwX5qN_HGbZkE7XskDXF9BIVNHRZXCAuAdWBFN-ZgTSQJZCco9TstqxlNaI6lRFxEc_X2fsV9AucK9vvUkQso9ka-35FCue_CXdPqlYBT-BQUWe08XMYmC-nB1EFJ79wTQuXTGUz7aFfTZ-ksFcSwZ910VG53_L10_xgpJk4oqxSIq8Muw9ZbKMeaIxHT8C6b7pJuc0DTHMb5ZbH8ojpEuFXjE4YhhsV-efe70DQlvJAsZK0b5IrkNdyJ25VocmENVgbiELDMuxOg63rmuppI6rz8s_vornM6tqWC90Cn4N1CRxnHlw6s5yHvdLKAGAquA', '.amazon.in'),
    ('session-id',   '522-0179626-6331825', '.amazon.in'),
    ('session-token','gV7GdwCnLiKpf3zlr8DejVFf6D1qo8vGTa9kcOBpMPQ6ZnLy+g4MxRb0p2k25EI8on7WJ0wBXl8VnHFcCjojyBc/NG2RqQg/lKiAg15TfJQC7rATVL8xqh/2ll8rZqw0g7CmprEH25gRJ8tWWxInbbXXUEdz+ewZNfscNtK+GOjWuCwaklV1bKGAXFjqrbmglWSeLKnTQBPn7MS7FRyTmFpmnSMONzafaU+2ZvmU/gsjyiC/ejrGdaiP9s82eE6XLsUyI3Iog8qxMhpGzTMQ/YamdfiJVqvT2fE/GcZGlBjREZUR2vbz8vPbLZMIRm2KgHbPRLRWNI4j3MupQlVypYkg6KnIg+d+j82oWqOUuwrWmmoTN9z/jM+J9dhpvK9v', '.amazon.in'),
    ('ubid-acbin',   '521-5890498-6216253', '.amazon.in'),
    ('x-acbin',      '"Plsud9HAH3@vsAlSKBai7ZsFRtT?xQFgqNJ5ZWapin5vWSCksTVCW3H3NQxMjxka"', '.amazon.in'),
]
for n, v, d in cookies:
    s.cookies.set(n, v, domain=d, path='/')

h = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-IN,en;q=0.9',
}

def get_keys(soup):
    keys = []
    for rv in soup.find_all(attrs={'data-hook': 'review'}):
        tag = rv.find('i', {'data-hook': 'review-star-rating'}) or rv.find('span', {'data-hook': 'review-star-rating'})
        rating = None
        if tag:
            alt = tag.find('span', class_='a-icon-alt')
            if alt:
                m = re.search(r'([\d.]+)\s+out of', alt.get_text())
                if m: rating = round(float(m.group(1)))
        ttag = rv.find(attrs={'data-hook': 'review-title'})
        title = ''
        if ttag:
            parts = [p.strip() for p in ttag.get_text('|').split('|') if p.strip() and 'out of' not in p and len(p.strip()) > 2]
            title = parts[0] if parts else ''
        btag = rv.find('span', {'data-hook': 'review-body'})
        body = ''
        if btag:
            inner = btag.find('span')
            body = (inner.get_text() if inner else btag.get_text())[:50]
        keys.append((rating, title[:40], body[:40]))
    return keys

# Page 1
r1 = s.get('https://www.amazon.in/product-reviews/B0BDJS3MRM/ref=cm_cr_dp_d_show_all_btm?ie=UTF8&reviewerType=all_reviews',
           headers={**h, 'Referer': 'https://www.amazon.in/'}, timeout=30)
s1 = BeautifulSoup(r1.text, 'html.parser')
k1 = get_keys(s1)
print(f"=== PAGE 1 ({len(k1)} reviews) ===")
for k in k1: print(f"  {k[0]} | {k[1]} | {k[2][:30]}")

time.sleep(5)

# Page 2
r2 = s.get('https://www.amazon.in/product-reviews/B0BDJS3MRM/ref=cm_cr_getr_d_paging_btm_next_2?ie=UTF8&reviewerType=all_reviews&pageNumber=2',
           headers={**h, 'Referer': r1.url}, timeout=30)
s2 = BeautifulSoup(r2.text, 'html.parser')
k2 = get_keys(s2)
print(f"\n=== PAGE 2 ({len(k2)} reviews) ===")
p1_set = {f"{a}_{b[:30]}_{c[:30]}" for a,b,c in k1}
for k in k2:
    key = f"{k[0]}_{k[1][:30]}_{k[2][:30]}"
    dup = "DUP" if key in p1_set else "NEW"
    print(f"  [{dup}] {k[0]} | {k[1]} | {k[2][:30]}")
