"""Generate Word Clouds for All Products - Quick Script"""

import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from pathlib import Path

def generate_wordcloud_for_product(csv_path, product_name, output_dir):
    """Generate word cloud for a single product"""
    print(f"\nProcessing {product_name}...")
    
    # Load reviews
    try:
        df = pd.read_csv(csv_path)
        print(f"  Loaded {len(df)} reviews")
    except Exception as e:
        print(f"  Error loading CSV: {e}")
        return
    
    # Combine all text
    all_text = []
    if 'title' in df.columns:
        all_text.extend(df['title'].dropna().astype(str).tolist())
    if 'review_text' in df.columns:
        all_text.extend(df['review_text'].dropna().astype(str).tolist())
    
    combined_text = ' '.join(all_text)
    print(f"  Text length: {len(combined_text)} characters")
    
    # Generate word cloud
    wordcloud = WordCloud(
        width=1600,
        height=800,
        background_color='white',
        colormap='viridis',
        max_words=200,
        relative_scaling=0.5,
        min_font_size=10
    ).generate(combined_text)
    
    # Create and save figure
    plt.figure(figsize=(16, 8))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.title(f'{product_name} Reviews - Word Cloud', fontsize=20, pad=20)
    plt.tight_layout(pad=0)
    
    output_path = output_dir / f'{product_name.lower().replace(" ", "_")}_wordcloud.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ Saved to: {output_path}")

def main():
    base_dir = Path(__file__).parent
    output_dir = base_dir / 'wordclouds'
    output_dir.mkdir(exist_ok=True)
    
    # Product configurations
    products = [
        ('data_scrapping/iphone15/iphone15_reviews.csv', 'iPhone 15'),
        ('data_scrapping/iphone16/iphone16_reviews.csv', 'iPhone 16'),
        ('data_scrapping/iqoo_zx10/iqoo_z10_reviews.csv', 'iQOO Z10'),
    ]
    
    print("=" * 70)
    print("Generating Word Clouds for All Products")
    print("=" * 70)
    
    for csv_path, product_name in products:
        full_path = base_dir / csv_path
        if full_path.exists():
            generate_wordcloud_for_product(full_path, product_name, output_dir)
        else:
            print(f"\nSkipping {product_name} - CSV not found at {full_path}")
    
    print("\n" + "=" * 70)
    print(f"All word clouds saved to: {output_dir}")
    print("=" * 70)

if __name__ == '__main__':
    main()
