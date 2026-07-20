import pandas as pd
import numpy as np
import pickle

MODEL_DIR = "models"
PRODUCTS_PATH = "data/processed/products_clean.csv"


def load_all():
    with open(f"{MODEL_DIR}/content_similarity.pkl", "rb") as f:
        content_data = pickle.load(f)
    with open(f"{MODEL_DIR}/collaborative_filtering.pkl", "rb") as f:
        cf_data = pickle.load(f)
    with open(f"{MODEL_DIR}/association_rules.pkl", "rb") as f:
        rules = pickle.load(f)

    popularity = pd.read_csv(f"data/processed/popularity_ranking.csv")
    sentiment = pd.read_csv(f"data/processed/product_sentiment_summary.csv")
    products = pd.read_csv(PRODUCTS_PATH)

    return content_data, cf_data, rules, popularity, sentiment, products


def normalize_series(s):
    if s.max() == s.min():
        return s * 0
    return (s - s.min()) / (s.max() - s.min())

def get_audience(breadcrumb):
    if pd.isna(breadcrumb):
        return "Unknown"
    parts = [p.strip() for p in str(breadcrumb).split("›")]
    return parts[1] if len(parts) > 1 else "Unknown"


def get_user_audience(user_id, cf_data, products):
    """A user's dominant audience = the most common audience among
    products they've already rated."""
    original = cf_data["original_matrix"]
    if user_id not in original.index:
        return None

    rated_asins = original.loc[user_id][original.loc[user_id] != 0].index
    rated_products = products[products["asin"].isin(rated_asins)]
    if len(rated_products) == 0:
        return None

    audiences = rated_products["audience"]
    audiences = audiences[audiences != "Unknown"]
    if len(audiences) == 0:
        return None

    return audiences.mode().iloc[0]  # most frequent audience


def filter_by_audience(candidates, target_audience, products):
    """Keep only candidates matching target_audience, or with Unknown
    audience (don't penalize missing data, just don't use it to exclude)."""
    if target_audience is None:
        return candidates  # no signal to filter on, leave as-is

    audience_map = dict(zip(products["asin"], products["audience"]))
    candidates = candidates.copy()
    candidates["_audience"] = candidates["asin"].map(audience_map)
    mask = (candidates["_audience"] == target_audience) | (candidates["_audience"] == "Unknown")
    return candidates[mask].drop(columns=["_audience"])

def get_similar_products(seed_asin, content_data, top_n=50):
    """Content-based candidates for a given seed product."""
    matrix = content_data["similarity_matrix"]
    asin_to_index = content_data["asin_to_index"]
    products = content_data["products"]

    if seed_asin not in asin_to_index:
        return pd.DataFrame(columns=["asin", "content_score"])

    idx = asin_to_index[seed_asin]
    scores = matrix[idx]
    result = pd.DataFrame({"asin": products["asin"], "content_score": scores})
    result = result[result["asin"] != seed_asin]
    return result.sort_values("content_score", ascending=False).head(top_n)


def get_cf_candidates(user_id, cf_data, top_n=50):
    """Collaborative filtering candidates for a given user."""
    predicted = cf_data["predicted_matrix"]
    original = cf_data["original_matrix"]

    if user_id not in predicted.index:
        return pd.DataFrame(columns=["asin", "cf_score"])

    user_pred = predicted.loc[user_id]
    already_rated = original.loc[user_id]
    unrated = user_pred[already_rated == 0]

    result = pd.DataFrame({"asin": unrated.index, "cf_score": normalize_series(unrated)})
    return result.sort_values("cf_score", ascending=False).head(top_n)


def get_association_boost(user_id, cf_data, rules, products):
    """Brand-level boost: if a user's rated brands appear as a rule
    antecedent, boost products from the consequent brand, weighted by
    rule confidence."""
    original = cf_data["original_matrix"]
    if user_id not in original.index:
        return pd.DataFrame(columns=["asin", "assoc_boost"])

    rated_asins = original.loc[user_id][original.loc[user_id] != 0].index
    rated_brands = set(products[products["asin"].isin(rated_asins)]["brand_name"])

    boost_by_brand = {}
    for _, rule in rules.iterrows():
        antecedents = set(rule["antecedents"])
        if antecedents & rated_brands:  # user has engaged with an antecedent brand
            for consequent_brand in rule["consequents"]:
                boost_by_brand[consequent_brand] = max(
                    boost_by_brand.get(consequent_brand, 0), rule["confidence"]
                )

    if not boost_by_brand:
        return pd.DataFrame(columns=["asin", "assoc_boost"])

    boosted = products[products["brand_name"].isin(boost_by_brand.keys())].copy()
    boosted["assoc_boost"] = boosted["brand_name"].map(boost_by_brand)
    return boosted[["asin", "assoc_boost"]]


def hybrid_recommend(user_id=None, seed_asin=None, top_n=10):
    content_data, cf_data, rules, popularity, sentiment, products = load_all()
    products["audience"] = products["breadcrumbs"].apply(get_audience)  # ADD THIS

    popularity = popularity[["asin", "popularity_score"]]
    sentiment = sentiment.rename(columns={"productASIN": "asin"})
    sentiment["sentiment_norm"] = (sentiment["avg_sentiment"] + 1) / 2
    sentiment = sentiment[["asin", "sentiment_norm"]]

    # Determine the target audience to filter by
    target_audience = None
    if seed_asin:
        seed_row = products[products["asin"] == seed_asin]
        if len(seed_row) > 0:
            target_audience = seed_row["audience"].iloc[0]
    elif user_id:
        target_audience = get_user_audience(user_id, cf_data, products)

    frames = []
    weights = {}

    if seed_asin:
        content_candidates = get_similar_products(seed_asin, content_data)
        content_candidates = filter_by_audience(content_candidates, target_audience, products)  # ADD
        frames.append(content_candidates)
        weights["content_score"] = 0.5 if not user_id else 0.35

    if user_id:
        cf_candidates = get_cf_candidates(user_id, cf_data)
        cf_candidates = filter_by_audience(cf_candidates, target_audience, products)  # ADD
        frames.append(cf_candidates)
        weights["cf_score"] = 0.35 if not seed_asin else 0.25

        assoc_candidates = get_association_boost(user_id, cf_data, rules, products)
        assoc_candidates = filter_by_audience(assoc_candidates, target_audience, products)  # ADD
        frames.append(assoc_candidates)
        weights["assoc_boost"] = 0.15

    if not frames:
        raise ValueError("Provide at least a user_id or a seed_asin")

    # Merge every signal onto a common candidate set (outer join, fill 0
    # for signals a candidate wasn't scored on)
    candidates = frames[0]
    for f in frames[1:]:
        candidates = candidates.merge(f, on="asin", how="outer")
    candidates = candidates.fillna(0)

    # Always blend in popularity and sentiment as universal signals
    candidates = candidates.merge(popularity, on="asin", how="left").fillna({"popularity_score": 0})
    candidates = candidates.merge(sentiment, on="asin", how="left").fillna({"sentiment_norm": 0.5})
    weights["popularity_score"] = 0.15
    weights["sentiment_norm"] = 0.1

    # Re-normalize weights to sum to 1 (since not every mode uses every signal)
    total_weight = sum(weights.values())
    weights = {k: v / total_weight for k, v in weights.items()}

    candidates["final_score"] = sum(
        candidates.get(col, 0) * w for col, w in weights.items()
    )

    candidates = candidates.merge(products[["asin", "title", "brand_name"]], on="asin", how="left")
    candidates = candidates.sort_values("final_score", ascending=False).drop_duplicates(subset=["asin"])

    return candidates.head(top_n)[["asin", "title", "brand_name", "final_score"]], weights


if __name__ == "__main__":
    # Test 1: personalized recommendations for a user (homepage mode)
    result, weights_used = hybrid_recommend(user_id="synth_user_2101", top_n=10)
    print("Mode: personalized (user only)")
    print("Weights used:", weights_used)
    print(result.to_string(index=False))

    print("\n" + "=" * 80 + "\n")

    # Test 2: similar products to a specific product (product-page mode)
    products = pd.read_csv(PRODUCTS_PATH)
    test_asin = products["asin"].iloc[0]
    test_title = products["title"].iloc[0]
    result2, weights_used2 = hybrid_recommend(seed_asin=test_asin, top_n=10)
    print(f"Mode: similar products to '{test_title[:50]}'")
    print("Weights used:", weights_used2)
    print(result2.to_string(index=False))

    print("\n" + "=" * 80 + "\n")

    # Test 3: full hybrid -- both a user AND a seed product
    result3, weights_used3 = hybrid_recommend(user_id="synth_user_2101", seed_asin=test_asin, top_n=10)
    print(f"Mode: full hybrid (user + product '{test_title[:40]}')")
    print("Weights used:", weights_used3)
    print(result3.to_string(index=False))