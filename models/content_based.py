import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import os

PROCESSED_PRODUCTS = "data/processed/products_clean.csv"
MODEL_DIR = "models"


def build_content_model():
    df = pd.read_csv(PROCESSED_PRODUCTS)
    df = df.reset_index(drop=True)

    # TF-IDF: turn each product's text into a vector of word-importance scores
    # stop_words="english" removes common filler words (the, and, is...)
    # max_features caps vocabulary size so it stays fast on 728 products
    vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
    tfidf_matrix = vectorizer.fit_transform(df["content_text"].fillna(""))

    # Cosine similarity between every pair of products -> a 728x728 matrix
    # where cell [i][j] = how similar product i is to product j (0 to 1)
    similarity_matrix = cosine_similarity(tfidf_matrix)

    # Map asin -> row index, so we can look up a product by its ID later
    asin_to_index = pd.Series(df.index, index=df["asin"]).to_dict()

    os.makedirs(MODEL_DIR, exist_ok=True)
    with open(f"{MODEL_DIR}/content_similarity.pkl", "wb") as f:
        pickle.dump({
            "similarity_matrix": similarity_matrix,
            "asin_to_index": asin_to_index,
            "products": df[["asin", "title"]],
        }, f)

    print(f"Built similarity matrix: {similarity_matrix.shape}")
    return similarity_matrix, asin_to_index, df


def get_similar_products(asin, top_n=5):
    with open(f"{MODEL_DIR}/content_similarity.pkl", "rb") as f:
        data = pickle.load(f)

    similarity_matrix = data["similarity_matrix"]
    asin_to_index = data["asin_to_index"]
    products = data["products"]

    if asin not in asin_to_index:
        print(f"Product {asin} not found")
        return []

    idx = asin_to_index[asin]
    # Get similarity scores for this product against all others
    scores = list(enumerate(similarity_matrix[idx]))
    # Sort by score descending, skip index 0 (a product is always most similar to itself)
    scores = sorted(scores, key=lambda x: x[1], reverse=True)[1:top_n + 1]

    results = []
    for i, score in scores:
        results.append({
            "asin": products.iloc[i]["asin"],
            "title": products.iloc[i]["title"],
            "similarity": round(float(score), 3)
        })
    return results


if __name__ == "__main__":
    build_content_model()

    # Quick test: show recommendations for the first product in the dataset
    df = pd.read_csv(PROCESSED_PRODUCTS)
    test_asin = df["asin"].iloc[0]
    test_title = df["title"].iloc[0]
    print(f"\nTest product: {test_title}")
    print("Similar products:")
    for rec in get_similar_products(test_asin):
        print(f"  - {rec['title'][:60]}  (score: {rec['similarity']})")