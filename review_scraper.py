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


class FlipkartReviewScraper:
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        ]
        self.reviews = []
        self.session = requests.Session()
    
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
        """
        Scrape all reviews from all pages
        
        Args:
            base_url: Base URL of the product reviews page
            total_pages: Total number of pages to scrape (default 947)
            start_page: Starting page number (default 1)
        """
        print(f"Starting to scrape {total_pages} pages of reviews...")
        print("This may take a while. Please be patient.\n")
        
        consecutive_empty_pages = 0
        max_empty_pages = 7
        
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
                
                print(f"Scraping page {page_num}/{total_pages}...", end=' ')
                
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
                    print(f"✓ Found {len(page_reviews)} reviews (Total: {len(self.reviews)})")
                    consecutive_empty_pages = 0  # Reset counter
                else:
                    print("⚠ No reviews found on this page")
                    consecutive_empty_pages += 1
                    
                    # Stop if 7 consecutive empty pages
                    if consecutive_empty_pages >= max_empty_pages:
                        print(f"\n⚠ Stopped: {max_empty_pages} consecutive pages with no reviews found")
                        print("This likely means we've reached the end or are being blocked.\n")
                        break
                
                # Save progress every 5 pages to same file
                if page_num % 5 == 0:
                    self.save_to_csv('reviews_in_progress.csv')
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
                    response = self.session.get(url, headers=self.headers, timeout=15)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.content, 'html.parser')
                    page_reviews = self.parse_review_page(soup)
                    if page_reviews:
                        self.reviews.extend(page_reviews)
                        print(f"✓ Retry successful! Found {len(page_reviews)} reviews (Total: {len(self.reviews)})")
                    time.sleep(5)
                except:
                    print(f"Retry failed. Skipping page {page_num}")
                continue
            
            except Exception as e:
                print(f"✗ Unexpected error on page {page_num}: {e}")
                continue
        
        print(f"\n{'='*60}")
        print(f"Scraping completed!")
        print(f"Total reviews collected: {len(self.reviews)}")
        print(f"{'='*60}\n")
        
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
    print("FLIPKART REVIEW SCRAPER")
    print("="*60)
    print(f"Product: Apple iPhone 15 (Black, 128 GB)")
    print(f"Starting from page 91")
    print("="*60)
    print()
    
    # Create scraper instance
    scraper = FlipkartReviewScraper()
    
    # Scrape from page 91 onwards
    scraper.scrape_all_reviews(url, total_pages=947, start_page=91)
    
    # Save to CSV
    df = scraper.save_to_csv('iphone15_reviews.csv')
    
    # Show statistics
    scraper.get_statistics()
    
    print("\n✓ Scraping complete! Ready for sentiment analysis.")
    print(f"✓ Data saved to: iphone15_reviews.csv")


if __name__ == "__main__":
    main()
