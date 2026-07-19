import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import os

REVIEWS_PATH = "data/processed/reviews_with_synthetic_users.csv"
OUTPUT_PATH = "data/processed/reviews_with_sentiment.csv"
PRODUCT_SENTIMENT_PATH = "data/processed/product_sentiment_summary.csv"

analyzer = SentimentIntensityAnalyzer()


def get_sentiment(text):
    if pd.isna(text) or str(text).strip() == "":
        return 0.0, "neutral"

    scores = analyzer.polarity_scores(str(text))
    compound = scores["compound"]

    # Standard VADER thresholds
    if compound >= 0.05:
        label = "positive"
    elif compound <= -0.05:
        label = "negative"
    else:
        label = "neutral"

    return compound, label


def run():
    reviews = pd.read_csv(REVIEWS_PATH)

    # Run VADER on the actual review text (not the pre-stripped
    # cleaned_review_text -- VADER relies on punctuation/capitalization
    # for emphasis, which cleaning may have removed)
    results = reviews["reviewText"].apply(get_sentiment)
    reviews["vader_compound"] = results.apply(lambda x: x[0])
    reviews["vader_label"] = results.apply(lambda x: x[1])

    # Compare with the pre-existing sentiment_score, if present
    if "sentiment_score" in reviews.columns:
        correlation = reviews["vader_compound"].corr(reviews["sentiment_score"])
        print(f"Correlation between our VADER score and existing sentiment_score: {correlation:.3f}")

    print("\nLabel distribution:")
    print(reviews["vader_label"].value_counts())

    # Star rating vs our sentiment label -- a sanity check.
    # 4-5 star reviews should mostly be labeled positive, 1-2 star mostly negative.
    print("\nAvg star rating per sentiment label:")
    print(reviews.groupby("vader_label")["rating"].mean())

    os.makedirs("data/processed", exist_ok=True)
    reviews.to_csv(OUTPUT_PATH, index=False)

    # Aggregate to product level: average sentiment per product,
    # useful later for the hybrid system and for display in the UI
    product_sentiment = (
        reviews.groupby("productASIN")
        .agg(
            avg_sentiment=("vader_compound", "mean"),
            review_count=("vader_compound", "count"),
            positive_pct=("vader_label", lambda x: (x == "positive").mean()),
        )
        .reset_index()
    )
    product_sentiment.to_csv(PRODUCT_SENTIMENT_PATH, index=False)
    print(f"\nSaved per-product sentiment summary for {len(product_sentiment)} products")


if __name__ == "__main__":
    run()