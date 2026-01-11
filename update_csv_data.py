import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time

def extract_specs_from_url(url):
    """Extract specifications from product URL using regex on page text"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text()
        
        specs = {}
        
        # Extract RAM
        ram_match = re.findall(r'(\d+)\s*GB\s*RAM', text, re.IGNORECASE)
        specs['ram'] = f"{ram_match[0]} GB" if ram_match else None
        
        # Extract Storage
        storage_match = re.findall(r'(\d+)\s*GB\s*(?:ROM|Storage|Internal)', text, re.IGNORECASE)
        specs['storage'] = f"{storage_match[0]} GB" if storage_match else None
        
        # Extract Battery
        battery_match = re.findall(r'(\d+)\s*mAh', text)
        specs['battery'] = f"{battery_match[0]} mAh" if battery_match else None
        
        # Extract Camera
        camera_match = re.findall(r'(\d+)\s*MP', text)
        if camera_match:
            # Get unique camera values
            unique_cameras = list(dict.fromkeys(camera_match))[:3]
            specs['camera_primary'] = ' + '.join([f"{c} MP" for c in unique_cameras])
        else:
            specs['camera_primary'] = None
        
        # Extract Processor
        processor_patterns = [
            r'(A\d+\s+Bionic)',
            r'(Snapdragon\s+\d+(?:\s+Gen\s+\d+)?)',
            r'(Exynos\s+\d+)',
            r'(MediaTek\s+Dimensity\s+\d+)',
            r'(Tensor\s+G\d+)'
        ]
        specs['processor'] = None
        for pattern in processor_patterns:
            proc_match = re.search(pattern, text, re.IGNORECASE)
            if proc_match:
                specs['processor'] = proc_match.group(1)
                break
        
        # Extract Screen Size
        screen_match = re.findall(r'(\d+\.?\d*)\s*(?:inch|")', text, re.IGNORECASE)
        if screen_match:
            # Filter realistic screen sizes (between 5 and 8 inches)
            realistic_sizes = [float(s) for s in screen_match if 5 <= float(s) <= 8]
            specs['screen_size'] = f"{realistic_sizes[0]} inch" if realistic_sizes else None
        else:
            specs['screen_size'] = None
        
        # Extract Rating
        rating_match = re.search(r'(\d\.\d)\s*★', text)
        specs['rating'] = float(rating_match.group(1)) if rating_match else None
        
        # 5G Support
        specs['5g_support'] = 'Yes' if re.search(r'5G', text, re.IGNORECASE) else 'No'
        
        return specs
    except Exception as e:
        print(f"Error extracting specs: {e}")
        return {}

# Load current CSV
df = pd.read_csv('mobile_data.csv')

print("Updating missing specifications...")
print("=" * 60)

# Update each product
for idx, row in df.iterrows():
    if pd.notna(row['product_url']) and pd.notna(row['brand']):
        product_name = str(row['product_name'])[:50] if pd.notna(row['product_name']) else 'Unknown'
        print(f"\nProcessing: {row['brand']} - {product_name}...")
        
        # Extract specs
        specs = extract_specs_from_url(row['product_url'])
        
        # Update DataFrame
        for key, value in specs.items():
            if value is not None:
                df.at[idx, key] = value
                print(f"  ✓ {key}: {value}")
        
        time.sleep(2)  # Rate limiting

# Fill some missing data based on product names
for idx, row in df.iterrows():
    product_name = str(row['product_name'])
    
    # Extract RAM from product name if missing
    if pd.isna(row['ram']):
        ram_in_name = re.search(r'\((\d+)\s*GB\s*RAM\)', product_name)
        if ram_in_name:
            df.at[idx, 'ram'] = f"{ram_in_name.group(1)} GB"
    
    # Extract storage from product name if missing
    if pd.isna(row['storage']):
        storage_in_name = re.search(r'\(.*?(\d+)\s*GB\)', product_name)
        if storage_in_name:
            df.at[idx, 'storage'] = f"{storage_in_name.group(1)} GB"

# Save updated CSV
df.to_csv('mobile_data.csv', index=False, encoding='utf-8-sig')

print("\n" + "=" * 60)
print("✓ CSV file updated successfully!")
print("=" * 60)

# Show summary
print("\nUpdated Data Summary:")
print("-" * 60)
for col in ['brand', 'product_name', 'price', 'ram', 'storage', 'battery', 'camera_primary', 'rating']:
    print(f"\n{col}:")
    print(df[col].to_string(index=False))
