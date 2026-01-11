from scrape_mobiles import FlipkartMobileScraper

# Initialize scraper
scraper = FlipkartMobileScraper()

# Updated Flipkart mobile product URLs (as of Jan 2026)
product_urls = [
    'https://www.flipkart.com/apple-iphone-15-black-128-gb/p/itm6ac6485515ae4',
    'https://www.flipkart.com/samsung-galaxy-s24-exynos-5g-cobalt-violet-256-gb/p/itm93794d8fd6381',
    'https://www.flipkart.com/oneplus-12-silky-black-256-gb/p/itm4464454f95a2e',
    'https://www.flipkart.com/xiaomi-14-black-512-gb/p/itm9199c6406170d',
    'https://www.flipkart.com/realme-gt-8-pro/p/itm78c31e0a1941f',
]

print("=" * 60)
print("FLIPKART MOBILE SCRAPER - AUTOMATED RUN")
print("=" * 60)
print(f"\nScraping {len(product_urls)} products...\n")

# Try scraping with error handling
successful = 0
failed = 0

for i, url in enumerate(product_urls, 1):
    print(f"\n[{i}/{len(product_urls)}] Processing: {url}")
    try:
        product_data = scraper.scrape_product_page(url)
        if product_data:
            scraper.data.append(product_data)
            successful += 1
        else:
            failed += 1
    except Exception as e:
        print(f"✗ Failed: {e}")
        failed += 1

print("\n" + "=" * 60)
print(f"Scraping completed!")
print(f"  Successful: {successful}")
print(f"  Failed: {failed}")
print("=" * 60)

# Save to CSV
if scraper.data:
    scraper.save_to_csv('mobile_data.csv')
    print("\n✓ Check 'mobile_data.csv' for the scraped data")
else:
    print("\n⚠ No data was collected. This might be due to:")
    print("  - Invalid URLs")
    print("  - Network issues")
    print("  - Flipkart page structure changes")
    print("  - Rate limiting/blocking")
    print("\nTry manually visiting Flipkart and copying fresh product URLs.")
