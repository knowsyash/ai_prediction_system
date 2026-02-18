"""Simple Flipkart Review Scraper - Updated for 2026"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import re
from datetime import datetime

class SimpleFlipkartScraper:
    CSV_FILENAME = 'iphone16_reviews.csv'
    
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
    
    def _get_last_successful_page(self):
        """Read the last successful page from progress file"""
        try:
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # Search for last successful page from bottom up
                for line in reversed(lines):
                    if 'Page' in line and 'Found' in line and 'reviews' in line:
                        # Extract page number from log like "Page 12: Found 8 reviews"
                        match = re.search(r'Page (\d+):', line)
                        if match:
                            return int(match.group(1))
            return 0
        except:
            return 0
    
    def _calculate_resume_page(self, last_page):
        """Calculate resume page: nearest previous number divisible by 5, then +1"""
        if last_page == 0:
            return 1
        # Find nearest previous number divisible by 5
        nearest_divisible_by_5 = (last_page // 5) * 5
        # Start from next page after that checkpoint
        return nearest_divisible_by_5 + 1
    
    def _extract_and_format_date(self, text):
        """Extract date from text - handles both relative dates and actual dates like 'Oct, 2024'"""
        from datetime import datetime
        from dateutil.relativedelta import relativedelta
        
        # First, check for actual date format like "Oct, 2024" or "Jan 2025"
        actual_date_pattern = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[,\s]+(\d{4})', text, re.IGNORECASE)
        if actual_date_pattern:
            month_str = actual_date_pattern.group(1)
            year_str = actual_date_pattern.group(2)
            return f"{month_str} {year_str}"
        
        # Look for relative date patterns like "3 months ago", "2 weeks ago"
        month_pattern = re.search(r'(\d+)\s*months?\s*ago', text, re.IGNORECASE)
        week_pattern = re.search(r'(\d+)\s*weeks?\s*ago', text, re.IGNORECASE)
        day_pattern = re.search(r'(\d+)\s*days?\s*ago', text, re.IGNORECASE)
        year_pattern = re.search(r'(\d+)\s*years?\s*ago', text, re.IGNORECASE)
        
        current_date = datetime.now()
        review_date = None
        
        if year_pattern:
            years = int(year_pattern.group(1))
            review_date = current_date - relativedelta(years=years)
        elif month_pattern:
            months = int(month_pattern.group(1))
            review_date = current_date - relativedelta(months=months)
        elif week_pattern:
            weeks = int(week_pattern.group(1))
            review_date = current_date - relativedelta(weeks=weeks)
        elif day_pattern:
            days = int(day_pattern.group(1))
            review_date = current_date - relativedelta(days=days)
        
        if review_date:
            # Format as "Jan 2026" or "Nov 2025" (month and year only)
            return review_date.strftime('%b %Y')
        
        return None
    
    def _extract_city(self, text):
        """Extract city name from text - handles all Flipkart patterns"""
        # Remove phone numbers first
        text = re.sub(r'\d{10,}', '', text)
        
        # Pattern 1: ", City/District/Division" at the end (most common)
        # Matches: "text , Palakkad District", "text , Kochi", "text , New Delhi"
        city_match = re.search(r',\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:District|Division|City))?)[\s,]*$', text)
        if not city_match:
            # Pattern 2: ", City" before date
            city_match = re.search(r',\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:District|Division|City))?)\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', text, re.IGNORECASE)
        if not city_match:
            # Pattern 3: ", City" anywhere in middle/end
            city_match = re.search(r',\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3}(?:\s+(?:District|Division|City))?)', text)
        
        if city_match:
            potential_city = city_match.group(1).strip()
            
            # Remove dates if present
            potential_city = re.sub(r'\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec).*$', '', potential_city, flags=re.IGNORECASE).strip()
            
            # Filter noise words
            noise = ['Certified', 'Buyer', 'Verified', 'Purchase', 'READ', 'MORE', 
                    'Report', 'Abuse', 'Helpful', 'Permalink', 'Storage', 'Color',
                    'Customer', 'Flipkart', 'Review', 'Rating', 'Seller']
            
            if (potential_city and len(potential_city) > 2 and 
                not any(n.lower() in potential_city.lower() for n in noise)):
                return potential_city
        
        return None
    
    def _get_existing_review_keys(self):
        """Get unique keys of existing reviews to prevent duplicates"""
        try:
            df = pd.read_csv(self.CSV_FILENAME)
            keys = set()
            for _, row in df.iterrows():
                rating = str(row['rating'])
                title = str(row['title'])[:30]
                review_text = str(row['review_text'])[:30]
                key = f"{rating}_{title}_{review_text}"
                keys.add(key)
            return keys
        except:
            return set()
    
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
        
    def clean_text(self, text, remove_dates=True):
        """Remove emojis, extra spaces, noise, names, phone numbers and locations from text"""
        # Remove emojis and non-ASCII characters
        text = re.sub(r'[^\x00-\x7F]+', ' ', text)
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?-]', '', text)
        
        # Remove phone numbers (10+ digits)
        text = re.sub(r'\b\d{10,}\b', '', text)
        
        # Remove actual dates like "Oct, 2024" or "Jan 2025"
        text = re.sub(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[,\s]+\d{4}', '', text, flags=re.IGNORECASE)
        
        # Remove time/date patterns
        if remove_dates:
            text = re.sub(r'\d+\s*(month|months|week|weeks|day|days|year|years|hour|hours)\s*ago', '', text, flags=re.IGNORECASE)
        
        # AGGRESSIVE NAME REMOVAL - Multiple passes for all name patterns
        
        # 1. Remove "FirstName LastName , City/District" patterns
        text = re.sub(r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}\s*,\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:District|Division|City))?', '', text)
        
        # 2. Remove "FirstName LastName" anywhere (2-3 capitalized words in sequence)
        text = re.sub(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b', '', text)
        
        # 3. Remove single capitalized names at end of sentences
        text = re.sub(r'\b[A-Z][A-Z]+(?:\s+[A-Z]+)*\b', '', text)  # ALL CAPS names
        
        # 4. Remove ", City" patterns at the end
        text = re.sub(r',\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:District|Division|City))?\s*$', '', text)
        
        # 5. Remove common prefixes
        text = re.sub(r'\b(by|reviewed by|posted by|from)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*', '', text, flags=re.IGNORECASE)
        
        # 6. Remove "Flipkart Customer" and similar
        text = re.sub(r'Flipkart\s+Customer', '', text, flags=re.IGNORECASE)
        
        # Clean up artifacts
        text = re.sub(r'\s*,\s*,\s*', ', ', text)  # Double commas
        text = re.sub(r',\s*$', '', text)  # Trailing commas
        text = re.sub(r'^\s*,', '', text)  # Leading commas
        text = re.sub(r'\s+', ' ', text)  # Multiple spaces
        
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
                
                # Load existing reviews to prevent duplicates
                existing_review_keys = self._get_existing_review_keys()
                
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
                                            'Storage', 'ratings and', 'reviews', 'Flipkart Customer',
                                            'by', 'reviewed', 'writes', 'says', 'posted', 'ago',
                                            'month', 'months', 'week', 'weeks', 'day', 'days', 'year', 'years']
                            
                            for i, line in enumerate(lines[1:], 1):
                                has_noise = any(kw in line for kw in noise_keywords)
                                # Skip lines with time patterns (e.g., "3 months ago")
                                has_time_pattern = re.search(r'\d+\s*(month|week|day|year|hour)s?\s*ago', line, re.IGNORECASE)
                                
                                if not has_noise and not has_time_pattern and len(line) > 5:
                                    if i == 1 or (not title_candidates and len(line) < 100):
                                        title_candidates.append(line)
                                    else:
                                        review_candidates.append(line)
                            
                            if title_candidates and review_candidates:
                                # Join all review content for extraction
                                full_text = ' '.join(lines)
                                review_content = ' '.join(review_candidates)
                                
                                # Extract city and date BEFORE cleaning (from full text)
                                city = self._extract_city(full_text)
                                review_date = self._extract_and_format_date(full_text)
                                
                                # Clean text (now remove dates and cities after extraction)
                                title = self.clean_text(title_candidates[0], remove_dates=True)
                                review_text = self.clean_text(review_content, remove_dates=True)
                                
                                # Check for personal names or identifiers in text
                                name_indicators = ['flipkart customer', 'certified buyer', 'by ', 'reviewed by']
                                has_name_indicator = any(indicator in title.lower() or indicator in review_text.lower() 
                                                        for indicator in name_indicators)
                                
                                # Check if title is a person name (2+ capitalized words)
                                is_person_name_title = bool(re.match(r'^[A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?$', title))
                                
                                # Validate - reject if contains name indicators or title is a name
                                if (3 < len(title) < 150 and
                                    15 < len(review_text) < 1000 and
                                    not title.replace(' ', '').replace(',', '').isdigit() and
                                    not has_name_indicator and
                                    not is_person_name_title):
                                    
                                    review_key = f"{rating}_{title[:30]}_{review_text[:30]}"
                                    if review_key not in seen_reviews and review_key not in existing_review_keys:
                                        seen_reviews.add(review_key)
                                        page_reviews.append({
                                            'rating': int(rating),
                                            'title': title,
                                            'review_text': review_text,
                                            'date': review_date if review_date else 'N/A',
                                            'city': city if city else 'N/A'
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
            delay = random.uniform(10, 15)  # Increased from 5-10 to 10-15 seconds
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
                existing_df = pd.DataFrame(columns=['rating', 'title', 'review_text', 'date', 'city'])
            
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
    url = "https://www.flipkart.com/apple-iphone-16-black-128-gb/product-reviews/itmb07d67f995271?pid=MOBH4DQFG8NKFRDY&lid=LSTMOBH4DQFG8NKFRDYKOOGZ6&marketplace=FLIPKART"
    
    print("="*60)
    print("SIMPLE FLIPKART REVIEW SCRAPER")
    print("="*60)
    print("Product: Apple iPhone 16 (Black, 128 GB)\n")
    
    scraper = SimpleFlipkartScraper()
    scraper.log_progress("="*60)
    
    # Check for resume point
    last_page = scraper._get_last_successful_page()
    resume_page = scraper._calculate_resume_page(last_page)
    
    if last_page > 0:
        scraper.log_progress(f"Resuming scrape - Last successful page: {last_page}, Starting from: {resume_page}")
        print(f"\nResuming from page {resume_page} (Last successful: {last_page})\n")
    else:
        scraper.log_progress("Starting fresh scrape - iPhone 16 reviews")
        print("\nStarting fresh scrape...\n")
    
    try:
        # Set to 10000 to scrape all pages dynamically (will stop when 5 consecutive empty pages found)
        total_count = scraper.scrape_reviews(url, max_pages=10000, start_page=resume_page, reverse=False)
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
