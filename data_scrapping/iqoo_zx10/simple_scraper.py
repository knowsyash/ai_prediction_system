"""Simple Flipkart Review Scraper - Updated for 2026"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import re
import os
from datetime import datetime

class SimpleFlipkartScraper:
    def __init__(self):
        # Rotate between multiple user agents
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
        ]
        self.session = requests.Session()  # Use session for connection pooling
        self.reviews = []
        self.progress_file = 'simple_save.txt'
        self.last_successful_page = None
        self.consecutive_empty = 0
        self.request_count = 0
    
    def get_headers(self):
        """Get headers with rotated user agent"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
            'DNT': '1',
        }
        
    def log_progress(self, message):
        """Log progress to text file"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.progress_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")
    
    def save_last_page(self, page_num):
        """Save the last successful page in a parseable format"""
        try:
            with open('last_page.txt', 'w', encoding='utf-8') as f:
                f.write(f"LAST_SUCCESSFUL_PAGE={page_num}\n")
                f.write(f"TIMESTAMP={datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        except Exception as e:
            self.log_progress(f"Could not save last page: {str(e)}")
    
    def get_resume_page(self, csv_filename='iqoo_z10_reviews.csv'):
        """Dynamically determine resume page from existing CSV data and last_page.txt"""
        resume_page = 1
        csv_exists = False
        csv_count = 0
        
        # Check CSV file first
        try:
            if os.path.exists(csv_filename):
                df = pd.read_csv(csv_filename)
                csv_count = len(df)
                csv_exists = True
                # Estimate page number (assuming ~2-5 reviews per page, use conservative estimate)
                estimated_page = max(1, csv_count // 3)
                self.log_progress(f"CSV found: {csv_count} existing reviews → estimated page {estimated_page}")
                print(f"📊 Found existing CSV: {csv_count} reviews")
                resume_page = estimated_page
        except Exception as e:
            self.log_progress(f"Could not read CSV: {str(e)}")
        
        # Check last_page.txt - use whichever is higher
        try:
            if os.path.exists('last_page.txt'):
                with open('last_page.txt', 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.startswith('LAST_SUCCESSFUL_PAGE='):
                            page = int(line.split('=')[1].strip())
                            self.log_progress(f"last_page.txt shows: page {page}")
                            print(f"📄 last_page.txt: page {page}")
                            # Use the maximum of CSV estimate and last_page
                            resume_page = max(resume_page, page)
        except Exception as e:
            self.log_progress(f"Could not read last_page.txt: {str(e)}")
        
        # Resume from next page after the last successful one
        if resume_page > 1:
            resume_page += 1
            self.log_progress(f"Auto-Resume Decision: Starting from page {resume_page}")
            print(f"✅ Resuming from page {resume_page}")
        else:
            self.log_progress("Starting fresh from page 1")
            print(f"🆕 Starting fresh from page 1")
        
        return resume_page
        
    def clean_text(self, text):
        """Remove emojis, extra spaces, and noise from text"""
        # Remove emojis and non-ASCII characters
        text = re.sub(r'[^\x00-\x7F]+', ' ', text)
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?-]', '', text)
        return text.strip()
    
    def _parse_structured_reviews(self, soup):
        """Try to parse reviews using common Flipkart review card structures."""
        page_reviews = []

        review_blocks = soup.find_all('div', attrs={'data-review-id': True})
        if not review_blocks:
            review_blocks = soup.find_all('div', class_=re.compile(r'_2wzgFH|EPCmJX|_27M-vq|_1AtVbE'))

        for block in review_blocks:
            try:
                # Rating
                rating = None
                rating_tag = block.find('div', class_=re.compile(r'_3LWZlK|XQDdHH|_1BLPMq'))
                if rating_tag:
                    rating_text = rating_tag.get_text(strip=True)
                    if rating_text and rating_text[0] in ['1', '2', '3', '4', '5']:
                        rating = int(rating_text[0])

                # Title
                title_tag = block.find('p', class_=re.compile(r'_2-N8zT|z9E0IG'))
                title = self.clean_text(title_tag.get_text(strip=True)) if title_tag else ''

                # Review text
                review_tag = block.find('div', class_=re.compile(r't-ZTKy|qwjRop|_11B6mJ'))
                review_text = self.clean_text(review_tag.get_text(strip=True)) if review_tag else ''

                if review_text or title:
                    page_reviews.append({
                        'rating': rating if rating is not None else None,
                        'title': title,
                        'review_text': review_text[:500]
                    })
            except Exception:
                continue

        return page_reviews

    def scrape_page(self, url):
        """Scrape a single page with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Rotate user agent and add jitter to timing
                time.sleep(random.uniform(0.5, 1.5))
                self.request_count += 1
                
                # Add longer delays every 10 requests to appear more human
                if self.request_count % 10 == 0:
                    wait = random.uniform(8, 12)
                    self.log_progress(f"Human-like pause: {wait:.1f}s after {self.request_count} requests")
                    print(f"  ⏸ Pausing {wait:.1f}s...")
                    time.sleep(wait)
                
                response = self.session.get(url, headers=self.get_headers(), timeout=15)
                response.raise_for_status()
                
                # Force proper encoding
                response.encoding = response.apparent_encoding if response.apparent_encoding else 'utf-8'
                
                soup = BeautifulSoup(response.text, 'html.parser')

                # Strategy 1: structured parsing
                page_reviews = self._parse_structured_reviews(soup)

                # Strategy 2: fallback generic parsing (old method)
                if not page_reviews:
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
                url = f"{base_url}&page={page}" if '?' in base_url else f"{base_url}?page={page}"
            
            if reverse:
                print(f"[Page {page}/1] Fetching...", end=' ')
            else:
                print(f"[Page {page}/{max_pages}] Fetching...", end=' ')
            
            page_reviews = self.scrape_page(url)
            
            if page_reviews:
                self.reviews.extend(page_reviews)
                self.last_successful_page = page
                self.save_last_page(page)  # Save progress for auto-resume
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
                saved_count = self.save_to_csv('iqoo_z10_reviews.csv')
                self.reviews = []  # Clear memory after saving
                self.log_progress(f"Progress checkpoint: Saved at page {page}. Total reviews in file: {saved_count}")
                print(f"\n📊 Progress saved at page {page}\n")
            
            # Be polite to the server - vary the delay
            delay = random.uniform(4, 8)
            time.sleep(delay)
        
        # Final save
        if self.reviews:
            saved_count = self.save_to_csv('iqoo_z10_reviews.csv')
            self.log_progress(f"Final save completed. Total reviews: {saved_count}")
        
        return self.reviews
    
    def save_to_csv(self, filename='iqoo_z10_reviews.csv'):
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
    url = "https://www.flipkart.com/iqoo-z10-5g-glacier-silver-128-gb/product-reviews/itm14d2be4da59ea?pid=MOBHDG7HR7BFNC4A&lid=LSTMOBHDG7HR7BFNC4AZKRLX8&marketplace=FLIPKART"
    
    print("="*60)
    print("SIMPLE FLIPKART REVIEW SCRAPER - AUTO RESUME")
    print("="*60)
    print("Product: iQOO Z10 5G (Glacier Silver, 128 GB)\n")
    
    scraper = SimpleFlipkartScraper()
    scraper.log_progress("="*60)
    scraper.log_progress("Scraper started")
    
    # Check for resume
    resume_page = scraper.get_resume_page()
    if resume_page > 1:
        print(f"🔄 Auto-Resume: Continuing from page {resume_page}\n")
    else:
        print("🆕 Fresh Start: Beginning from page 1\n")
    
    try:
        reviews = scraper.scrape_reviews(url, max_pages=250, start_page=resume_page, reverse=False)
        df_count = scraper.save_to_csv('iqoo_z10_reviews_new.csv')
        
        if df_count > 0:
            df = pd.read_csv('iqoo_z10_reviews_new.csv')
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
        saved_count = scraper.save_to_csv('iqoo_z10_reviews_new.csv')
        scraper.log_progress(f"Progress saved. Total reviews: {saved_count}")
        print("✓ Progress saved")
    except Exception as e:
        scraper.log_progress(f"Fatal error: {str(e)}")
        print(f"Fatal error: {e}")

if __name__ == "__main__":
    main()
