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


# ---------- Startup: warm the model cache once, at boot, not on first request ----------

@app.on_event("startup")
def warm_cache():
    load_all_cached()
    print("Models loaded and cached.")


# ---------- Endpoints ----------

@app.get("/")
def root():
    return {"message": "E-commerce Recommendation API. See /docs for usage."}


@app.get("/products", response_model=list[ProductOut])
def list_products(limit: int = Query(20, le=100), offset: int = 0):
    """Browse products, paginated."""
    products = pd.read_csv("data/processed/products_clean.csv")
    page = products.iloc[offset: offset + limit]
    return page.to_dict(orient="records")


@app.get("/products/{asin}", response_model=ProductOut)
def get_product(asin: str):
    """Get a single product's details."""
    products = pd.read_csv("data/processed/products_clean.csv")
    row = products[products["asin"] == asin]
    if len(row) == 0:
        raise HTTPException(status_code=404, detail=f"Product {asin} not found")
    return row.iloc[0].to_dict()


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

@app.get("/products/search", response_model=list[ProductOut])
def search_products(q: str = Query(..., min_length=1), limit: int = Query(24, le=100)):
    """Search products by title or brand."""
    products = pd.read_csv("data/processed/products_clean.csv")
    q_lower = q.lower()
    mask = (
        products["title"].str.lower().str.contains(q_lower, na=False) |
        products["brand_name"].str.lower().str.contains(q_lower, na=False)
    )
    results = products[mask].head(limit)
    return results.to_dict(orient="records")