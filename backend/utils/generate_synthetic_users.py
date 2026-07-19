import pandas as pd
import numpy as np
import os

REVIEWS_PATH = "data/processed/reviews_clean.csv"
PRODUCTS_PATH = "data/processed/products_clean.csv"
OUTPUT_PATH = "data/processed/reviews_with_synthetic_users.csv"

np.random.seed(42)  # reproducible randomness


def get_top_category(breadcrumb):
    """Breadcrumbs look like 'Clothing, Shoes & Jewelry › Men › Clothing › Active › Polos'.
    We just want the broad top-level category, e.g. 'Clothing, Shoes & Jewelry'."""
    if pd.isna(breadcrumb):
        return "Unknown"
    return str(breadcrumb).split("›")[0].strip()


def generate_synthetic_users():
    reviews = pd.read_csv(REVIEWS_PATH)
    products = pd.read_csv(PRODUCTS_PATH)

    # Attach each review's product category
    products["top_category"] = products["breadcrumbs"].apply(get_top_category)
    reviews = reviews.merge(
        products[["asin", "top_category"]],
        left_on="productASIN", right_on="asin", how="left"
    )
    reviews["top_category"] = reviews["top_category"].fillna("Unknown")

    categories = reviews["top_category"].unique().tolist()

    # Roughly 1 synthetic user per 3 reviews on average -> gives repeat reviewers
    num_users = max(50, len(reviews) // 3)
    user_ids = [f"synth_user_{i}" for i in range(num_users)]

    # Each user gets a home category, weighted by how common that category is overall
    category_weights = reviews["top_category"].value_counts(normalize=True)
    user_home_category = np.random.choice(
        category_weights.index,
        size=num_users,
        p=category_weights.values
    )
    user_home_map = dict(zip(user_ids, user_home_category))

    # Group review row-indices by category, so we can pull matching reviews for each user
    category_to_indices = {
        cat: reviews.index[reviews["top_category"] == cat].tolist()
        for cat in categories
    }
    for cat in category_to_indices:
        np.random.shuffle(category_to_indices[cat])

    assigned_user = pd.Series([None] * len(reviews), index=reviews.index)

    # Each user "writes" a number of reviews following a light power-law:
    # most users write 1-2, a few write many more (mirrors real reviewer behavior)
    for user in user_ids:
        home_cat = user_home_map[user]
        n_reviews = min(int(np.random.zipf(a=2.5)), 10)  # cap so no single user dominates

        for _ in range(n_reviews):
            # 80% chance: pull from home category. 20%: pull from any category (cross-shopping)
            if np.random.rand() < 0.8 and category_to_indices.get(home_cat):
                pool_cat = home_cat
            else:
                pool_cat = np.random.choice(categories)

            pool = category_to_indices.get(pool_cat, [])
            if not pool:
                continue

            idx = pool.pop()
            if assigned_user[idx] is None:
                assigned_user[idx] = user

    # Any leftover unassigned reviews (ran out of user "budget") get assigned to random existing users
    unassigned = assigned_user[assigned_user.isna()].index
    assigned_user.loc[unassigned] = np.random.choice(user_ids, size=len(unassigned))

    reviews["synthetic_user_id"] = assigned_user

    os.makedirs("data/processed", exist_ok=True)
    reviews.to_csv(OUTPUT_PATH, index=False)

    # Summary stats so we can sanity-check the simulation
    reviews_per_user = reviews.groupby("synthetic_user_id").size()
    print(f"Total reviews: {len(reviews)}")
    print(f"Synthetic users created: {reviews['synthetic_user_id'].nunique()}")
    print(f"Avg reviews per user: {reviews_per_user.mean():.2f}")
    print(f"Users with 2+ reviews: {(reviews_per_user >= 2).sum()}")
    print(f"Max reviews by one user: {reviews_per_user.max()}")


if __name__ == "__main__":
    generate_synthetic_users()