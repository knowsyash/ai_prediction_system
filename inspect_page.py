import requests
from bs4 import BeautifulSoup

url = 'https://www.flipkart.com/apple-iphone-15-black-128-gb/p/itm6ac6485515ae4'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

print("Fetching page...")
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.content, 'html.parser')

print("\n" + "=" * 60)
print("FINDING SPECIFICATIONS")
print("=" * 60)

# Look for specification tables
print("\n1. Looking for table rows with specifications...")
all_trs = soup.find_all('tr')
print(f"Found {len(all_trs)} table rows")

for i, tr in enumerate(all_trs[:20]):  # Check first 20
    tds = tr.find_all('td')
    if len(tds) >= 2:
        print(f"  Row {i}: {tds[0].text.strip()[:30]} = {tds[1].text.strip()[:30]}")

print("\n2. Looking for list items with specs...")
all_lis = soup.find_all('li', class_=True)
print(f"Found {len(all_lis)} list items with classes")

spec_related = [li for li in all_lis if 'GB' in li.text or 'RAM' in li.text or 'MP' in li.text or 'mAh' in li.text]
print(f"Found {len(spec_related)} spec-related items:")
for li in spec_related[:10]:
    print(f"  {li.get('class')}: {li.text.strip()[:60]}")

print("\n3. Looking for rating...")
rating_divs = soup.find_all('div', class_=True)
for div in rating_divs:
    if '★' in div.text or 'rating' in str(div.get('class')).lower():
        print(f"  {div.get('class')}: {div.text.strip()[:50]}")

print("\n4. Looking for all text with 'GB RAM'...")
ram_texts = soup.find_all(string=lambda x: 'GB RAM' in str(x) if x else False)
for text in ram_texts[:5]:
    print(f"  {text.strip()}")

print("\n5. Looking for battery info...")
battery_texts = soup.find_all(string=lambda x: 'mAh' in str(x) if x else False)
for text in battery_texts[:5]:
    print(f"  {text.strip()}")
