# ShopSense — ML-Powered E-commerce Recommendation Engine

A full-stack recommendation system built on real scraped Amazon product and
review data, combining six recommendation techniques into a hybrid engine,
served through a FastAPI backend and a working shopping-site frontend
(browsing, search, filters, cart, personalized recommendations).

## Live Demo

[Add your deployed link here once live]

## Screenshots

[Add 2-4 screenshots here: home page, product page, for-you page]

## What This Project Demonstrates

- **Content-Based Filtering** — TF-IDF + cosine similarity over product text
- **Association Rule Mining** — Apriori, brand-level co-occurrence patterns
- **Popularity-Based Ranking** — weighted blend of rating volume, quality,
  purchase momentum, and sentiment
- **Sentiment Analysis** — VADER, run on raw review text, cross-validated
  against star ratings
- **Collaborative Filtering** — Truncated SVD matrix factorization over a
  mean-centered user-item matrix
- **Hybrid Recommendation System** — mode-adaptive weighted blend of all of
  the above, with an audience-consistency filter to keep recommendations
  on-theme
- A real FastAPI backend (10+ endpoints) and a working frontend: browsing,
  category filters, price/rating filters, sorting, pagination, search,
  cart, and product detail pages with reviews and sentiment badges

## Tech Stack

- **Backend:** Python, FastAPI, Uvicorn, Pandas, NumPy
- **ML/NLP:** Scikit-learn (TF-IDF, cosine similarity, TruncatedSVD),
  mlxtend (Apriori/association rules), VADER (sentiment analysis)
- **Frontend:** Vanilla HTML/CSS/JS, Tailwind CSS (CDN), served as static
  files directly from FastAPI (no build step, no separate frontend server)
- **Data:** 728 real scraped Amazon products, 6,327 real reviews

## Architecture
Browser (frontend/) ──HTTP──> FastAPI (backend/main.py) ──reads──> Pickled models (models/*.pkl)
└──reads──> Processed CSVs (data/processed/)

Models are trained offline (via the scripts in `models/`) and saved as
`.pkl` files. The API loads them once at startup (`@app.on_event("startup")`)
and caches them in memory (`lru_cache`) — no retraining happens per-request.

## Project Structure
Recommendation system/
├── data/
│ ├── products.csv, reviews.csv # raw scraped data
│ └── processed/ # cleaned, enriched CSVs
├── backend/
│ ├── main.py # FastAPI app, all endpoints
│ └── utils/
│ ├── data_loader.py # cleaning: mojibake fix, parsing
│ └── generate_synthetic_users.py # synthetic user simulation
├── models/
│ ├── content_based.py # TF-IDF + cosine similarity
│ ├── association_rules.py # Apriori, brand-level
│ ├── popularity.py # weighted popularity ranking
│ ├── sentiment_analysis.py # VADER sentiment
│ ├── collaborative_filtering.py # SVD matrix factorization
│ └── hybrid.py # combines all of the above
├── frontend/
│ ├── index.html, product.html,
│ │ for-you.html, cart.html
│ └── static/ # shared JS: cart, product cards
├── requirements.txt
└── README.md

## Key Engineering Decisions

### The missing user-ID problem
The scraped review data has no reviewer identity — only a per-review ID
linked to a product. This blocks genuine Collaborative Filtering, which
needs user-item interaction history. Re-scraping Amazon reliably wasn't
practical (bot detection, ToS), so this project uses a **documented
synthetic user simulation** (`generate_synthetic_users.py`): each synthetic
user gets a "home category" weighted by real category popularity, and a
review count following a Zipf/power-law distribution (mirroring how a small
share of real users leave most reviews). ~80% of a user's reviews are drawn
from their home category, ~20% cross-category, giving collaborative
filtering a realistic-but-simulated signal.

**This is disclosed here, in-app (see the For You page), and in code
comments — any CF/association-rule results reflect simulated behavior, not
real customers.**

### Sparse rating matrix → mean-centering
An early version of Collaborative Filtering filled missing ratings with 0,
which SVD misread as "strongly disliked" rather than "unknown" (since 96%+
of the user-item matrix is empty). Fixed by mean-centering: unknown ratings
are set to 0 *relative to the global average*, not to an absolute 0. This
tripled explained variance (7.4% → 19.7%) and produced meaningfully better
recommendations.

### Audience-consistency filtering in the Hybrid system
Testing the hybrid recommender surfaced occasional cross-audience noise
(e.g. a men's-shopping profile getting a women's dress recommended) —
traced back to the synthetic layer's intentional cross-category noise.
Rather than just down-weighting Collaborative Filtering's influence (which
would undercut the point of having built it), the hybrid system filters
candidates by product audience (Men/Women/Boys/etc., parsed from category
breadcrumbs) *before* scoring — preserving CF's real signal while removing
audience-mismatched results.

### Association rules: product-level → brand-level
Product-level co-occurrence was too sparse to find real patterns (700+
distinct SKUs, max pair co-occurrence of 3 out of 1,693 baskets). Regrouped
to brand-level (285 distinct brands), which found 17 real rules, all with
lift > 1.

## API Endpoints

| Endpoint | Description |
|---|---|
| `GET /products` | Browse products — filters: category, price, rating, brand; sort; pagination |
| `GET /products/search` | Full-catalog search by title/brand, same filters as above |
| `GET /products/{asin}` | Single product detail, including image gallery + sentiment summary |
| `GET /products/{asin}/reviews` | Reviews for a product, with VADER sentiment labels |
| `GET /categories` | List of product categories with counts |
| `GET /popular` | Popularity-ranked products |
| `GET /recommendations/similar/{asin}` | Content-based: similar products |
| `GET /recommendations/for-user/{user_id}` | Personalized: CF + association + popularity |
| `GET /recommendations/hybrid` | Full hybrid — accepts `user_id`, `seed_asin`, or both |

Interactive docs available at `/docs` once running.

## Setup

```bash
python -m venv venv
# Windows: venv\Scripts\Activate.ps1
# Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
```

## Running the Full Pipeline

```bash
# 1. Clean raw data
python backend/utils/data_loader.py

# 2. Generate synthetic user IDs (for collaborative filtering)
python backend/utils/generate_synthetic_users.py

# 3. Build all recommendation models
python models/content_based.py
python models/association_rules.py
python models/popularity.py
python models/sentiment_analysis.py
python models/collaborative_filtering.py

# 4. Run the app
uvicorn backend.main:app --reload
```

Then open `http://127.0.0.1:8000/app` in your browser.

## Try It

- Browse: `http://127.0.0.1:8000/app`
- A product page: `http://127.0.0.1:8000/app/product.html?asin=B078LC7GCX`
- Personalized recs: `http://127.0.0.1:8000/app/for-you.html` (try `synth_user_2101`)

## Known Limitations

- **Synthetic user data** for collaborative filtering (see above) — not
  real customer behavior.
- **Near-duplicate product listings** — a small number of products appear
  under multiple ASINs (likely color/size variants scraped separately).
  Deduplicated in the popularity ranking by title; not deduplicated
  elsewhere.
- **Collaborative filtering explains ~20% of variance** (SVD, 20
  components) — reasonable for a 700-product, review-derived dataset, but
  occasionally still surfaces a weakly-related recommendation, traceable to
  synthetic-user cross-category noise.
- **No real checkout/payment** — the cart is a demo (client-side,
  session-only), not a real commerce flow.
- Dataset is scoped mostly to menswear/clothing categories rather than a
  full cross-category catalog.

## Roadmap

1. ✅ Data Collection & Cleaning
2. ✅ Content-Based Filtering
3. ✅ Association Rules
4. ✅ Popularity-Based Recommendation
5. ✅ Sentiment Analysis
6. ✅ Collaborative Filtering
7. ✅ Hybrid Recommendation System
8. ✅ FastAPI Backend
9. ✅ Frontend (browsing, search, filters, cart, personalization)
10. 🔲 Deployment
