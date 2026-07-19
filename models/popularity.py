import pandas as pd

PRODUCTS_PATH = "data/processed/products_clean.csv"
SENTIMENT_PATH = "data/processed/product_sentiment_summary.csv"


def parse_recent_purchases(x):
    """'50+ bought' -> 50, missing -> 0"""
    if pd.isna(x):
        return 0
    digits = "".join(c for c in str(x) if c.isdigit())
    return int(digits) if digits else 0


def build_popularity_score():
    products = pd.read_csv(PRODUCTS_PATH)
    sentiment = pd.read_csv(SENTIMENT_PATH)

    products["recent_purchases_clean"] = products["recent_purchases"].apply(parse_recent_purchases)

    # Merge in sentiment so popularity isn't purely volume-based
    products = products.merge(sentiment, left_on="asin", right_on="productASIN", how="left")
    products["avg_sentiment"] = products["avg_sentiment"].fillna(0)

    # Normalize each signal to 0-1 so they're comparable before combining
    def normalize(col):
        return (col - col.min()) / (col.max() - col.min() + 1e-9)

    products["norm_rating_count"] = normalize(products["rating_count_clean"])
    products["norm_rating_stars"] = normalize(products["rating_stars_clean"].fillna(0))
    products["norm_recent_purchases"] = normalize(products["recent_purchases_clean"])
    products["norm_sentiment"] = normalize(products["avg_sentiment"])

    # Weighted popularity score: rating volume + rating quality + recent
    # momentum + sentiment, weighted so no single noisy signal dominates
    products["popularity_score"] = (
        0.35 * products["norm_rating_count"] +
        0.25 * products["norm_rating_stars"] +
        0.25 * products["norm_recent_purchases"] +
        0.15 * products["norm_sentiment"]
    )

    # Deduplicate near-identical listings by title, keeping the one with
    # the higher rating_count_clean (the "main" listing, likely)
    products = products.sort_values("rating_count_clean", ascending=False)
    products = products.drop_duplicates(subset=["title"], keep="first")

    products = products.sort_values("popularity_score", ascending=False)
    products[["asin", "title", "rating_count_clean", "rating_stars_clean",
              "recent_purchases_clean", "avg_sentiment", "popularity_score"]].to_csv(
        "data/processed/popularity_ranking.csv", index=False
    )

    return products


def get_top_products(n=10):
    products = pd.read_csv("data/processed/popularity_ranking.csv")
    return products.head(n)


if __name__ == "__main__":
    ranked = build_popularity_score()
    print("Top 10 trending/best-selling products:\n")
    for _, row in ranked.head(10).iterrows():
        print(f"{row['title'][:60]}")
        print(f"  rating_count={row['rating_count_clean']}, stars={row['rating_stars_clean']}, "
              f"popularity_score={row['popularity_score']:.3f}\n")