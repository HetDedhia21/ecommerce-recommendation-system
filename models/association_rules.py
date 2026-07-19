import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder
import pickle
import os

REVIEWS_PATH = "data/processed/reviews_with_synthetic_users.csv"
PRODUCTS_PATH = "data/processed/products_clean.csv"
MODEL_DIR = "models"


def build_baskets():
    """Group BRANDS (not individual products) by synthetic user."""
    reviews = pd.read_csv(REVIEWS_PATH)
    products = pd.read_csv(PRODUCTS_PATH)

    # Attach brand to each review via its product ASIN
    reviews = reviews.merge(
        products[["asin", "brand_name"]],
        left_on="productASIN", right_on="asin", how="left"
    )
    reviews = reviews.dropna(subset=["brand_name"])

    # Drop duplicate (user, brand) pairs -- a user with 3 reviews of the
    # same brand should only count as "engaged with that brand" once
    reviews = reviews.drop_duplicates(subset=["synthetic_user_id", "brand_name"])

    baskets = (
        reviews.groupby("synthetic_user_id")["brand_name"]
        .apply(list)
        .tolist()
    )
    baskets = [b for b in baskets if len(b) >= 2]
    return baskets


def build_association_rules(min_support=0.01, min_confidence=0.1):
    baskets = build_baskets()
    print(f"Usable baskets (2+ brands): {len(baskets)}")

    te = TransactionEncoder()
    te_array = te.fit(baskets).transform(baskets)
    basket_df = pd.DataFrame(te_array, columns=te.columns_)

    frequent_itemsets = apriori(basket_df, min_support=min_support, use_colnames=True)
    frequent_itemsets["itemset_size"] = frequent_itemsets["itemsets"].apply(len)
    print(f"Frequent itemsets found: {len(frequent_itemsets)}")
    print(frequent_itemsets["itemset_size"].value_counts().sort_index())

    if (frequent_itemsets["itemset_size"] >= 2).sum() == 0:
        print("Still no 2+ itemsets -- lower min_support further")
        return None

    rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=min_confidence)
    rules = rules.sort_values("lift", ascending=False)

    os.makedirs(MODEL_DIR, exist_ok=True)
    with open(f"{MODEL_DIR}/association_rules.pkl", "wb") as f:
        pickle.dump(rules, f)

    print(f"Association rules found: {len(rules)}")
    return rules


def show_readable_rules(rules, top_n=10):
    for _, row in rules.head(top_n).iterrows():
        print(f"\nIf a user engaged with: {list(row['antecedents'])}")
        print(f"  -> they often also engaged with: {list(row['consequents'])}")
        print(f"  confidence: {row['confidence']:.2f}, lift: {row['lift']:.2f}")


if __name__ == "__main__":
    rules = build_association_rules()
    if rules is not None and len(rules) > 0:
        show_readable_rules(rules)