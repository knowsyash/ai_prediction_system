import pandas as pd

# Load the data
df = pd.read_csv('mobile_data.csv')

print("=" * 60)
print("MISSING DATA ANALYSIS")
print("=" * 60)

print("\nColumns with missing values:")
print("-" * 60)

for col in df.columns:
    missing = df[col].isnull().sum()
    if missing > 0:
        print(f"  {col:20s}: {missing}/{len(df)} missing ({missing/len(df)*100:.1f}%)")

print("\n" + "=" * 60)
print("DATA COMPLETENESS SUMMARY")
print("=" * 60)

total_cells = df.shape[0] * df.shape[1]
missing_cells = df.isnull().sum().sum()
completeness = (1 - missing_cells/total_cells) * 100

print(f"Total products: {df.shape[0]}")
print(f"Total attributes: {df.shape[1]}")
print(f"Missing values: {missing_cells}/{total_cells}")
print(f"Data completeness: {completeness:.1f}%")

print("\n" + "=" * 60)
print("CURRENT DATA SAMPLE")
print("=" * 60)
print(df[['brand', 'product_name', 'price', 'ram', 'storage', 'battery', 'rating']].to_string(index=False))
