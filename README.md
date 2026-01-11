# Mobile Demand Prediction - Data Scraping Module

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Scraper
```bash
python scrape_mobiles.py
```

## Usage Options

### Option 1: Scrape Specific Products
1. Run the script
2. Choose option `1`
3. Paste Flipkart product URLs (one per line)
4. Press Enter twice to start scraping

### Option 2: Scrape from Category Page
1. Run the script
2. Choose option `2`
3. Paste category page URL (e.g., https://www.flipkart.com/mobiles/pr?sid=tyy,4io)
4. Specify number of products to scrape
5. Script will automatically extract and scrape products

## Data Collected

The scraper collects the following attributes:
- **Basic Info**: Product name, brand, URL
- **Pricing**: Current price, original price, discount percentage
- **Ratings**: Rating, total reviews, total ratings
- **Specifications**: RAM, storage, battery, camera, processor, screen size, 5G support
- **Availability**: Stock status, delivery days, offers count
- **Trends**: Trending/bestseller tags
- **Timestamp**: Date of scraping

## Output

Data is saved to `mobile_data.csv` in the same directory.

## Tips for Best Results

1. **Rate Limiting**: Script includes 2-second delays between requests to avoid blocking
2. **Multiple Runs**: Run the script daily/weekly to collect time-series data
3. **Verify URLs**: Make sure URLs are valid Flipkart product pages
4. **Check CSV**: After scraping, verify data quality in the CSV file

## Next Steps

1. Collect data over 2-4 weeks for temporal patterns
2. Clean and preprocess the data
3. Engineer features for demand prediction
4. Train ML models (LSTM, Prophet, or XGBoost)

## Important Notes

⚠️ **Legal Compliance**: 
- Respect Flipkart's robots.txt
- Use for educational purposes only
- Don't overload their servers with requests
- Consider using Flipkart's API if available for commercial use
