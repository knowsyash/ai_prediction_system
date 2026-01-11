import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Load the data
df = pd.read_csv('mobile_data.csv')

print("=" * 60)
print("MOBILE DATA ANALYSIS")
print("=" * 60)

print(f"\n📊 Dataset Overview:")
print(f"Total products: {len(df)}")
print(f"Brands: {df['brand'].nunique()}")
print(f"Date collected: {df['date_scraped'].iloc[0]}")

print(f"\n💰 Price Statistics:")
print(f"Average price: ₹{df['price'].mean():,.0f}")
print(f"Lowest price: ₹{df['price'].min():,.0f}")
print(f"Highest price: ₹{df['price'].max():,.0f}")

print(f"\n⭐ Rating Statistics:")
if df['rating'].notna().any():
    print(f"Average rating: {df['rating'].mean():.2f}")
else:
    print("No rating data available")

print(f"\n📈 Engagement Metrics:")
print(f"Total ratings across all products: {df['total_ratings'].sum():,}")

print("\n" + "=" * 60)
print("PRODUCT DETAILS")
print("=" * 60)
print(df[['brand', 'product_name', 'price', 'discount_percent', 'total_ratings']].to_string(index=False))

print("\n" + "=" * 60)
print("✓ Data collection successful!")
print("✓ Ready for time-series collection (run daily/weekly)")
print("=" * 60)

# Basic visualization if matplotlib works
try:
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle('Mobile Demand Prediction - Initial Data Analysis', fontsize=14, fontweight='bold')
    
    # Price by brand
    if df['brand'].notna().any():
        df_clean = df[df['price'].notna() & df['brand'].notna()]
        axes[0, 0].bar(range(len(df_clean)), df_clean['price'])
        axes[0, 0].set_xticks(range(len(df_clean)))
        axes[0, 0].set_xticklabels(df_clean['brand'], rotation=45)
        axes[0, 0].set_title('Price by Brand')
        axes[0, 0].set_ylabel('Price (₹)')
        axes[0, 0].grid(axis='y', alpha=0.3)
    
    # Total ratings
    if df['total_ratings'].notna().any():
        df_ratings = df[df['total_ratings'].notna() & df['brand'].notna()]
        axes[0, 1].bar(range(len(df_ratings)), df_ratings['total_ratings'])
        axes[0, 1].set_xticks(range(len(df_ratings)))
        axes[0, 1].set_xticklabels(df_ratings['brand'], rotation=45)
        axes[0, 1].set_title('Total Ratings (Popularity Indicator)')
        axes[0, 1].set_ylabel('Number of Ratings')
        axes[0, 1].grid(axis='y', alpha=0.3)
    
    # Discount percentage
    if df['discount_percent'].notna().any():
        df_discount = df[df['discount_percent'].notna() & df['brand'].notna()]
        axes[1, 0].bar(range(len(df_discount)), df_discount['discount_percent'])
        axes[1, 0].set_xticks(range(len(df_discount)))
        axes[1, 0].set_xticklabels(df_discount['brand'], rotation=45)
        axes[1, 0].set_title('Discount Percentage')
        axes[1, 0].set_ylabel('Discount (%)')
        axes[1, 0].grid(axis='y', alpha=0.3)
    
    # Price vs Ratings scatter
    if df['price'].notna().any() and df['total_ratings'].notna().any():
        df_scatter = df[(df['price'].notna()) & (df['total_ratings'].notna())]
        axes[1, 1].scatter(df_scatter['price'], df_scatter['total_ratings'], s=100, alpha=0.6)
        for i, brand in enumerate(df_scatter['brand']):
            axes[1, 1].annotate(brand, 
                               (df_scatter['price'].iloc[i], df_scatter['total_ratings'].iloc[i]),
                               fontsize=8, alpha=0.7)
        axes[1, 1].set_title('Price vs Popularity')
        axes[1, 1].set_xlabel('Price (₹)')
        axes[1, 1].set_ylabel('Total Ratings')
        axes[1, 1].grid(alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('mobile_analysis.png', dpi=150, bbox_inches='tight')
    print("\n📊 Visualization saved as 'mobile_analysis.png'")
    plt.show()
    
except Exception as e:
    print(f"\nVisualization skipped: {e}")
