const API = "http://127.0.0.1:8000";

function getAsinFromUrl() {
  const params = new URLSearchParams(window.location.search);
  return params.get("asin");
}

function renderProductDetail(product) {
  const price = product.price_value ? `$${product.price_value.toFixed(2)}` : "Price unavailable";
  const stars = product.rating_stars_clean ? `★ ${product.rating_stars_clean}` : "";
  const reviewCount = product.rating_count_clean ? `(${product.rating_count_clean.toLocaleString()} ratings)` : "";
  const img = product.image_url
    ? `<img src="${product.image_url}" alt="${product.title}"
         class="w-full md:w-72 h-72 object-contain bg-white rounded-xl border"
         onerror="this.onerror=null;this.src='https://placehold.co/300x300/f3f4f6/9ca3af?text=No+Image';">`
    : `<div class="w-full md:w-72 h-72 bg-gray-100 rounded-xl flex items-center justify-center text-gray-300 text-sm">No image</div>`;

  const productJson = JSON.stringify(product).replace(/'/g, "&#39;");

  let sentimentBadge = "";
  if (product.positive_pct !== null && product.positive_pct !== undefined) {
    const pct = Math.round(product.positive_pct * 100);
    const color = pct >= 70 ? "bg-green-100 text-green-700" : pct >= 40 ? "bg-amber-100 text-amber-700" : "bg-red-100 text-red-700";
    sentimentBadge = `<span class="text-xs px-2.5 py-1 rounded-full ${color}">${pct}% positive reviews</span>`;
  }

  document.getElementById("product-detail").innerHTML = `
    <div class="flex flex-col md:flex-row gap-6">
      ${img}
      <div class="flex-1">
        <p class="text-sm text-gray-400 mb-2">${product.brand_name || ""}</p>
        <h1 class="text-2xl font-bold text-gray-900 mb-4">${product.title}</h1>
        <div class="flex items-center gap-4 mb-3">
          <span class="text-2xl font-semibold text-gray-900">${price}</span>
          <span class="text-amber-500">${stars} <span class="text-gray-400 text-sm">${reviewCount}</span></span>
        </div>
        <div class="mb-6">${sentimentBadge}</div>
        <button onclick='addToCart(${productJson})'
                class="bg-gray-900 text-white text-sm px-6 py-2.5 rounded-lg hover:bg-gray-700">
          Add to Cart
        </button>
      </div>
    </div>
  `;
}

function renderReview(review) {
  const labelColor = review.vader_label === "positive" ? "text-green-600" : review.vader_label === "negative" ? "text-red-600" : "text-gray-500";
  const stars = "★".repeat(Math.round(review.rating)) + "☆".repeat(5 - Math.round(review.rating));

  return `
    <div class="bg-white rounded-xl border p-4">
      <div class="flex items-center justify-between mb-1">
        <span class="text-amber-500 text-sm">${stars}</span>
        <span class="text-xs font-medium ${labelColor} capitalize">${review.vader_label}</span>
      </div>
      ${review.reviewTitle ? `<p class="text-sm font-medium text-gray-900 mb-1">${review.reviewTitle}</p>` : ""}
      <p class="text-sm text-gray-600" style="display:-webkit-box;-webkit-line-clamp:4;-webkit-box-orient:vertical;overflow:hidden;">
        ${review.reviewText}
      </p>
    </div>
  `;
}

async function loadReviews(asin) {
  const res = await fetch(`${API}/products/${asin}/reviews?limit=6`);
  const reviews = await res.json();
  document.getElementById("reviews-list").innerHTML = reviews.length
    ? `<div class="grid grid-cols-1 md:grid-cols-2 gap-3">${reviews.map(renderReview).join("")}</div>`
    : `<p class="text-gray-400 text-sm">No reviews available.</p>`;
}

async function loadProduct() {
  const asin = getAsinFromUrl();
  if (!asin) {
    document.getElementById("product-detail").innerHTML = `<p class="text-red-500">No product specified.</p>`;
    return;
  }

  const res = await fetch(`${API}/products/${asin}`);
  if (!res.ok) {
    document.getElementById("product-detail").innerHTML = `<p class="text-red-500">Product not found.</p>`;
    return;
  }
  const product = await res.json();
  renderProductDetail(product);

  const simRes = await fetch(`${API}/recommendations/similar/${asin}?top_n=8`);
  const similar = await simRes.json();
  document.getElementById("similar-grid").innerHTML = similar.length
    ? similar.map(renderProductCard).join("")
    : `<p class="text-gray-400 text-sm">No similar products found.</p>`;

  await loadReviews(asin);
}

loadProduct();