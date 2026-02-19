"""Simple Flipkart Review Scraper - Updated for 2026"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import re
from datetime import datetime

class SimpleFlipkartScraper:
    CSV_FILENAME = 'iphone15_reviews.csv'
    
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0'
    ]
    
    def __init__(self):
        self.session = requests.Session()
        self.current_ua_index = 0
        self.reviews = []
        self.progress_file = 'simple_save.txt'
        self.last_successful_page = None
        self.consecutive_empty = 0
        self.total_in_file = self._count_existing_reviews()
        self.network_errors = 0
        
    def _count_existing_reviews(self):
        """Count reviews already in the CSV file"""
        try:
            df = pd.read_csv(self.CSV_FILENAME)
            return len(df)
        except:
            return 0
    
    def _get_headers(self):
        """Rotate user agents to avoid blocking"""
        self.current_ua_index = (self.current_ua_index + 1) % len(self.USER_AGENTS)
        return {
            'User-Agent': self.USER_AGENTS[self.current_ua_index],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
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
        max_retries = 5
        for attempt in range(max_retries):
            try:
                headers = self._get_headers()
                response = self.session.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                self.network_errors = 0  # Reset on success
                soup = BeautifulSoup(response.text, 'html.parser')
                
                page_reviews = []
                seen_reviews = set()
                
                # Find all divs and look for individual review patterns
                all_divs = soup.find_all('div')
                
                for div in all_divs:
                    text = div.get_text(separator='\n', strip=True)
                    
                    if not text or len(text) < 20:
                        continue
                    
                    lines = [l.strip() for l in text.split('\n') if l.strip()]
                    
                    # Look for pattern: rating on first line, title on second, review text after
                    if len(lines) >= 3:
                        first_line = lines[0].strip()
                        
                        # Check if first character is a rating 1-5
                        if first_line and first_line[0] in ['1', '2', '3', '4', '5']:
                            rating = first_line[0]
                            
                            # Skip if this looks like a summary (has "ratings and" or multiple reviews)
                            full_text = ' '.join(lines)
                            if 'ratings and' in full_text or 'User reviews sorted' in full_text:
                                continue
                            
                            # Get title (usually second line or part after rating)
                            title_candidates = []
                            review_candidates = []
                            
                            noise_keywords = ['Certified Buyer', 'Verified Purchase', 'Report Abuse', 
                                            'Permalink', 'Helpful', 'READ MORE', 'Review for Color',
                                            'Storage', 'ratings and', 'reviews']
                            
                            for i, line in enumerate(lines[1:], 1):
                                has_noise = any(kw in line for kw in noise_keywords)
                                if not has_noise and len(line) > 5:
                                    if i == 1 or (not title_candidates and len(line) < 100):
                                        title_candidates.append(line)
                                    else:
                                        review_candidates.append(line)
                            
                            if title_candidates and review_candidates:
                                title = self.clean_text(title_candidates[0])
                                review_text = self.clean_text(' '.join(review_candidates))
                                
                                # Validate
                                if (3 < len(title) < 150 and
                                    15 < len(review_text) < 1000 and
                                    not title.replace(' ', '').replace(',', '').isdigit()):
                                    
                                    review_key = f"{rating}_{title[:30]}_{review_text[:30]}"
                                    if review_key not in seen_reviews:
                                        seen_reviews.add(review_key)
                                        page_reviews.append({
                                            'rating': int(rating),
                                            'title': title,
                                            'review_text': review_text
                                        })
                
                return page_reviews
                
            except requests.exceptions.RequestException as e:
                self.network_errors += 1
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 10  # Exponential backoff: 10s, 20s, 40s, 80s
                    self.log_progress(f"Network error on attempt {attempt+1}/{max_retries}. Retrying in {wait_time}s... Error: {str(e)[:100]}")
                    print(f"⚠ Network error (#{self.network_errors}), retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    # Rotate user agent on retry
                    self._get_headers()
                else:
                    self.log_progress(f"Failed after {max_retries} attempts: {str(e)}")
                    print(f"❌ Error: Network failure after {max_retries} retries")
                    # If too many network errors, take a longer break
                    if self.network_errors > 10:
                        print("⚠ Too many network errors. Pausing for 5 minutes...")
                        time.sleep(300)
                        self.network_errors = 0
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
                saved_count = self.save_to_csv()
                self.reviews = []  # Clear memory after saving
                self.log_progress(f"Progress checkpoint: Saved at page {page}. Total reviews in file: {saved_count}")
                print(f"\n📊 Progress saved at page {page}. Total in file: {saved_count}\n")
            
            # Be polite to the server - longer delays to avoid blocking
            delay = random.uniform(5, 10)
            time.sleep(delay)
        
        # Final save
        if self.reviews:
            saved_count = self.save_to_csv()
            self.log_progress(f"Final save completed. Total reviews: {saved_count}")
        
        return self.total_in_file
    
    def save_to_csv(self, filename=None):
        if filename is None:
            filename = self.CSV_FILENAME
            
        if not self.reviews:
            # Return current file count even if no new reviews
            try:
                df = pd.read_csv(filename)
                return len(df)
            except:
                return 0
        
        try:
            # Create backup before saving
            import os
            import shutil
            if os.path.exists(filename):
                backup_name = filename.replace('.csv', '_backup.csv')
                shutil.copy2(filename, backup_name)
            
            # Load existing data
            try:
                existing_df = pd.read_csv(filename)
            except (FileNotFoundError, pd.errors.EmptyDataError):
                existing_df = pd.DataFrame(columns=['rating', 'title', 'review_text'])
            
            # Append new reviews
            new_df = pd.DataFrame(self.reviews)
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            
            # Remove duplicates
            combined_df = combined_df.drop_duplicates(subset=['title', 'review_text'], keep='first')
            
            # Save to file
            combined_df.to_csv(filename, index=False)
            
            self.total_in_file = len(combined_df)
            return len(combined_df)
            
        except Exception as e:
            self.log_progress(f"Error saving to CSV: {str(e)}")
            print(f"❌ Error saving: {str(e)}")
            return self.total_in_file

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
        total_count = scraper.scrape_reviews(url, max_pages=949, start_page=1, reverse=False)
        final_count = scraper.save_to_csv()
        
        if final_count > 0:
            df = pd.read_csv(scraper.CSV_FILENAME)
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
        saved_count = scraper.save_to_csv()
        scraper.log_progress(f"Progress saved. Total reviews: {saved_count}")
        print(f"✓ Progress saved. Total in file: {saved_count}")
    except Exception as e:
        scraper.log_progress(f"Fatal error: {str(e)}")
        print(f"Fatal error: {e}")

if __name__ == "__main__":
    main()
