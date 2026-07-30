const API = "http://127.0.0.1:8000";

async function loadPopular() {
  const res = await fetch(`${API}/popular?top_n=8`);
  const data = await res.json();
  document.getElementById("popular-grid").innerHTML = data.map(renderProductCard).join("");
}

async function loadProducts(limit = 20) {
  const res = await fetch(`${API}/products?limit=${limit}`);
  const data = await res.json();
  document.getElementById("products-grid").innerHTML = data.map(renderProductCard).join("");
  return data;
}

let allProducts = [];

async function init() {
  await loadPopular();
  allProducts = await loadProducts(40);
}

document.getElementById("search-box").addEventListener("input", (e) => {
  const q = e.target.value.toLowerCase();
  const filtered = allProducts.filter(p => p.title.toLowerCase().includes(q));
  document.getElementById("products-grid").innerHTML = filtered.map(renderProductCard).join("");
});

init();