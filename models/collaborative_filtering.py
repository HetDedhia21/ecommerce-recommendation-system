import pandas as pd
import numpy as np
from sklearn.decomposition import TruncatedSVD
import pickle
import os

REVIEWS_PATH = "data/processed/reviews_with_synthetic_users.csv"
PRODUCTS_PATH = "data/processed/products_clean.csv"
MODEL_DIR = "models"


def build_user_item_matrix():
    reviews = pd.read_csv(REVIEWS_PATH)

    ratings = (
        reviews.groupby(["synthetic_user_id", "productASIN"])["rating"]
        .mean()
        .reset_index()
    )

    global_mean = ratings["rating"].mean()

    matrix = ratings.pivot(index="synthetic_user_id", columns="productASIN", values="rating")

    # Mean-center: known ratings become their deviation from the global
    # average; unknown ratings become 0 (= "assume average"), instead of
    # 0 meaning "assume terrible" like before
    matrix_centered = matrix - global_mean
    matrix_centered = matrix_centered.fillna(0)

    return matrix_centered, matrix, global_mean


def build_cf_model(n_components=20):
    matrix_centered, matrix_raw, global_mean = build_user_item_matrix()
    print(f"User-item matrix shape: {matrix_centered.shape}")

    n_components = min(n_components, min(matrix_centered.shape) - 1)

    svd = TruncatedSVD(n_components=n_components, random_state=42)
    user_factors = svd.fit_transform(matrix_centered)
    item_factors = svd.components_.T

    predicted_matrix = np.dot(user_factors, item_factors.T) + global_mean  # shift back to 1-5 scale

    predicted_df = pd.DataFrame(
        predicted_matrix, index=matrix_centered.index, columns=matrix_centered.columns
    )

    os.makedirs(MODEL_DIR, exist_ok=True)
    with open(f"{MODEL_DIR}/collaborative_filtering.pkl", "wb") as f:
        pickle.dump({
            "predicted_matrix": predicted_df,
            "original_matrix": matrix_raw.fillna(0),
            "global_mean": global_mean,
            "explained_variance": svd.explained_variance_ratio_.sum(),
        }, f)

    print(f"Global mean rating: {global_mean:.3f}")
    print(f"Explained variance with {n_components} components: {svd.explained_variance_ratio_.sum():.3f}")
    return predicted_df, matrix_raw.fillna(0)


def recommend_for_user(user_id, top_n=5):
    with open(f"{MODEL_DIR}/collaborative_filtering.pkl", "rb") as f:
        data = pickle.load(f)

    predicted_matrix = data["predicted_matrix"]
    original_matrix = data["original_matrix"]

    if user_id not in predicted_matrix.index:
        print(f"User {user_id} not found")
        return []

    user_predictions = predicted_matrix.loc[user_id]
    already_rated = original_matrix.loc[user_id]

    # Only recommend products the user hasn't already rated
    unrated_mask = already_rated == 0
    candidates = user_predictions[unrated_mask].sort_values(ascending=False)

    products = pd.read_csv(PRODUCTS_PATH)
    asin_to_title = dict(zip(products["asin"], products["title"]))
    asin_to_brand = dict(zip(products["asin"], products["brand_name"]))

    results = []
    for asin, score in candidates.head(top_n).items():
        results.append({
            "asin": asin,
            "title": asin_to_title.get(asin, "Unknown"),
            "brand": asin_to_brand.get(asin, "Unknown"),
            "predicted_score": round(float(score), 3),
        })
    return results


if __name__ == "__main__":
    predicted_df, matrix = build_cf_model()

    # Pick a user with a decent number of ratings for a meaningful test
    ratings_per_user = (matrix != 0).sum(axis=1)
    test_user = ratings_per_user.sort_values(ascending=False).index[0]

    print(f"\nTest user: {test_user} ({ratings_per_user[test_user]} products rated)")
    print("Already rated brands:")
    rated_asins = matrix.loc[test_user][matrix.loc[test_user] != 0].index
    products = pd.read_csv(PRODUCTS_PATH)
    rated_brands = products[products["asin"].isin(rated_asins)]["brand_name"].tolist()
    print(rated_brands)

    print("\nTop 5 recommended products:")
    for rec in recommend_for_user(test_user):
        print(f"  - {rec['title'][:55]} ({rec['brand']})  predicted: {rec['predicted_score']}")