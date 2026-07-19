import pandas as pd

products = pd.read_csv("data/processed/products_clean.csv")

print("Unique brands:", products["brand_name"].nunique())
print(products["brand_name"].value_counts().head(15))
print()

def top_category(breadcrumb):
    if pd.isna(breadcrumb):
        return "Unknown"
    return str(breadcrumb).split("›")[0].strip()

products["top_category"] = products["breadcrumbs"].apply(top_category)
print("Unique top categories:", products["top_category"].nunique())
print(products["top_category"].value_counts().head(15))