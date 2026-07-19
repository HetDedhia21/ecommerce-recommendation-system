# E-commerce Recommendation System

A multi-technique product recommendation engine built on real scraped Amazon
product and review data, combining content similarity, association rules,
sentiment analysis, and collaborative filtering into a hybrid system with a
FastAPI backend.

## Project Goal

Build a smart recommendation engine that suggests products using product
similarity, purchase/behavior patterns, and review sentiment — demonstrating
multiple real-world recommendation techniques in one deployable project.

## Features

**Core (Phase 1)**
1. Content-Based Recommendation — TF-IDF + Cosine Similarity over product
   titles/descriptions. ✅ Implemented
2. Frequently Bought Together — Association Rule Mining (Apriori/FP-Growth)
   over co-occurrence patterns. 🔲 Planned

**Intermediate (Phase 2)**
3. Popularity-Based Recommendation (trending / best sellers). 🔲 Planned
4. Sentiment Analysis on reviews (TextBlob/VADER). 🔲 Planned (a
   preliminary `sentiment_score` exists in the raw data but needs to be
   verified/reproduced as part of this project's own pipeline)

**Advanced (Phase 3)**
5. Collaborative Filtering (User-Item Matrix, optional SVD). 🔲 Planned
6. Hybrid Recommendation System combining the above. 🔲 Planned

**Bonus**
- Rating prediction
- Explainable recommendations
- Inventory-based recommendations

## Dataset

Real scraped Amazon data (provided, original scraper unknown):
- `data/products.csv` — 729 products (title, brand, price, rating stats,
  description, category breadcrumbs, etc.)
- `data/reviews.csv` — 6,327 reviews (review text, rating, product link,
  no original reviewer identity)

### ⚠️ Important note on synthetic data

The raw review data has **no reviewer/user ID column** — only a per-review
ID and the product it belongs to. This makes genuine Collaborative Filtering
impossible as-is (CF requires knowing which *user* interacted with which
*items*).

Since the original scraper is unavailable and re-scraping Amazon reliably
(bot detection, ToS) wasn't practical, this project uses a **synthetic user
simulation**: (`backend/utils/generate_synthetic_users.py`) instead of real
reviewer identities. Each synthetic user is assigned a "home category"
weighted by real category popularity, and a review count following a
Zipf/power-law distribution (mirroring the real-world pattern where a small
number of users leave most reviews). ~80% of a user's reviews are drawn from
their home category, ~20% from elsewhere, to give collaborative filtering a
realistic-but-not-real signal to learn from.

**This is clearly synthetic data, generated for demonstration purposes.**
Any collaborative filtering results in this project reflect simulated
behavior, not real customer patterns. This is disclosed here and should be
disclosed again in any writeup, demo, or interview discussion of this
project.

Current synthetic user stats:
- 2,064 synthetic users across 6,320 cleaned reviews
- Average 3.06 reviews per user
- 1,693 users (82%) have 2+ reviews (i.e. usable for CF)
- Max reviews by one simulated user: 14

## Tech Stack

- **Backend:** Python, Pandas, NumPy, Scikit-learn, FastAPI, Uvicorn
- **ML/NLP:** TF-IDF, Cosine Similarity, Apriori/FP-Growth, Collaborative
  Filtering, Sentiment Analysis
- **Data format:** SQLite/MongoDB optional; currently flat CSV files

## Project Structure
Recommendation system/
├── data/
│   ├── products.csv              # raw scraped product data
│   ├── reviews.csv               # raw scraped review data
│   └── processed/
│       ├── products_clean.csv               # cleaned products
│       ├── reviews_clean.csv                # cleaned reviews (mojibake fixed)
│       └── reviews_with_synthetic_users.csv # + synthetic_user_id column
├── backend/
│   └── utils/
│       ├── data_loader.py                # cleans raw CSVs -> processed CSVs
│       └── generate_synthetic_users.py   # simulates user IDs for CF
├── models/
│   ├── content_based.py          # TF-IDF + cosine similarity model
│   └── content_similarity.pkl    # saved similarity matrix (generated, gitignored)
├── frontend/                     # (not yet built)
├── notebooks/
│   └── data_exploration.py       # initial data exploration
├── requirements.txt
└── README.md

## Setup

```bash
python -m venv venv
# Windows: venv\Scripts\Activate.ps1
# Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
```

## Running the pipeline so far

```bash
# 1. Clean raw data (fixes encoding, parses prices/ratings, builds content_text)
python backend/utils/data_loader.py

# 2. Generate synthetic user IDs for reviews (needed for collaborative filtering later)
python backend/utils/generate_synthetic_users.py

# 3. Build content-based similarity model
python models/content_based.py
```

## Known Data Limitations

- **No real user identity** in review data — collaborative filtering uses
  synthetic users (see above).
- **Duplicate/near-duplicate product listings** — some products appear
  twice under different ASINs (likely color/size variants scraped
  separately). Not deduplicated by content similarity yet.
- Dataset is scoped to a single category (men's clothing/polos appear
  heavily) rather than a full cross-category Amazon catalog.
- Collaborative filtering (20.9% explained variance with SVD) occasionally
  surfaces a thematically unrelated recommendation. This traces to the
  synthetic user simulation's built-in cross-category noise (~20% of each
  synthetic user's reviews are drawn from outside their "home category"),
  which real user data wouldn't exhibit as strongly.
## Roadmap

1. ✅ Data Collection & Cleaning
2. ✅ Content-Based Filtering
3. 🔲 Association Rules (co-occurrence based, using synthetic users)
4. 🔲 Sentiment Analysis
5. 🔲 Collaborative Filtering (synthetic users)
6. 🔲 Combine into Hybrid System
7. 🔲 Build FastAPI backend + simple frontend
8. 🔲 Deploy

## Outcome

A full-stack ML project demonstrating multiple recommendation system
techniques (content-based, association rules, sentiment-aware, and
collaborative), combined into a hybrid engine with a FastAPI backend.