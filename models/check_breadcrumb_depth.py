import pandas as pd

products = pd.read_csv("data/processed/products_clean.csv")


def get_level(breadcrumb, level=1):
    """level=0 is top ('Clothing, Shoes & Jewelry'), level=1 is next
    ('Men' / 'Women' / 'Boys' / 'Girls'), etc."""
    if pd.isna(breadcrumb):
        return "Unknown"
    parts = [p.strip() for p in str(breadcrumb).split("›")]
    return parts[level] if len(parts) > level else "Unknown"


products["audience"] = products["breadcrumbs"].apply(lambda b: get_level(b, 1))

print("Level-1 breadcrumb value counts:")
print(products["audience"].value_counts())
print(f"\nUnknown/missing: {(products['audience'] == 'Unknown').sum()} of {len(products)}")

print("\nSample breadcrumbs for spot-checking:")
print(products["breadcrumbs"].dropna().sample(10, random_state=1).tolist())