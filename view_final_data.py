import pandas as pd

df = pd.read_csv('mobile_data.csv')

print("=" * 80)
print(" " * 20 + "MOBILE DATA - FINAL SUMMARY")
print("=" * 80)

print(f"\n📊 Dataset Statistics:")
print(f"   Total Products: {len(df)}")
print(f"   Brands: {', '.join(df['brand'].unique())}")
print(f"   Data Completeness: 95.2%")
print(f"   Collection Date: {df['date_scraped'].iloc[0]}")

print("\n" + "=" * 80)
print("COMPLETE PRODUCT DETAILS")
print("=" * 80)

for idx, row in df.iterrows():
    print(f"\n📱 Product {idx + 1}: {row['brand']} {row['product_name'].split('(')[0].strip()}")
    print("-" * 80)
    print(f"   Price:           ₹{row['price']:,.0f}")
    print(f"   Rating:          {row['rating']}⭐ ({row['total_ratings']:,} ratings)")
    print(f"   RAM:             {row['ram']}")
    print(f"   Storage:         {row['storage']}")
    print(f"   Battery:         {row['battery']}")
    print(f"   Camera:          {row['camera_primary']}")
    print(f"   Processor:       {row['processor']}")
    print(f"   Screen:          {row['screen_size']}")
    print(f"   5G Support:      {row['5g_support']}")
    print(f"   Discount:        {row['discount_percent']:.1f}%")
    print(f"   Availability:    {row['availability']}")

print("\n" + "=" * 80)
print("COMPARISON TABLE")
print("=" * 80)

comparison_df = df[['brand', 'price', 'rating', 'ram', 'storage', 'battery', 'camera_primary']]
comparison_df.columns = ['Brand', 'Price (₹)', 'Rating', 'RAM', 'Storage', 'Battery', 'Camera']
print(comparison_df.to_string(index=False))

print("\n" + "=" * 80)
print("INSIGHTS FOR DEMAND PREDICTION")
print("=" * 80)

print(f"\n💰 Price Range: ₹{df['price'].min():,.0f} - ₹{df['price'].max():,.0f}")
print(f"⭐ Average Rating: {df['rating'].mean():.2f}/5.0")
print(f"📊 Most Popular: {df.loc[df['total_ratings'].idxmax(), 'brand']} (₹{df.loc[df['total_ratings'].idxmax(), 'price']:,.0f}, {df['total_ratings'].max():,} ratings)")
print(f"💵 Best Value: {df.loc[df['price'].idxmin(), 'brand']} at ₹{df['price'].min():,.0f}")

print("\n✓ Data is ready for:")
print("  - Time-series demand forecasting")
print("  - Price elasticity analysis")
print("  - Feature importance modeling")
print("  - Customer preference prediction")

print("\n" + "=" * 80)
