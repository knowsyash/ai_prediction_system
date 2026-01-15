"""
Advanced Flipkart Review Scraper with Anti-Bot Protection
Uses Selenium for browser automation to bypass Flipkart's protection
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import pandas as pd
import time
import random


class AdvancedReviewScraper:
    def __init__(self):
        self.reviews = []
        self.setup_driver()
    
    def setup_driver(self):
        """Setup Chrome driver with options to avoid detection"""
        chrome_options = Options()
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Uncomment to run headless (without browser window)
        # chrome_options.add_argument('--headless=new')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 10)
    
    def random_delay(self, min_sec=2, max_sec=5):
        """Add random delay to mimic human behavior"""
        time.sleep(random.uniform(min_sec, max_sec))
    
    def extract_reviews_from_page(self):
        """Extract all reviews from current page"""
        page_reviews = []
        
        try:
            # Wait for reviews to load
            self.wait.until(EC.presence_of_element_all_located((By.CLASS_NAME, "_27M-vq")))
            
            # Find all review containers
            review_elements = self.driver.find_elements(By.CSS_SELECTOR, "div._1AtVbE.col-12-12")
            
            for review_elem in review_elements:
                try:
                    review_data = {}
                    
                    # Rating
                    try:
                        rating = review_elem.find_element(By.CSS_SELECTOR, "div._3LWZlK").text
                        review_data['rating'] = int(rating[0]) if rating and rating[0].isdigit() else None
                    except:
                        review_data['rating'] = None
                    
                    # Title
                    try:
                        title = review_elem.find_element(By.CSS_SELECTOR, "p._2-N8zT").text
                        review_data['title'] = title
                    except:
                        review_data['title'] = ''
                    
                    # Review text
                    try:
                        text = review_elem.find_element(By.CSS_SELECTOR, "div.t-ZTKy").text
                        review_data['review_text'] = text
                    except:
                        review_data['review_text'] = ''
                    
                    # Reviewer name
                    try:
                        name = review_elem.find_element(By.CSS_SELECTOR, "p._2sc7ZR._2V5EHH").text
                        review_data['reviewer_name'] = name
                    except:
                        review_data['reviewer_name'] = 'Anonymous'
                    
                    # Location and certified buyer
                    try:
                        location_elem = review_elem.find_element(By.CSS_SELECTOR, "p._2mcZGG")
                        location_text = location_elem.text
                        review_data['location'] = location_text
                        review_data['certified_buyer'] = 'Certified Buyer' in location_text
                    except:
                        review_data['location'] = ''
                        review_data['certified_buyer'] = False
                    
                    # Date
                    try:
                        date_elements = review_elem.find_elements(By.CSS_SELECTOR, "p._2sc7ZR")
                        if len(date_elements) > 1:
                            review_data['review_date'] = date_elements[-1].text
                        else:
                            review_data['review_date'] = ''
                    except:
                        review_data['review_date'] = ''
                    
                    # Likes
                    try:
                        likes = review_elem.find_element(By.CSS_SELECTOR, "div._1_BQL8").text
                        import re
                        match = re.search(r'\d+', likes)
                        review_data['likes'] = int(match.group()) if match else 0
                    except:
                        review_data['likes'] = 0
                    
                    if review_data.get('review_text') or review_data.get('title'):
                        page_reviews.append(review_data)
                
                except Exception as e:
                    continue
        
        except Exception as e:
            print(f"Error extracting reviews: {e}")
        
        return page_reviews
    
    def click_next_page(self):
        """Click the next page button"""
        try:
            # Find and click next button
            next_buttons = self.driver.find_elements(By.XPATH, "//a[@class='_1LKTO3' and text()='Next']")
            if next_buttons:
                # Scroll to button
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", next_buttons[0])
                time.sleep(1)
                next_buttons[0].click()
                self.random_delay(3, 5)
                return True
            return False
        except:
            return False
    
    def scrape_all_reviews(self, url, max_pages=947):
        """Scrape all reviews with browser automation"""
        print("="*60)
        print("ADVANCED FLIPKART REVIEW SCRAPER")
        print("="*60)
        print("Using Selenium browser automation to bypass restrictions")
        print("="*60)
        print()
        
        try:
            # Load first page
            print("Loading review page...")
            self.driver.get(url)
            self.random_delay(5, 7)  # Wait for page to load
            
            page_num = 1
            
            while page_num <= max_pages:
                print(f"Scraping page {page_num}/{max_pages}...", end=' ')
                
                # Extract reviews from current page
                page_reviews = self.extract_reviews_from_page()
                
                if page_reviews:
                    self.reviews.extend(page_reviews)
                    print(f"✓ Found {len(page_reviews)} reviews (Total: {len(self.reviews)})")
                else:
                    print("⚠ No reviews found")
                
                # Save backup every 5 pages
                if page_num % 5 == 0:
                    self.save_to_csv(f'reviews_backup_page_{page_num}.csv')
                    print(f"\n📊 Backup saved: {len(self.reviews)} reviews\n")
                
                # Try to go to next page
                if page_num < max_pages:
                    if not self.click_next_page():
                        print("\nNo more pages available or reached end")
                        break
                
                page_num += 1
                
        except KeyboardInterrupt:
            print("\n\n⚠ Interrupted by user. Saving progress...")
        except Exception as e:
            print(f"\n\nError: {e}")
        finally:
            self.cleanup()
        
        print(f"\n{'='*60}")
        print(f"Scraping completed!")
        print(f"Total reviews collected: {len(self.reviews)}")
        print(f"{'='*60}\n")
    
    def save_to_csv(self, filename='iphone15_reviews.csv'):
        """Save reviews to CSV"""
        if self.reviews:
            df = pd.DataFrame(self.reviews)
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            print(f"✓ Saved to {filename}")
            return df
        return None
    
    def cleanup(self):
        """Close browser"""
        if hasattr(self, 'driver'):
            self.driver.quit()


def main():
    url = "https://www.flipkart.com/apple-iphone-15-black-128-gb/product-reviews/itm6ac6485515ae4?pid=MOBGTAGPTB3VS24W&lid=LSTMOBGTAGPTB3VS24WKFODHL&marketplace=FLIPKART"
    
    scraper = AdvancedReviewScraper()
    scraper.scrape_all_reviews(url, max_pages=947)
    scraper.save_to_csv('iphone15_reviews_final.csv')
    
    print("\n✓ Complete! Check iphone15_reviews_final.csv")


if __name__ == "__main__":
    main()
