"""
Flipkart Review Scraper
Scrapes all product reviews from Flipkart for sentiment analysis
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime
import re
import random
import os


class FlipkartReviewScraper:
    def __init__(self, csv_filename='data_scrapping/iphone15_reviews.csv', progress_file='data_scrapping/scraper_progress.txt'):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        ]
        self.reviews = []
        self.session = requests.Session()
        self.csv_filename = csv_filename
        self.progress_file = progress_file
        self.total_scraped = 0
    
    def get_headers(self):
        """Get random headers to avoid detection"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }
    
    def get_current_progress(self):
        """Check CSV file and return current row count and start page"""
        if os.path.exists(self.csv_filename):
            try:
                df = pd.read_csv(self.csv_filename)
                row_count = len(df)
                # Flipkart typically shows 8-10 reviews per page, be conservative
                # Go back 10 pages to ensure we don't miss any reviews
                start_page = max(1, (row_count // 10) - 10)
                return row_count, start_page
            except Exception as e:
                print(f"Warning: Could not read existing CSV: {e}")
                return 0, 1
        return 0, 1
    
    def save_progress(self, current_page, total_reviews, status='Running'):
        """Save current progress to txt file"""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            progress_info = f"""
{'='*60}
SCRAPER PROGRESS REPORT
{'='*60}
Status: {status}
Last Updated: {timestamp}
Current Page: {current_page}
Total Reviews Scraped: {total_reviews}
CSV File: {self.csv_filename}
{'='*60}
"""
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                f.write(progress_info)
            print(f"✓ Progress saved to {self.progress_file}")
        except Exception as e:
            print(f"Warning: Could not save progress: {e}")
    
    def parse_review_page(self, soup):
        """Parse reviews from a single page"""
        page_reviews = []
        
        # Find all review containers - updated selector based on actual HTML
        review_containers = soup.find_all('div', class_=re.compile(r'lvJbLV|col-12-12'))
        
        if not review_containers:
            # Try alternative selectors
            review_containers = soup.find_all('div', class_=re.compile(r'col.*_390CkK|cPHDOP'))
        
        if not review_containers:
            review_containers = soup.find_all('div', class_=re.compile(r'_1AtVbE|col-12-12'))
        
        for review in review_containers:
            try:
                review_data = {}
                
                # Extract rating - Flipkart uses dynamic classes, so search by content
                # Look for a div with single digit 1-5 (star rating)
                rating_div = None
                all_divs = review.find_all('div', recursive=True)
                for div in all_divs:
                    text = div.get_text(strip=True)
                    # Check if it's a single digit between 1-5 or digit with star
                    if text and (text in ['1', '2', '3', '4', '5'] or (len(text) <= 3 and text[0].isdigit() and '★' in text)):
                        rating_div = div
                        break
                
                if rating_div:
                    rating_text = rating_div.get_text(strip=True)
                    try:
                        # Extract only the number part
                        rating_num = re.search(r'[1-5]', rating_text)
                        review_data['rating'] = int(rating_num.group()) if rating_num else None
                    except:
                        review_data['rating'] = None
                else:
                    review_data['rating'] = None
                
                # Extract review title
                title = review.find('p', class_=re.compile(r'_2-N8zT|z9E0IG|qW2QI1'))
                review_data['title'] = title.get_text(strip=True) if title else ''
                
                # Extract review text
                review_text_div = review.find('div', class_=re.compile(r't-ZTKy|qwjRop'))
                if not review_text_div:
                    review_text_div = review.find('div', {'class': ''})
                
                review_data['review_text'] = review_text_div.get_text(strip=True) if review_text_div else ''
                
                # Extract reviewer name
                reviewer = review.find('p', class_=re.compile(r'_2sc7ZR|_2NsDsF'))
                review_data['reviewer_name'] = reviewer.get_text(strip=True) if reviewer else 'Anonymous'
                
                # Extract location and certified buyer info
                location_div = review.find('p', class_=re.compile(r'_2mcZGG|MztJPv'))
                if location_div:
                    location_text = location_div.get_text(strip=True)
                    review_data['location'] = location_text
                    review_data['certified_buyer'] = 'Certified Buyer' in location_text
                else:
                    review_data['location'] = ''
                    review_data['certified_buyer'] = False
                
                # Extract date
                date_span = review.find('p', class_=re.compile(r'_2sc7ZR'))
                date_text = date_span.get_text(strip=True) if date_span else ''
                review_data['review_date'] = date_text
                
                # Extract likes and dislikes
                thumbs_up = review.find('div', class_=re.compile(r'_1_BQL8|_2ZibVB'))
                if thumbs_up:
                    likes_text = thumbs_up.get_text(strip=True)
                    review_data['likes'] = int(re.search(r'\d+', likes_text).group()) if re.search(r'\d+', likes_text) else 0
                else:
                    review_data['likes'] = 0
                
                thumbs_down = review.find('div', class_=re.compile(r'_1_BQL8|_2ZibVB'))
                if thumbs_down:
                    dislikes_text = thumbs_down.get_text(strip=True)
                    review_data['dislikes'] = int(re.search(r'\d+', dislikes_text).group()) if re.search(r'\d+', dislikes_text) else 0
                else:
                    review_data['dislikes'] = 0
                
                # Only add if we have actual review text
                if review_data.get('review_text') or review_data.get('title'):
                    page_reviews.append(review_data)
                    
            except Exception as e:
                print(f"Error parsing individual review: {e}")
                continue
        
        return page_reviews
    
    def scrape_all_reviews(self, base_url, total_pages=947, start_page=1):
        """Scrape reviews from multiple pages with auto-resume"""
        # Check current progress first
        existing_rows, calculated_start = self.get_current_progress()
        if existing_rows > 0:
            print(f"\n✓ Found existing data: {existing_rows} reviews")
            print(f"✓ Calculated start page (with 10-page buffer): {calculated_start}")
            # Use the higher of provided start_page or calculated
            start_page = max(start_page, calculated_start)
        
        print(f"\nStarting scrape from page {start_page} to {total_pages}...")
        print(f"Target: ~{(total_pages - start_page + 1) * 10} reviews\n")
        print(f"Note: Going back 10 pages from calculated position to ensure no reviews are missed\n")
        
        # Save initial progress
        self.save_progress(start_page, existing_rows, 'Started')
        self.total_scraped = existing_rows  # Initialize with existing count
        
        consecutive_empty_pages = 0
        max_empty_pages = 20  # Increased to 20 to handle gaps
        
        for page_num in range(start_page, total_pages + 1):
            try:
                # Construct page URL
                if page_num == 1:
                    url = base_url
                else:
                    # Add page parameter to URL
                    if '?' in base_url:
                        url = f"{base_url}&page={page_num}"
                    else:
                        url = f"{base_url}?page={page_num}"
                
                print(f"[Page {page_num}/{total_pages}] Fetching reviews...", end=' ')
                
                # Random delay between 4-7 seconds to avoid detection
                time.sleep(random.uniform(4, 7))
                
                # Make request with rotating headers
                response = self.session.get(url, headers=self.get_headers(), timeout=15)
                response.raise_for_status()
                
                # Parse HTML
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract reviews from this page
                page_reviews = self.parse_review_page(soup)
                
                if page_reviews:
                    self.reviews.extend(page_reviews)
                    self.total_scraped += len(page_reviews)  # Add to running total
                    print(f"✓ Found {len(page_reviews)} reviews (Session: {len(self.reviews)}, Total: {self.total_scraped})")
                    consecutive_empty_pages = 0
                    
                    # Save progress every 10 pages
                    if page_num % 10 == 0:
                        self.save_progress(page_num, self.total_scraped, 'Running')
                        # Auto-save to CSV every 10 pages
                        self.save_to_csv(self.csv_filename)
                        print(f"\n📊 Progress checkpoint saved - Page {page_num}\n")
                    # Update progress every 5 pages (without full save)
                    elif page_num % 5 == 0:
                        self.save_progress(page_num, self.total_scraped, 'Running')
                else:
                    print("⚠ No reviews found on this page")
                    consecutive_empty_pages += 1
                    
                    # Stop if 7 consecutive empty pages
                    if consecutive_empty_pages >= max_empty_pages:
                        print(f"\n⚠ Stopped: {max_empty_pages} consecutive pages with no reviews")
                        self.save_progress(page_num, self.total_scraped, 'Stopped - No more reviews')
                        break
                
                # Save progress every 5 pages to same file
                if page_num % 5 == 0:
                    self.save_to_csv('data_scrapping/reviews_in_progress.csv')
                    self.reviews = []  # Clear to avoid duplicates
                    print(f"\n📊 Progress saved\n")
                
                # Be respectful - add delay between requests
                time.sleep(3)  # 3 second delay between pages
                
            except requests.exceptions.RequestException as e:
                print(f"✗ Error: {e}")
                if '429' in str(e):
                    wait_time = 30
                    print(f"Rate limited! Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                else:
                    print(f"Retrying page {page_num} in 10 seconds...")
                    time.sleep(10)
                # Try again
                try:
                    response = self.session.get(url, headers=self.get_headers(), timeout=15)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.content, 'html.parser')
                    page_reviews = self.parse_review_page(soup)
                    if page_reviews:
                        self.reviews.extend(page_reviews)
                        self.total_scraped = existing_rows + len(self.reviews)
                        print(f"✓ Retry successful! Found {len(page_reviews)} reviews (Session: {len(self.reviews)}, Total: {self.total_scraped})")
                    time.sleep(5)
                except:
                    print(f"Retry failed. Skipping page {page_num}")
                continue
            
            except Exception as e:
                print(f"✗ Unexpected error on page {page_num}: {e}")
                continue
        
        print(f"\n{'='*60}")
        print(f"Scraping completed!")
        print(f"Session reviews: {len(self.reviews)}")
        print(f"Total reviews in CSV: {self.total_scraped}")
        print(f"{'='*60}\n")
        
        # Save final progress
        self.save_progress(total_pages, self.total_scraped, 'Completed')
        
        return self.reviews
    
    def save_to_csv(self, filename='flipkart_reviews.csv'):
        """Save reviews to CSV file (append mode)"""
        if self.reviews:
            df = pd.DataFrame(self.reviews)
            
            # Keep only rating, title, and review_text columns (if they exist)
            available_cols = [col for col in ['rating', 'title', 'review_text'] if col in df.columns]
            if available_cols:
                df = df[available_cols]
            
            # Check if file exists
            import os
            file_exists = os.path.isfile(filename)
            
            # Append to file if it exists, otherwise create new
            mode = 'a' if file_exists else 'w'
            header = not file_exists  # Write header only if file doesn't exist
            
            df.to_csv(filename, mode=mode, header=header, index=False, encoding='utf-8-sig')
            print(f"✓ Reviews saved to {filename}")
            return df
        else:
            print("No reviews to save!")
            return None
    

    def get_statistics(self):
        """Get basic statistics about collected reviews"""
        if not self.reviews:
            print("No reviews collected yet!")
            return None
        
        df = pd.DataFrame(self.reviews)
        
        print(f"\n{'='*60}")
        print("REVIEW STATISTICS")
        print(f"{'='*60}")
        print(f"Total Reviews: {len(df)}")
        print(f"\nRating Distribution:")
        if 'rating' in df.columns:
            print(df['rating'].value_counts().sort_index())
        
        if 'certified_buyer' in df.columns:
            certified = df['certified_buyer'].sum()
            print(f"\nCertified Buyers: {certified} ({certified/len(df)*100:.1f}%)")
        
        print(f"{'='*60}\n")
        
        return df


def main():
    # Product URL from user
    url = "https://www.flipkart.com/apple-iphone-15-black-128-gb/product-reviews/itm6ac6485515ae4?pid=MOBGTAGPTB3VS24W&lid=LSTMOBGTAGPTB3VS24WKFODHL&marketplace=FLIPKART"
    
    print("="*60)
    print("FLIPKART REVIEW SCRAPER - AUTO RESUME")
    print("="*60)
    print(f"Product: Apple iPhone 15 (Black, 128 GB)")
    print("="*60)
    print()
    
    # Create scraper instance with auto-resume capability
    scraper = FlipkartReviewScraper(
        csv_filename='data_scrapping/reviews_in_progress.csv',
        progress_file='data_scrapping/scraper_progress.txt'
    )
    
    # Check existing progress
    existing_rows, auto_start_page = scraper.get_current_progress()
    print(f"✓ Auto-detected: {existing_rows} existing reviews")
    print(f"✓ Will start from page: {auto_start_page}")
    print()
    
    try:
        # Scrape with auto-resume (will automatically continue from where it left off)
        scraper.scrape_all_reviews(url, total_pages=947, start_page=auto_start_page)
        
        # Save to CSV
        df = scraper.save_to_csv('data_scrapping/reviews_in_progress.csv')
        
        # Show statistics
        scraper.get_statistics()
        
        print("\n✓ Scraping complete! Ready for sentiment analysis.")
        print(f"✓ Data saved to: data_scrapping/reviews_in_progress.csv")
        print(f"✓ Progress log: data_scrapping/scraper_progress.txt")
        
    except KeyboardInterrupt:
        print("\n\n⚠ Scraping interrupted by user!")
        print("Saving progress...")
        scraper.save_to_csv('data_scrapping/reviews_in_progress.csv')
        scraper.save_progress(0, scraper.total_scraped, 'Interrupted')
        print("✓ Progress saved. Run again to resume from where you left off.")
    except Exception as e:
        print(f"\n\n✗ Error occurred: {e}")
        print("Saving progress...")
        scraper.save_to_csv('data_scrapping/reviews_in_progress.csv')
        scraper.save_progress(0, scraper.total_scraped, 'Error')
        print("✓ Progress saved. Run again to resume.")


if __name__ == "__main__":
    main()
