# Mobile Price Scraper

Simple web scraper for collecting mobile phone data from Flipkart.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

Run the main script:
```bash
python main.py
```

Choose option:
- **1**: Scrape products (saves to `mobile_data.csv`)
- **2**: View saved data

## Features

- Scrapes product name, price, ratings
- Extracts specs: RAM, storage, battery, camera
- Saves data to CSV for analysis
- Clean, readable code

## Data Collected

- Brand, name, price, discount
- Rating and total ratings
- RAM, storage, battery
- Camera, processor, 5G support

## Customization

Edit `PRODUCT_URLS` in `main.py` to scrape different products.

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
