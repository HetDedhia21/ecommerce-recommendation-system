const API = window.location.origin;

function getAsinFromUrl() {
  const params = new URLSearchParams(window.location.search);
  return params.get("asin");
}

function renderProductDetail(product) {
  const price = product.price_inr ? formatINR(product.price_inr) : "Price unavailable";
  const stars = product.rating_stars_clean ? `★ ${product.rating_stars_clean}` : "";
  const reviewCount = product.rating_count_clean ? `(${product.rating_count_clean.toLocaleString()} ratings)` : "";
  const img = product.image_url
    ? `<img src="${product.image_url}" alt="${product.title}"
         class="w-full md:w-72 h-72 object-contain bg-white rounded-xl border dark:border-zinc-700"
         onerror="this.onerror=null;this.src='https://placehold.co/300x300/f4f4f5/a1a1aa?text=No+Image';">`
    : `<div class="w-full md:w-72 h-72 bg-zinc-100 dark:bg-zinc-800 rounded-xl flex items-center justify-center text-zinc-300 dark:text-zinc-600 text-sm">No image</div>`;

  const productJson = JSON.stringify(product).replace(/'/g, "&#39;");

  let sentimentBadge = "";
  if (product.positive_pct !== null && product.positive_pct !== undefined) {
    const pct = Math.round(product.positive_pct * 100);
    const color = pct >= 70 ? "bg-brand-100 text-brand-700 dark:bg-brand-900 dark:text-brand-300" : pct >= 40 ? "bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300" : "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300";
    sentimentBadge = `<span class="text-xs px-2.5 py-1 rounded-full ${color}">${pct}% positive reviews</span>`;
  }

  document.getElementById("product-detail").innerHTML = `
    <div class="flex flex-col md:flex-row gap-6">
      ${img}
      <div class="flex-1">
        <p class="text-sm text-zinc-400 dark:text-zinc-500 mb-2">${product.brand_name || ""}</p>
        <h1 class="text-2xl font-bold text-zinc-900 dark:text-zinc-100 mb-4">${product.title}</h1>
        <div class="flex items-center gap-4 mb-3">
          <span class="text-2xl font-semibold text-zinc-900 dark:text-zinc-100">${price}</span>
          <span class="text-amber-500">${stars} <span class="text-zinc-400 dark:text-zinc-500 text-sm">${reviewCount}</span></span>
        </div>
        <div class="mb-6">${sentimentBadge}</div>
        <button onclick='addToCart(${productJson})'
                class="bg-brand-600 text-white text-sm px-6 py-2.5 rounded-lg hover:bg-brand-700">
          Add to Cart
        </button>
      </div>
    </div>
  `;
}

function renderReview(review) {
  const labelColor = review.vader_label === "positive" ? "text-brand-600 dark:text-brand-400" : review.vader_label === "negative" ? "text-red-600 dark:text-red-400" : "text-zinc-500";
  const stars = "★".repeat(Math.round(review.rating)) + "☆".repeat(5 - Math.round(review.rating));

  return `
    <div class="bg-white dark:bg-zinc-800 rounded-xl border border-zinc-200 dark:border-zinc-700 p-4">
      <div class="flex items-center justify-between mb-1">
        <span class="text-amber-500 text-sm">${stars}</span>
        <span class="text-xs font-medium ${labelColor} capitalize">${review.vader_label}</span>
      </div>
      ${review.reviewTitle ? `<p class="text-sm font-medium text-zinc-900 dark:text-zinc-100 mb-1">${review.reviewTitle}</p>` : ""}
      <p class="text-sm text-zinc-600 dark:text-zinc-400" style="display:-webkit-box;-webkit-line-clamp:4;-webkit-box-orient:vertical;overflow:hidden;">
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
    : `<p class="text-zinc-400 dark:text-zinc-500 text-sm">No reviews available.</p>`;
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
    : `<p class="text-zinc-400 dark:text-zinc-500 text-sm">No similar products found.</p>`;

  await loadReviews(asin);
}

loadProduct();