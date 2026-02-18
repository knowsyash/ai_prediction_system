import requests

session = requests.Session()
cookies = [
    ('at-acbin','Atza|gQApRDzpAwEBAKHKpOfx9sj8OBhb-iGgDgwqn-HezwX5qN_HGbZkE7XskDXF9BIVNHRZXCAuAdWBFN-ZgTSQJZCco9TstqxlNaI6lRFxEc_X2fsV9AucK9vvUkQso9ka-35FCue_CXdPqlYBT-BQUWe08XMYmC-nB1EFJ79wTQuXTGUz7aFfTZ-ksFcSwZ910VG53_L10_xgpJk4oqxSIq8Muw9ZbKMeaIxHT8C6b7pJuc0DTHMb5ZbH8ojpEuFXjE4YhhsV-efe70DQlvJAsZK0b5IrkNdyJ25VocmENVgbiELDMuxOg63rmuppI6rz8s_vornM6tqWC90Cn4N1CRxnHlw6s5yHvdLKAGAquA','.amazon.in'),
    ('sess-at-acbin','a0F0xpVaA1cAAlV4S1+7WTET2lgodTlsB6+3jQEFmgs=','.amazon.in'),
    ('session-id','522-0179626-6331825','.amazon.in'),
    ('session-id-time','2082787201l','.amazon.in'),
    ('session-token','gV7GdwCnLiKpf3zlr8DejVFf6D1qo8vGTa9kcOBpMPQ6ZnLy+g4MxRb0p2k25EI8on7WJ0wBXl8VnHFcCjojyBc/NG2RqQg/lKiAg15TfJQC7rATVL8xqh/2ll8rZqw0g7CmprEH25gRJ8tWWxInbbXXUEdz+ewZNfscNtK+GOjWuCwaklV1bKGAXFjqrbmglWSeLKnTQBPn7MS7FRyTmFpmnSMONzafaU+2ZvmU/gsjyiC/ejrGdaiP9s82eE6XLsUyI3Iog8qxMhpGzTMQ/YamdfiJVqvT2fE/GcZGlBjREZUR2vbz8vPbLZMIRm2KgHbPRLRWNI4j3MupQlVypYkg6KnIg+d+j82oWqOUuwrWmmoTN9z/jM+J9dhpvK9v','.amazon.in'),
    ('ubid-acbin','521-5890498-6216253','.amazon.in'),
    ('x-acbin','"Plsud9HAH3@vsAlSKBai7ZsFRtT?xQFgqNJ5ZWapin5vWSCksTVCW3H3NQxMjxka"','.amazon.in'),
    ('sso-state-acbin','Xdsso|ZQG8qmxLHoaDJ3zEa95jYQRS7SK8gp0gyoGikL6Lq3FfrzEtY1uKxkCdIEYyBTrDhVpatfCOQ8bEpyOxsHREoQuSZH4iU4qVJxhRP1JOhExXlhQL','.amazon.in'),
    ('sst-acbin','Sst1|PQJ6Lnb9-fnCe8T0q34MRBQVCiELUbqMuu_T8PjXqEZUUq7-4LqyAFlWyf8k_O1DoGzWP491BNzS7CoCVb0Y7gapQ59TveJABmE170FPiXSTv18m0DDK09gpw4HojdfsK83iJA8ajnS2vqCUoe7senetXw53fHNVqm0fWsTntZo6iWyAtPRFBO-PbIu9nGwZ2nJf9aTaAwV9V2YwTLnFrXKx81J_RU2YGhJHT5h6q-ST5OBH92r-HTwlNN2OvNmWfr43fGQaUXtUO82nEpgPnX9D2Xo5X7zcTjzV2FTsHBNQhUfHqau1ykCsDET5WabV8hGG','.amazon.in'),
    ('lc-acbin','en_IN','.amazon.in'),
    ('i18n-prefs','INR','.amazon.in'),
]
for n, v, d in cookies:
    session.cookies.set(n, v, domain=d, path='/')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-IN,en;q=0.9',
    'Referer': 'https://www.amazon.in/',
}

url = 'https://www.amazon.in/product-reviews/B0BDJS3MRM/ref=cm_cr_dp_d_show_all_btm?ie=UTF8&reviewerType=all_reviews'
r = session.get(url, headers=headers, timeout=30)
html = r.text

with open('page1_debug.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('Status           :', r.status_code)
print('Final URL        :', r.url)
print('data-hook=review :', html.count('data-hook="review"'))
print('review-body      :', html.count('review-body'))
print('review-title     :', html.count('review-title'))
print('review-star      :', html.count('review-star-rating'))
print('Saved            : page1_debug.html')
