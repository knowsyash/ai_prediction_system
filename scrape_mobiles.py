import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime
import re

class FlipkartMobileScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Connection': 'keep-alive',
        }
        self.data = []
    
    def extract_number(self, text):
        """Extract numeric value from text"""
        if not text:
            return None
        numbers = re.findall(r'\d+', str(text))
        return int(numbers[0]) if numbers else None
    
    def scrape_product_page(self, url):
        """Scrape individual product page"""
        try:
            time.sleep(2)  # Rate limiting
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            product_data = {
                'date_scraped': datetime.now().strftime('%Y-%m-%d'),
                'product_url': url
            }
            
            # Product Name (updated selectors for 2026)
            name_tag = (soup.find('span', {'class': 'CEn5rD'}) or 
                       soup.find('span', {'class': 'LMizgS'}) or
                       soup.find('span', {'class': 'B_NuCI'}) or 
                       soup.find('h1', {'class': 'yhB1nd'}))
            product_data['product_name'] = name_tag.text.strip() if name_tag else 'N/A'
            
            # Extract brand from product name
            if product_data['product_name'] != 'N/A':
                product_data['brand'] = product_data['product_name'].split()[0]
            else:
                product_data['brand'] = 'N/A'
            
            # Price (updated for 2026 structure)
            price_tag = (soup.find('div', {'class': 'hZ3P6w'}) or 
                        soup.find('div', {'class': '_30jeq3'}) or 
                        soup.find('div', {'class': '_30jeq3 _16Jk6d'}))
            if price_tag:
                price_text = price_tag.text.strip().replace('₹', '').replace(',', '')
                product_data['price'] = self.extract_number(price_text)
            else:
                product_data['price'] = None
            
            # Original Price (updated selectors)
            original_price_tag = (soup.find('div', {'class': 'pjjBkO'}) or
                                 soup.find('div', {'class': '_3I9_wc'}) or 
                                 soup.find('div', {'class': '_3auQ3N'}))
            if original_price_tag:
                original_price_text = original_price_tag.text.strip().replace('₹', '').replace(',', '')
                product_data['original_price'] = self.extract_number(original_price_text)
            else:
                product_data['original_price'] = product_data['price']
            
            # Discount (updated selectors)
            discount_tag = (soup.find('div', {'class': 'EXhNF1'}) or
                           soup.find('div', {'class': '_3Ay6Sb'}) or 
                           soup.find('div', {'class': '_2Nx3a1'}))
            if discount_tag:
                product_data['discount_percent'] = self.extract_number(discount_tag.text)
            else:
                if product_data['price'] and product_data['original_price']:
                    product_data['discount_percent'] = round(((product_data['original_price'] - product_data['price']) / product_data['original_price']) * 100, 2)
                else:
                    product_data['discount_percent'] = 0
            
            # Rating (updated selectors)
            rating_tag = (soup.find('div', {'class': 'fKo7pT'}) or
                         soup.find('div', {'class': '_3LWZlK'}) or 
                         soup.find('div', {'class': '_3LWZlK _1BLPMq'}))
            if rating_tag:
                rating_text = rating_tag.text.strip().replace('★', '').strip()
                try:
                    product_data['rating'] = float(rating_text)
                except:
                    product_data['rating'] = None
            else:
                product_data['rating'] = None
            
            # Reviews and Ratings count (updated selectors)
            reviews_tag = (soup.find('span', {'class': 'Wphh3N'}) or
                          soup.find('span', {'class': '_2_R_DZ'}) or 
                          soup.find('span', string=re.compile(r'Ratings')))
            if reviews_tag:
                reviews_text = reviews_tag.text.strip()
                numbers = re.findall(r'[\d,]+', reviews_text)
                if len(numbers) >= 2:
                    product_data['total_ratings'] = int(numbers[0].replace(',', ''))
                    product_data['total_reviews'] = int(numbers[1].replace(',', ''))
                elif len(numbers) == 1:
                    product_data['total_ratings'] = int(numbers[0].replace(',', ''))
                    product_data['total_reviews'] = 0
            else:
                product_data['total_ratings'] = 0
                product_data['total_reviews'] = 0
            
            # Specifications (updated selectors)
            specs = {}
            # Try new structure first
            spec_rows = (soup.find_all('tr', {'class': 'Kgzm3Z'}) or 
                        soup.find_all('tr', {'class': '_1s_Smc'}) or 
                        soup.find_all('li', {'class': 'rgWa7D'}))
            
            for row in spec_rows:
                # Try new class names
                spec_name = (row.find('td', {'class': 'rWazvI'}) or
                            row.find('td', {'class': '_1hKmbr'}))
                spec_value = (row.find('td', {'class': 'rWazvI'}) or
                             row.find('td', {'class': '_21lJbe'}))
                
                if spec_name and spec_value and spec_name != spec_value:
                    key = spec_name.text.strip().lower()
                    value = spec_value.text.strip()
                    specs[key] = value
                elif spec_name:  # Try finding sibling
                    siblings = list(row.find_all('td'))
                    if len(siblings) >= 2:
                        key = siblings[0].text.strip().lower()
                        value = siblings[1].text.strip()
                        specs[key] = value
            
            # Extract specific specs
            product_data['ram'] = self.extract_spec(specs, ['ram', 'memory'])
            product_data['storage'] = self.extract_spec(specs, ['storage', 'internal storage', 'rom'])
            product_data['battery'] = self.extract_spec(specs, ['battery', 'battery capacity'])
            product_data['camera_primary'] = self.extract_spec(specs, ['primary camera', 'rear camera', 'camera'])
            product_data['processor'] = self.extract_spec(specs, ['processor', 'chipset', 'cpu'])
            product_data['screen_size'] = self.extract_spec(specs, ['display', 'screen size', 'display size'])
            product_data['5g_support'] = self.check_5g_support(specs, product_data['product_name'])
            
            # Availability
            availability_tag = soup.find('div', {'class': '_16FRp0'}) or soup.find('button', string=re.compile('ADD TO CART', re.IGNORECASE))
            if availability_tag:
                availability_text = availability_tag.text.strip().lower()
                product_data['availability'] = 'In Stock' if 'add to cart' in availability_text or 'buy now' in availability_text else 'Out of Stock'
            else:
                product_data['availability'] = 'Unknown'
            
            # Delivery time - simplified
            delivery_tag = soup.find('div', {'class': '_2P_LDn'}) or soup.find('span', string=re.compile('delivery', re.IGNORECASE))
            if delivery_tag:
                delivery_text = delivery_tag.text.strip().lower()
                days = self.extract_number(delivery_text)
                product_data['delivery_days'] = days if days else 3
            else:
                product_data['delivery_days'] = None
            
            # Offers count
            offers_section = soup.find_all('li', {'class': '_16eBzU'})
            product_data['offers_count'] = len(offers_section)
            
            # Trending tag
            trending_tag = soup.find(string=re.compile('bestseller|trending', re.IGNORECASE))
            product_data['trending_tag'] = 'Yes' if trending_tag else 'No'
            
            print(f"✓ Scraped: {product_data['product_name']}")
            return product_data
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Error fetching {url}: {e}")
            return None
        except Exception as e:
            print(f"✗ Error parsing {url}: {e}")
            return None
    
    def extract_spec(self, specs, possible_keys):
        """Extract specification value by checking multiple possible keys"""
        for key in possible_keys:
            for spec_key, spec_value in specs.items():
                if key in spec_key:
                    return spec_value
        return 'N/A'
    
    def check_5g_support(self, specs, product_name):
        """Check if phone supports 5G"""
        product_name_lower = product_name.lower()
        if '5g' in product_name_lower:
            return 'Yes'
        
        for spec_key, spec_value in specs.items():
            if 'network' in spec_key or '5g' in spec_key:
                if '5g' in spec_value.lower():
                    return 'Yes'
        return 'No'
    
    def scrape_category_page(self, url, max_products=50):
        """Scrape product links from category page"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all product links
            product_links = []
            link_tags = soup.find_all('a', {'class': '_1fQZEK'}) or soup.find_all('a', {'class': 's1Q9rs'})
            
            for tag in link_tags[:max_products]:
                href = tag.get('href')
                if href:
                    full_url = 'https://www.flipkart.com' + href if href.startswith('/') else href
                    product_links.append(full_url)
            
            return list(set(product_links))  # Remove duplicates
            
        except Exception as e:
            print(f"✗ Error fetching category page: {e}")
            return []
    
    def scrape_multiple_products(self, product_urls):
        """Scrape multiple product pages"""
        for url in product_urls:
            product_data = self.scrape_product_page(url)
            if product_data:
                self.data.append(product_data)
            time.sleep(2)  # Delay between requests
    
    def save_to_csv(self, filename='mobile_data.csv'):
        """Save scraped data to CSV"""
        if not self.data:
            print("No data to save!")
            return
        
        df = pd.DataFrame(self.data)
        
        # Reorder columns
        column_order = ['date_scraped', 'brand', 'product_name', 'price', 'original_price', 
                       'discount_percent', 'rating', 'total_reviews', 'total_ratings',
                       'ram', 'storage', 'battery', 'camera_primary', 'processor', 
                       'screen_size', '5g_support', 'availability', 'delivery_days',
                       'offers_count', 'trending_tag', 'product_url']
        
        # Only include columns that exist
        column_order = [col for col in column_order if col in df.columns]
        df = df[column_order]
        
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"\n✓ Data saved to {filename}")
        print(f"Total products scraped: {len(self.data)}")


if __name__ == "__main__":
    scraper = FlipkartMobileScraper()
    
    # Example: Scrape specific product URLs
    product_urls = [
        # Add Flipkart product URLs here
        # Example: 'https://www.flipkart.com/apple-iphone-15-...'
    ]
    
    print("=" * 60)
    print("FLIPKART MOBILE SCRAPER")
    print("=" * 60)
    print("\nOptions:")
    print("1. Scrape from specific product URLs")
    print("2. Scrape from category page")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == '1':
        print("\nPaste product URLs (one per line, press Enter twice to finish):")
        urls = []
        while True:
            url = input().strip()
            if not url:
                break
            urls.append(url)
        
        if urls:
            print(f"\nStarting to scrape {len(urls)} products...")
            scraper.scrape_multiple_products(urls)
            scraper.save_to_csv()
    
    elif choice == '2':
        category_url = input("\nEnter Flipkart category page URL: ").strip()
        max_products = input("How many products to scrape? (default: 20): ").strip()
        max_products = int(max_products) if max_products else 20
        
        print(f"\nFetching product links from category page...")
        product_links = scraper.scrape_category_page(category_url, max_products)
        
        if product_links:
            print(f"Found {len(product_links)} product links")
            print(f"\nStarting to scrape products...")
            scraper.scrape_multiple_products(product_links)
            scraper.save_to_csv()
        else:
            print("No product links found!")
    
    else:
        print("Invalid choice!")
