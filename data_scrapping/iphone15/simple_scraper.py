"""Simple Flipkart Review Scraper - Updated for 2026"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import re
from datetime import datetime

class SimpleFlipkartScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        self.reviews = []
        self.progress_file = 'simple_save.txt'
        self.last_successful_page = None
        self.consecutive_empty = 0
        
    def log_progress(self, message):
        """Log progress to text file"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.progress_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")
        
    def clean_text(self, text):
        """Remove emojis, extra spaces, and noise from text"""
        # Remove emojis and non-ASCII characters
        text = re.sub(r'[^\x00-\x7F]+', ' ', text)
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?-]', '', text)
        return text.strip()
    
    def scrape_page(self, url):
        """Scrape a single page with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=self.headers, timeout=15)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                
                page_reviews = []
                all_divs = soup.find_all('div')
                seen_reviews = set()
                
                for div in all_divs:
                    div_text = div.get_text(separator='|', strip=True)
                    
                    if div_text and len(div_text) > 15:
                        if div_text[0] in ['1', '2', '3', '4', '5']:
                            rating = div_text[0]
                            remaining = div_text[1:].strip()
                            parts = [p.strip() for p in remaining.split('|') if p.strip()]
                            
                            if len(parts) >= 2:
                                title = self.clean_text(parts[0])
                                review_text = self.clean_text(' '.join(parts[1:]))
                                
                                # Filter out navigation and noise
                                invalid_keywords = ['Flipkart', 'Login', 'Cart', 'Electronics', 'TVs', 
                                                  'Appliances', 'Become a Seller', 'Advertise', 'Gift Cards',
                                                  'Help Center', 'Contact Us', 'About Us', 'Page', 'NEXT',
                                                  'Certified Buyer', 'Report Abuse', 'Permalink', 'Helpful',
                                                  'Like', 'Unlike', 'Share', 'Comment', 'READ MORE']
                                
                                has_noise = any(kw in title for kw in invalid_keywords) or any(kw in review_text[:50] for kw in invalid_keywords)
                                has_numbers_only = title.replace(' ', '').isdigit()
                                
                                is_valid = (len(review_text) > 15 and 
                                           len(title) < 100 and
                                           len(title) > 3 and
                                           not has_noise and
                                           not has_numbers_only)
                                
                                if is_valid:
                                    review_key = f"{rating}_{title[:30]}_{review_text[:30]}"
                                    if review_key not in seen_reviews:
                                        seen_reviews.add(review_key)
                                        page_reviews.append({
                                            'rating': int(rating),
                                            'title': title,
                                            'review_text': review_text[:500]
                                        })
                
                return page_reviews
                
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = 10 * (attempt + 1)
                    self.log_progress(f"Network error on attempt {attempt+1}/{max_retries}. Retrying in {wait_time}s...")
                    print(f"⚠ Network error, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    self.log_progress(f"Failed after {max_retries} attempts: {str(e)}")
                    print(f"❌ Error: Network failure")
                    return []
            except Exception as e:
                self.log_progress(f"Unexpected error: {str(e)}")
                print(f"❌ Error: {str(e)[:50]}")
                return []
        
        return []
    
    def scrape_reviews(self, base_url, max_pages=100, start_page=1, reverse=False):
        if reverse:
            self.log_progress(f"Starting REVERSE scrape from page {start_page} down to 1")
            print(f"Starting REVERSE scrape from page {start_page} down to 1... Target: {start_page} pages\n")
            page_range = range(start_page, 0, -1)
        else:
            self.log_progress(f"Starting scrape from page {start_page} to {max_pages}")
            print(f"Starting scrape from page {start_page} to {max_pages}... Target: {max_pages - start_page + 1} pages\n")
            page_range = range(start_page, max_pages + 1)
        
        page_count = 0
        
        for page in page_range:
            if page == 1:
                url = base_url
            else:
                url = f"{base_url}&page={page}"
            
            if reverse:
                print(f"[Page {page}/1] Fetching...", end=' ')
            else:
                print(f"[Page {page}/{max_pages}] Fetching...", end=' ')
            
            page_reviews = self.scrape_page(url)
            
            if page_reviews:
                self.reviews.extend(page_reviews)
                self.last_successful_page = page
                self.consecutive_empty = 0
                self.log_progress(f"Page {page}: Found {len(page_reviews)} reviews (Session total: {len(self.reviews)})")
                print(f"✓ Found {len(page_reviews)} reviews (Total: {len(self.reviews)})")
            else:
                self.consecutive_empty += 1
                self.log_progress(f"Page {page}: No reviews found (Consecutive empty: {self.consecutive_empty})")
                print("⚠ No reviews found")
                
                # Stop if 5 consecutive pages have no reviews
                if self.consecutive_empty >= 5:
                    self.log_progress(f"STOPPING: 5 consecutive pages with no reviews. Last successful: Page {self.last_successful_page}")
                    print(f"\n⚠ Stopping: 5 consecutive pages with no reviews")
                    print(f"Last successful page: {self.last_successful_page}")
                    break
            
            page_count += 1
            
            # Save every 5 pages
            if page_count % 5 == 0:
                saved_count = self.save_to_csv('iphone15_reviews.csv')
                self.reviews = []  # Clear memory after saving
                self.log_progress(f"Progress checkpoint: Saved at page {page}. Total reviews in file: {saved_count}")
                print(f"\n📊 Progress saved at page {page}\n")
            
            # Be polite to the server
            time.sleep(random.uniform(3, 6))
        
        # Final save
        if self.reviews:
            saved_count = self.save_to_csv('iphone15_reviews.csv')
            self.log_progress(f"Final save completed. Total reviews: {saved_count}")
        
        return self.reviews
    
    def save_to_csv(self, filename='iphone15_reviews.csv'):
        if self.reviews:
            try:
                existing_df = pd.read_csv(filename)
                if existing_df.empty or len(existing_df.columns) == 0:
                    raise ValueError("Empty CSV")
                
                new_df = pd.DataFrame(self.reviews)
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                combined_df = combined_df.drop_duplicates(subset=['title', 'review_text'], keep='first')
                combined_df.to_csv(filename, index=False)
                return len(combined_df)
            except (FileNotFoundError, ValueError, pd.errors.EmptyDataError):
                df = pd.DataFrame(self.reviews)
                df.to_csv(filename, index=False)
                return len(df)
        else:
            return 0

def main():
    url = "https://www.flipkart.com/apple-iphone-15-black-128-gb/product-reviews/itm6ac6485515ae4?pid=MOBGTAGPTB3VS24W&lid=LSTMOBGTAGPTB3VS24WKFODHL&marketplace=FLIPKART"
    
    print("="*60)
    print("SIMPLE FLIPKART REVIEW SCRAPER")
    print("="*60)
    print("Product: Apple iPhone 15 (Black, 128 GB)\n")
    
    scraper = SimpleFlipkartScraper()
    scraper.log_progress("="*60)
    scraper.log_progress("Scraper started - Resuming from page 520")
    
    try:
        reviews = scraper.scrape_reviews(url, max_pages=949, start_page=520, reverse=False)
        df_count = scraper.save_to_csv('iphone15_reviews_new.csv')
        
        if df_count > 0:
            df = pd.read_csv('iphone15_reviews_new.csv')
            print(f"\n{'='*60}")
            print(f"STATISTICS")
            print(f"{'='*60}")
            print(f"Total Reviews: {len(df)}")
            print(f"\nRating Distribution:")
            print(df['rating'].value_counts().sort_index())
            print(f"{'='*60}")
            scraper.log_progress(f"Scraping completed successfully. Total reviews: {len(df)}")
        
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted! Saving progress...")
        scraper.log_progress("Scraper interrupted by user")
        saved_count = scraper.save_to_csv('iphone15_reviews_new.csv')
        scraper.log_progress(f"Progress saved. Total reviews: {saved_count}")
        print("✓ Progress saved")
    except Exception as e:
        scraper.log_progress(f"Fatal error: {str(e)}")
        print(f"Fatal error: {e}")

if __name__ == "__main__":
    main()
