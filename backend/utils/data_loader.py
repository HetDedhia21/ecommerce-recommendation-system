import pandas as pd
import ftfy
import re
import os

RAW_PRODUCTS = "data/products.csv"
RAW_REVIEWS = "data/reviews.csv"
PROCESSED_DIR = "data/processed"


def fix_encoding(text):
    if pd.isna(text):
        return ""
    return ftfy.fix_text(str(text))


def clean_products(df):
    df = df.copy()

    # Fix mojibake in text fields
    text_cols = ["title", "about_item", "product_description", "brand_name"]
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].apply(fix_encoding)

    # Drop rows with no asin or no title — unusable for recommendations
    df = df.dropna(subset=["asin", "title"])
    df = df.drop_duplicates(subset=["asin"])

    # Clean price: strip "$" and text, convert to float
    if "price_value" in df.columns:
        df["price_value"] = pd.to_numeric(df["price_value"], errors="coerce")

    # Clean rating count: "1,654 ratings" -> 1654
    def parse_count(x):
        if pd.isna(x):
            return 0
        digits = re.sub(r"[^\d]", "", str(x))
        return int(digits) if digits else 0

    if "rating_count" in df.columns:
        df["rating_count_clean"] = df["rating_count"].apply(parse_count)

    # Clean rating stars: "4.6 out of 5 stars" -> 4.6
    if "rating_stars" in df.columns:
        df["rating_stars_clean"] = (
            df["rating_stars"]
            .astype(str)
            .str.extract(r"([\d.]+)")
            .astype(float)
        )

    # Build a single text field for content-based filtering later
    df["content_text"] = (
        df.get("title", "").fillna("") + ". " +
        df.get("about_item", "").fillna("") + ". " +
        df.get("product_description", "").fillna("")
    )

    return df


def clean_reviews(df):
    df = df.copy()

    df["reviewText"] = df["reviewText"].apply(fix_encoding)
    if "reviewTitle" in df.columns:
        df["reviewTitle"] = df["reviewTitle"].apply(fix_encoding)

    # Drop reviews with no text or no product link
    df = df.dropna(subset=["reviewText", "productASIN"])
    df = df.drop_duplicates(subset=["reviewID"])

    # Ratings should be numeric
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    df = df.dropna(subset=["rating"])

    return df


def run():
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    products = pd.read_csv(RAW_PRODUCTS)
    reviews = pd.read_csv(RAW_REVIEWS)

    products_clean = clean_products(products)
    reviews_clean = clean_reviews(reviews)

    products_clean.to_csv(f"{PROCESSED_DIR}/products_clean.csv", index=False)
    reviews_clean.to_csv(f"{PROCESSED_DIR}/reviews_clean.csv", index=False)

    print(f"Products: {len(products)} -> {len(products_clean)} after cleaning")
    print(f"Reviews: {len(reviews)} -> {len(reviews_clean)} after cleaning")


if __name__ == "__main__":
    run()