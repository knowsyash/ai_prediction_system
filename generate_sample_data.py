import pandas as pd
from datetime import datetime
import random

# Create sample mobile data for demonstration
# In production, this would come from actual scraping

sample_data = [
    {
        'date_scraped': '2026-01-11',
        'brand': 'Apple',
        'product_name': 'Apple iPhone 15 (Black, 128 GB)',
        'price': 69990,
        'original_price': 79900,
        'discount_percent': 12.4,
        'rating': 4.6,
        'total_reviews': 15234,
        'total_ratings': 28450,
        'ram': '6 GB',
        'storage': '128 GB',
        'battery': '3877 mAh',
        'camera_primary': '48 MP + 12 MP',
        'processor': 'A16 Bionic Chip',
        'screen_size': '6.1 inch',
        '5g_support': 'Yes',
        'availability': 'In Stock',
        'delivery_days': 2,
        'offers_count': 8,
        'trending_tag': 'Yes',
        'product_url': 'https://www.flipkart.com/apple-iphone-15-black-128-gb'
    },
    {
        'date_scraped': '2026-01-11',
        'brand': 'Samsung',
        'product_name': 'Samsung Galaxy S24 5G (Cobalt Violet, 256 GB)',
        'price': 74999,
        'original_price': 99999,
        'discount_percent': 25.0,
        'rating': 4.5,
        'total_reviews': 8765,
        'total_ratings': 16890,
        'ram': '8 GB',
        'storage': '256 GB',
        'battery': '4000 mAh',
        'camera_primary': '50 MP + 12 MP + 10 MP',
        'processor': 'Exynos 2400',
        'screen_size': '6.2 inch',
        '5g_support': 'Yes',
        'availability': 'In Stock',
        'delivery_days': 3,
        'offers_count': 12,
        'trending_tag': 'Yes',
        'product_url': 'https://www.flipkart.com/samsung-galaxy-s24-5g-cobalt-violet-256-gb'
    },
    {
        'date_scraped': '2026-01-11',
        'brand': 'OnePlus',
        'product_name': 'OnePlus 12 (Silky Black, 256 GB)',
        'price': 64999,
        'original_price': 69999,
        'discount_percent': 7.14,
        'rating': 4.4,
        'total_reviews': 5432,
        'total_ratings': 12340,
        'ram': '12 GB',
        'storage': '256 GB',
        'battery': '5400 mAh',
        'camera_primary': '50 MP + 64 MP + 48 MP',
        'processor': 'Snapdragon 8 Gen 3',
        'screen_size': '6.82 inch',
        '5g_support': 'Yes',
        'availability': 'In Stock',
        'delivery_days': 2,
        'offers_count': 6,
        'trending_tag': 'Yes',
        'product_url': 'https://www.flipkart.com/oneplus-12-silky-black-256-gb'
    },
    {
        'date_scraped': '2026-01-11',
        'brand': 'Xiaomi',
        'product_name': 'Xiaomi 14 (Black, 512 GB)',
        'price': 54999,
        'original_price': 59999,
        'discount_percent': 8.33,
        'rating': 4.3,
        'total_reviews': 3210,
        'total_ratings': 7650,
        'ram': '12 GB',
        'storage': '512 GB',
        'battery': '4610 mAh',
        'camera_primary': '50 MP + 50 MP + 50 MP',
        'processor': 'Snapdragon 8 Gen 3',
        'screen_size': '6.36 inch',
        '5g_support': 'Yes',
        'availability': 'In Stock',
        'delivery_days': 4,
        'offers_count': 5,
        'trending_tag': 'No',
        'product_url': 'https://www.flipkart.com/xiaomi-14-black-512-gb'
    },
    {
        'date_scraped': '2026-01-11',
        'brand': 'Realme',
        'product_name': 'Realme GT 5 240W (Racing Yellow, 512 GB)',
        'price': 42999,
        'original_price': 49999,
        'discount_percent': 14.0,
        'rating': 4.2,
        'total_reviews': 2156,
        'total_ratings': 5432,
        'ram': '16 GB',
        'storage': '512 GB',
        'battery': '5240 mAh',
        'camera_primary': '50 MP + 8 MP',
        'processor': 'Snapdragon 8 Gen 2',
        'screen_size': '6.74 inch',
        '5g_support': 'Yes',
        'availability': 'In Stock',
        'delivery_days': 3,
        'offers_count': 4,
        'trending_tag': 'No',
        'product_url': 'https://www.flipkart.com/realme-gt-5-240w-racing-yellow-512-gb'
    },
    {
        'date_scraped': '2026-01-11',
        'brand': 'Vivo',
        'product_name': 'Vivo X100 Pro (Asteroid Black, 256 GB)',
        'price': 89999,
        'original_price': 94999,
        'discount_percent': 5.26,
        'rating': 4.5,
        'total_reviews': 1876,
        'total_ratings': 4321,
        'ram': '16 GB',
        'storage': '256 GB',
        'battery': '5400 mAh',
        'camera_primary': '50 MP + 50 MP + 50 MP',
        'processor': 'MediaTek Dimensity 9300',
        'screen_size': '6.78 inch',
        '5g_support': 'Yes',
        'availability': 'In Stock',
        'delivery_days': 2,
        'offers_count': 7,
        'trending_tag': 'Yes',
        'product_url': 'https://www.flipkart.com/vivo-x100-pro-asteroid-black-256-gb'
    },
    {
        'date_scraped': '2026-01-11',
        'brand': 'Google',
        'product_name': 'Google Pixel 8 Pro (Obsidian, 256 GB)',
        'price': 84999,
        'original_price': 106999,
        'discount_percent': 20.56,
        'rating': 4.4,
        'total_reviews': 3456,
        'total_ratings': 7890,
        'ram': '12 GB',
        'storage': '256 GB',
        'battery': '5050 mAh',
        'camera_primary': '50 MP + 48 MP + 48 MP',
        'processor': 'Google Tensor G3',
        'screen_size': '6.7 inch',
        '5g_support': 'Yes',
        'availability': 'In Stock',
        'delivery_days': 3,
        'offers_count': 9,
        'trending_tag': 'Yes',
        'product_url': 'https://www.flipkart.com/google-pixel-8-pro-obsidian-256-gb'
    },
    {
        'date_scraped': '2026-01-11',
        'brand': 'Motorola',
        'product_name': 'Motorola Edge 50 Ultra (Forest Grey, 512 GB)',
        'price': 59999,
        'original_price': 69999,
        'discount_percent': 14.29,
        'rating': 4.1,
        'total_reviews': 1234,
        'total_ratings': 3210,
        'ram': '12 GB',
        'storage': '512 GB',
        'battery': '4500 mAh',
        'camera_primary': '50 MP + 50 MP + 64 MP',
        'processor': 'Snapdragon 8s Gen 3',
        'screen_size': '6.7 inch',
        '5g_support': 'Yes',
        'availability': 'In Stock',
        'delivery_days': 4,
        'offers_count': 5,
        'trending_tag': 'No',
        'product_url': 'https://www.flipkart.com/motorola-edge-50-ultra-forest-grey-512-gb'
    },
    {
        'date_scraped': '2026-01-11',
        'brand': 'OPPO',
        'product_name': 'OPPO Find X7 Ultra (Ocean Blue, 256 GB)',
        'price': 72999,
        'original_price': 79999,
        'discount_percent': 8.75,
        'rating': 4.3,
        'total_reviews': 1987,
        'total_ratings': 4567,
        'ram': '12 GB',
        'storage': '256 GB',
        'battery': '5000 mAh',
        'camera_primary': '50 MP + 50 MP + 50 MP',
        'processor': 'Snapdragon 8 Gen 3',
        'screen_size': '6.82 inch',
        '5g_support': 'Yes',
        'availability': 'In Stock',
        'delivery_days': 3,
        'offers_count': 6,
        'trending_tag': 'No',
        'product_url': 'https://www.flipkart.com/oppo-find-x7-ultra-ocean-blue-256-gb'
    },
    {
        'date_scraped': '2026-01-11',
        'brand': 'Nothing',
        'product_name': 'Nothing Phone (2a) (Black, 256 GB)',
        'price': 27999,
        'original_price': 29999,
        'discount_percent': 6.67,
        'rating': 4.3,
        'total_reviews': 4321,
        'total_ratings': 9876,
        'ram': '12 GB',
        'storage': '256 GB',
        'battery': '5000 mAh',
        'camera_primary': '50 MP + 50 MP',
        'processor': 'MediaTek Dimensity 7200 Pro',
        'screen_size': '6.7 inch',
        '5g_support': 'Yes',
        'availability': 'In Stock',
        'delivery_days': 2,
        'offers_count': 4,
        'trending_tag': 'Yes',
        'product_url': 'https://www.flipkart.com/nothing-phone-2a-black-256-gb'
    }
]

# Create DataFrame
df = pd.DataFrame(sample_data)

# Save to CSV
df.to_csv('mobile_data.csv', index=False, encoding='utf-8-sig')

print("=" * 60)
print("SAMPLE DATA GENERATED SUCCESSFULLY")
print("=" * 60)
print(f"\nTotal products: {len(df)}")
print(f"\nBrands: {', '.join(df['brand'].unique())}")
print(f"\nPrice range: ₹{df['price'].min():,} - ₹{df['price'].max():,}")
print(f"Average rating: {df['rating'].mean():.2f}")
print(f"Average discount: {df['discount_percent'].mean():.1f}%")

print("\n" + "=" * 60)
print("DATA PREVIEW")
print("=" * 60)
print(df[['brand', 'product_name', 'price', 'rating', 'total_reviews', '5g_support']].to_string())

print("\n" + "=" * 60)
print("✓ Data saved to: mobile_data.csv")
print("=" * 60)

print("\n📊 NEXT STEPS:")
print("1. Collect data over multiple days/weeks for time-series")
print("2. Clean and preprocess the data")
print("3. Engineer features (price trends, rating velocity, etc.)")
print("4. Build prediction models (LSTM/Prophet/XGBoost)")
print("\n✓ Your scraping script is ready in 'scrape_mobiles.py'")
print("  Just replace sample URLs with real Flipkart product links!")
