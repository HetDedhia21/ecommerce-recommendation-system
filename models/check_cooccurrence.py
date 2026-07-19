import pandas as pd
from itertools import combinations
from collections import Counter

REVIEWS_PATH = "data/processed/reviews_with_synthetic_users.csv"

reviews = pd.read_csv(REVIEWS_PATH)
reviews = reviews.drop_duplicates(subset=["synthetic_user_id", "productASIN"])

baskets = (
    reviews.groupby("synthetic_user_id")["productASIN"]
    .apply(list)
    .tolist()
)
baskets = [b for b in baskets if len(b) >= 2]

# Count how many times every possible pair of products co-occurs in a basket
pair_counts = Counter()
for basket in baskets:
    for pair in combinations(sorted(set(basket)), 2):
        pair_counts[pair] += 1

print(f"Total baskets: {len(baskets)}")
print(f"Unique product pairs that co-occurred at least once: {len(pair_counts)}")
print(f"Max times any single pair co-occurred: {max(pair_counts.values())}")
print("Top 10 most common pairs:")
for pair, count in pair_counts.most_common(10):
    print(f"  {pair}: {count} baskets")