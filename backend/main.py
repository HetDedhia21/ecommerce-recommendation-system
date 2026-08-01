from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
import pandas as pd

from models.hybrid import hybrid_recommend, get_similar_products, load_all_cached
from models.popularity import get_top_products
app = FastAPI(title="E-commerce Recommendation API", version="1.0")

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

import ast
from functools import lru_cache

def compute_audience(breadcrumb):
    if pd.isna(breadcrumb):
        return "Unknown"
    parts = [p.strip() for p in str(breadcrumb).split("›")]
    return parts[1] if len(parts) > 1 else "Unknown"


def parse_all_images(all_images_str, max_images=6):
    if pd.isna(all_images_str):
        return []
    try:
        images = ast.literal_eval(all_images_str)
    except (ValueError, SyntaxError):
        return []
    if not isinstance(images, list):
        return []
    clean = [u for u in images if isinstance(u, str) and u.startswith("http") and "play-button-overlay" not in u]
    return clean[:max_images]


@lru_cache(maxsize=1)
def get_products_with_audience():
    df = pd.read_csv("data/processed/products_clean.csv")
    df["audience"] = df["breadcrumbs"].apply(compute_audience)
    return df

@app.get("/app")
def serve_frontend():
    return FileResponse("frontend/index.html")

@app.get("/app/{page_name}")
def serve_frontend_page(page_name: str):
    return FileResponse(f"frontend/{page_name}")


# ---------- Response models (define the exact JSON shape we return) ----------

class RecommendationItem(BaseModel):
    asin: str
    title: str
    brand_name: Optional[str] = None
    image_url: Optional[str] = None
    final_score: Optional[float] = None


class ProductOut(BaseModel):    
    asin: str
    title: str
    brand_name: Optional[str] = None
    price_value: Optional[float] = None
    image_url: Optional[str] = None
    rating_stars_clean: Optional[float] = None
    rating_count_clean: Optional[int] = None


class ProductListResponse(BaseModel):
    total: int
    items: list[ProductOut]


class ProductDetailOut(ProductOut):
    images: list[str] = []
    avg_sentiment: Optional[float] = None
    positive_pct: Optional[float] = None


class ReviewOut(BaseModel):
    reviewTitle: Optional[str] = None
    reviewText: str
    rating: float
    vader_label: str

# ---------- Startup: warm the model cache once, at boot, not on first request ----------

@app.on_event("startup")
def warm_cache():
    load_all_cached()
    print("Models loaded and cached.")

# ---------- Endpoints ----------

@app.get("/")
def root():
    return {"message": "E-commerce Recommendation API. See /docs for usage."}


@app.get("/products", response_model=ProductListResponse)
def list_products(
    limit: int = Query(24, le=100),
    offset: int = 0,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    brand: Optional[str] = None,
    sort_by: Optional[str] = None,
):
    df = get_products_with_audience()

    if category:
        df = df[df["audience"] == category]
    if min_price is not None:
        df = df[df["price_value"] >= min_price]
    if max_price is not None:
        df = df[df["price_value"] <= max_price]
    if min_rating is not None:
        df = df[df["rating_stars_clean"] >= min_rating]
    if brand:
        df = df[df["brand_name"].str.lower() == brand.lower()]

    if sort_by == "price_asc":
        df = df.sort_values("price_value", ascending=True, na_position="last")
    elif sort_by == "price_desc":
        df = df.sort_values("price_value", ascending=False, na_position="last")
    elif sort_by == "rating_desc":
        df = df.sort_values("rating_stars_clean", ascending=False, na_position="last")
    elif sort_by == "popularity":
        df = df.sort_values("rating_count_clean", ascending=False, na_position="last")

    total = len(df)
    page = df.iloc[offset: offset + limit]
    return {"total": total, "items": page.to_dict(orient="records")}    


@app.get("/products/search", response_model=ProductListResponse)
def search_products(
    q: str = Query(..., min_length=1),
    limit: int = Query(24, le=100),
    offset: int = 0,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    sort_by: Optional[str] = None,
):
    df = get_products_with_audience()
    q_lower = q.lower()
    mask = (
        df["title"].str.lower().str.contains(q_lower, na=False) |
        df["brand_name"].str.lower().str.contains(q_lower, na=False)
    )
    df = df[mask]

    if category:
        df = df[df["audience"] == category]
    if min_price is not None:
        df = df[df["price_value"] >= min_price]
    if max_price is not None:
        df = df[df["price_value"] <= max_price]
    if min_rating is not None:
        df = df[df["rating_stars_clean"] >= min_rating]

    if sort_by == "price_asc":
        df = df.sort_values("price_value", ascending=True, na_position="last")
    elif sort_by == "price_desc":
        df = df.sort_values("price_value", ascending=False, na_position="last")
    elif sort_by == "rating_desc":
        df = df.sort_values("rating_stars_clean", ascending=False, na_position="last")

    total = len(df)
    page = df.iloc[offset: offset + limit]
    return {"total": total, "items": page.to_dict(orient="records")}


@app.get("/products/{asin}", response_model=ProductDetailOut)
def get_product(asin: str):
    df = get_products_with_audience()
    row = df[df["asin"] == asin]
    if len(row) == 0:
        raise HTTPException(status_code=404, detail=f"Product {asin} not found")

    product = row.iloc[0].to_dict()
    product["images"] = parse_all_images(row.iloc[0].get("all_images"))

    try:
        sentiment_df = pd.read_csv("data/processed/product_sentiment_summary.csv")
        srow = sentiment_df[sentiment_df["productASIN"] == asin]
        if len(srow) > 0:
            product["avg_sentiment"] = float(srow.iloc[0]["avg_sentiment"])
            product["positive_pct"] = float(srow.iloc[0]["positive_pct"])
    except FileNotFoundError:
        pass

    return product


@app.get("/recommendations/similar/{asin}", response_model=list[RecommendationItem])
def similar_products(asin: str, top_n: int = Query(10, le=50)):
    """Content-based: products similar to a given product."""
    try:
        result, _ = hybrid_recommend(seed_asin=asin, top_n=top_n)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if len(result) == 0:
        raise HTTPException(status_code=404, detail=f"No recommendations found for {asin}")
    return result.to_dict(orient="records")


@app.get("/recommendations/for-user/{user_id}", response_model=list[RecommendationItem])
def personalized_recommendations(user_id: str, top_n: int = Query(10, le=50)):
    """Personalized: collaborative filtering + association + popularity for a known user."""
    try:
        result, _ = hybrid_recommend(user_id=user_id, top_n=top_n)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if len(result) == 0:
        raise HTTPException(status_code=404, detail=f"No recommendations found for user {user_id}")
    return result.to_dict(orient="records")


@app.get("/recommendations/hybrid", response_model=list[RecommendationItem])
def full_hybrid_recommendations(
    user_id: Optional[str] = None,
    seed_asin: Optional[str] = None,
    top_n: int = Query(10, le=50),
):
    """Full hybrid: pass user_id, seed_asin, or both."""
    if not user_id and not seed_asin:
        raise HTTPException(status_code=400, detail="Provide at least user_id or seed_asin")
    result, weights_used = hybrid_recommend(user_id=user_id, seed_asin=seed_asin, top_n=top_n)
    return result.to_dict(orient="records")


@app.get("/popular", response_model=list[ProductOut])
def popular_products(top_n: int = Query(10, le=50)):
    """Popularity-based / trending products."""
    result = get_top_products(top_n)
    return result[["asin", "title", "brand_name", "price_value", "image_url", "rating_stars_clean", "rating_count_clean"]].to_dict(
        orient="records"
    )


@app.get("/categories")
def list_categories():
    df = get_products_with_audience()
    counts = df[df["audience"] != "Unknown"]["audience"].value_counts()
    return [{"name": name, "count": int(count)} for name, count in counts.items()]


@app.get("/products/{asin}/reviews", response_model=list[ReviewOut])
def get_product_reviews(asin: str, limit: int = Query(5, le=20)):
    reviews = pd.read_csv("data/processed/reviews_with_sentiment.csv")
    product_reviews = reviews[reviews["productASIN"] == asin]
    if "helpfulVoteCount" in product_reviews.columns:
        product_reviews = product_reviews.sort_values("helpfulVoteCount", ascending=False)
    return product_reviews.head(limit).to_dict(orient="records")