from bs4 import BeautifulSoup

with open('page1_debug.html', encoding='utf-8') as f:
    soup = BeautifulSoup(f.read(), 'html.parser')

reviews = soup.find_all(attrs={'data-hook': 'review'})
print(f'Total reviews: {len(reviews)}')

for i, r in enumerate(reviews[:3]):
    print(f'\n--- Review {i+1} ---')
    for t in r.find_all(attrs={'data-hook': True}):
        hook = t.get('data-hook')
        text = t.get_text(strip=True)[:120]
        print(f'  [{hook}] {text}')

    # Also print the review-date raw text (city is embedded here on Amazon)
    date_tag = r.find('span', attrs={'data-hook': 'review-date'})
    if date_tag:
        print(f'  DATE RAW: {date_tag.get_text()}')

    # Check genome-widget (reviewer name/location)
    genome = r.find(attrs={'data-hook': 'genome-widget'})
    if genome:
        print(f'  GENOME RAW: {genome.get_text(strip=True)[:200]}')
        print(f'  GENOME HTML: {str(genome)[:400]}')
