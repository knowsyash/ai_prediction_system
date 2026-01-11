"""
Mobile Price Scraper - Simplified Version
Scrapes mobile phone data from Flipkart for price prediction
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime
import re


class MobileScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        self.data = []
    
    def get_number(self, text):
        """Extract first number from text"""
        if not text:
            return None
        numbers = re.findall(r'\d+', str(text))
        return int(numbers[0]) if numbers else None
    
    def find_element(self, soup, class_names):
        """Find element by trying multiple class names"""
        for cls in class_names:
            elem = soup.find(class_=cls)
            if elem:
                return elem
        return None
    
    def find_spec(self, specs, keywords):
        """Find spec value by keywords"""
        for key in keywords:
            for spec_key, value in specs.items():
                if key in spec_key:
                    return value
        return 'N/A'
    
    def scrape_product(self, url):
        """Scrape single product page"""
        try:
            time.sleep(2)
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            text = soup.get_text()
            
            p = {'date': datetime.now().strftime('%Y-%m-%d'), 'url': url}
            
            # Product name & brand
            name = self.find_element(soup, ['CEn5rD', 'LMizgS', 'B_NuCI', 'yhB1nd'])
            p['name'] = name.text.strip() if name else 'N/A'
            p['brand'] = p['name'].split()[0] if p['name'] != 'N/A' else 'N/A'
            
            # Price & discount
            price_elem = self.find_element(soup, ['hZ3P6w', '_30jeq3', '_16Jk6d'])
            p['price'] = self.get_number(price_elem.text.replace('₹', '').replace(',', '')) if price_elem else None
            
            orig_elem = self.find_element(soup, ['pjjBkO', '_3I9_wc', '_3auQ3N', 'yRaY8j'])
            orig_price = self.get_number(orig_elem.text) if (orig_elem and '₹' in orig_elem.text) else None
            p['original_price'] = orig_price if (orig_price and orig_price > p['price']) else p['price']
            
            disc_elem = self.find_element(soup, ['EXhNF1', '_3Ay6Sb', '_2Nx3a1', 'UkUFwK'])
            if disc_elem and '%' in disc_elem.text:
                p['discount'] = self.get_number(disc_elem.text)
            elif p['original_price'] > p['price']:
                p['discount'] = round(((p['original_price'] - p['price']) / p['original_price']) * 100, 1)
            else:
                p['discount'] = 0
            
            # Ratings
            rating_elem = self.find_element(soup, ['fKo7pT', '_3LWZlK', '_1BLPMq'])
            if rating_elem:
                try:
                    p['rating'] = float(rating_elem.text.replace('★', '').strip())
                except:
                    p['rating'] = None
            else:
                match = re.search(r'(\d\.\d)\s*★', text)
                p['rating'] = float(match.group(1)) if match else None
            
            ratings_elem = self.find_element(soup, ['Wphh3N', '_2_R_DZ', '_13vcmD'])
            if ratings_elem:
                nums = re.findall(r'[\d,]+', ratings_elem.text)
                p['total_ratings'] = int(nums[0].replace(',', '')) if nums else 0
            else:
                match = re.search(r'([\d,]+)\s+Ratings', text)
                p['total_ratings'] = int(match.group(1).replace(',', '')) if match else 0
            
            # Category ratings
            for category in ['camera', 'battery', 'display', 'design']:
                match = re.search(f'{category}.*?(\\d\\.\\d)', text, re.IGNORECASE)
                p[f'{category}_rating'] = float(match.group(1)) if match else None
            
            # Specifications
            specs = {}
            for row in soup.find_all('tr'):
                cells = row.find_all('td')
                if len(cells) >= 2:
                    specs[cells[0].text.strip().lower()] = cells[1].text.strip()
            
            # Regex fallback for specs
            if not specs:
                if m := re.search(r'(\d+)\s*GB\s*RAM', text, re.IGNORECASE):
                    specs['ram'] = f"{m.group(1)} GB"
                if m := re.search(r'(\d+)\s*GB\s*(?:ROM|Storage)', text, re.IGNORECASE):
                    specs['storage'] = f"{m.group(1)} GB"
                if m := re.search(r'(\d+)\s*mAh', text):
                    specs['battery'] = f"{m.group(1)} mAh"
                if cameras := re.findall(r'(\d+)\s*MP', text):
                    specs['camera'] = ' + '.join([f"{c} MP" for c in list(dict.fromkeys(cameras))[:2]])
                for pattern in [r'(A\d+\s+Bionic)', r'(Snapdragon\s+\d+)', r'(Exynos\s+\d+)', r'(Dimensity\s+\d+)']:
                    if m := re.search(pattern, text, re.IGNORECASE):
                        specs['processor'] = m.group(1)
                        break
            
            p['ram'] = self.find_spec(specs, ['ram', 'memory'])
            p['storage'] = self.find_spec(specs, ['storage', 'rom', 'internal'])
            p['battery'] = self.find_spec(specs, ['battery', 'battery capacity'])
            p['camera'] = self.find_spec(specs, ['camera', 'primary camera', 'rear camera'])
            p['processor'] = self.find_spec(specs, ['processor', 'chipset', 'cpu'])
            p['5g'] = 'Yes' if '5g' in p['name'].lower() else 'No'
            
            rating_str = f"{p['rating']}★" if p['rating'] else 'No rating'
            print(f"✓ {p['brand']} - ₹{p['price']:,} | {rating_str} | {p['ram']} RAM")
            return p
            
        except Exception as e:
            print(f"✗ Error: {e}")
            return None
    
    def scrape_all(self, urls):
        """Scrape multiple products"""
        print(f"\nScraping {len(urls)} products...\n")
        for i, url in enumerate(urls, 1):
            print(f"[{i}/{len(urls)}] ", end='')
            if product := self.scrape_product(url):
                self.data.append(product)
        print(f"\n✓ Completed: {len(self.data)} products scraped")
    
    def save_csv(self, filename='mobile_data.csv'):
        """Save data to CSV"""
        if not self.data:
            print("No data to save")
            return
        
        df = pd.DataFrame(self.data)
        df.to_csv(filename, index=False)
        print(f"✓ Saved to {filename}")
        print(f"\nSummary:")
        print(f"  Products: {len(df)}")
        print(f"  Price range: ₹{df['price'].min():,} - ₹{df['price'].max():,}")
        print(f"  Avg rating: {df['rating'].mean():.1f}")
    
    def view_data(self, filename='mobile_data.csv'):
        """View saved data"""
        df = pd.read_csv(filename)
        print("\n" + "="*80)
        print("MOBILE DATA")
        print("="*80)
        for _, row in df.iterrows():
            print(f"\n{row['brand']} - {row['name'][:50]}")
            print(f"  Price: ₹{row['price']:,} | Discount: {row['discount']}%")
            print(f"  Rating: {row['rating']}★ ({row['total_ratings']:,} ratings)")
            if pd.notna(row['camera_rating']):
                print(f"  📷 Camera: {row['camera_rating']} | 🔋 Battery: {row['battery_rating']} | 📱 Display: {row['display_rating']} | 🎨 Design: {row['design_rating']}")
            print(f"  RAM: {row['ram']} | Storage: {row['storage']} | Battery: {row['battery']}")
            print(f"  Camera: {row['camera']} | Processor: {row['processor']}")
        print("\n" + "="*80)


# Sample product URLs (update with current links)
PRODUCT_URLS = [
    'https://www.flipkart.com/apple-iphone-15-black-128-gb/p/itm6ac6485515ae4',
    'https://www.flipkart.com/samsung-galaxy-s24-exynos-5g-cobalt-violet-256-gb/p/itm93794d8fd6381',
    'https://www.flipkart.com/oneplus-12-silky-black-256-gb/p/itm4464454f95a2e',
]


if __name__ == "__main__":
    print("="*60)
    print("MOBILE SCRAPER")
    print("="*60)
    
    scraper = MobileScraper()
    
    print("\n1. Scrape products")
    print("2. View saved data")
    choice = input("\nChoice (1/2): ").strip()
    
    if choice == '1':
        scraper.scrape_all(PRODUCT_URLS)
        scraper.save_csv()
    elif choice == '2':
        scraper.view_data()
    else:
        print("Invalid choice")

