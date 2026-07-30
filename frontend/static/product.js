const API = "http://127.0.0.1:8000";

function getAsinFromUrl() {
  const params = new URLSearchParams(window.location.search);
  return params.get("asin");
}

function renderProductDetail(product) {
  const price = product.price_value ? `$${product.price_value.toFixed(2)}` : "Price unavailable";
  const stars = product.rating_stars_clean ? `★ ${product.rating_stars_clean}` : "";
  const reviewCount = product.rating_count_clean ? `(${product.rating_count_clean.toLocaleString()} ratings)` : "";

  document.getElementById("product-detail").innerHTML = `
    <p class="text-sm text-gray-400 mb-2">${product.brand_name || ""}</p>
    <h1 class="text-2xl font-bold text-gray-900 mb-4">${product.title}</h1>
    <div class="flex items-center gap-4 mb-4">
      <span class="text-2xl font-semibold text-gray-900">${price}</span>
      <span class="text-amber-600">${stars} <span class="text-gray-400 text-sm">${reviewCount}</span></span>
    </div>
  `;
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
}

loadProduct();