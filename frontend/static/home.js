const API = "http://127.0.0.1:8000";

async function loadPopular() {
  const res = await fetch(`${API}/popular?top_n=8`);
  const data = await res.json();
  document.getElementById("popular-grid").innerHTML = data.map(renderProductCard).join("");
}

async function loadProducts(limit = 24, offset = 0) {
  const res = await fetch(`${API}/products?limit=${limit}&offset=${offset}`);
  const data = await res.json();
  document.getElementById("products-grid").innerHTML = data.map(renderProductCard).join("");
}

async function searchProducts(query) {
  if (!query) {
    loadProducts();
    return;
  }
  const res = await fetch(`${API}/products/search?q=${encodeURIComponent(query)}`);
  const data = await res.json();
  document.getElementById("products-grid").innerHTML = data.length
    ? data.map(renderProductCard).join("")
    : `<p class="text-gray-400 text-sm col-span-4">No products match "${query}".</p>`;
}

let searchTimeout;
document.getElementById("search-box").addEventListener("input", (e) => {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => searchProducts(e.target.value.trim()), 250);
});

loadPopular();
loadProducts();