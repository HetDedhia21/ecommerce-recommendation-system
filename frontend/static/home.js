const API = window.location.origin;
const PAGE_SIZE = 24;

let state = {
  offset: 0,
  category: "",
  minPrice: "",
  maxPrice: "",
  minRating: "",
  sortBy: "",
  query: "",
};

async function loadPopular() {
  const res = await fetch(`${API}/popular?top_n=8`);
  const data = await res.json();
  document.getElementById("popular-grid").innerHTML = data.map(renderProductCard).join("");
}

async function loadCategories() {
  const res = await fetch(`${API}/categories`);
  const categories = await res.json();

  const listDiv = document.getElementById("category-list");
  const allBtn = `<div class="cursor-pointer px-2 py-1 rounded-lg category-item ${state.category === "" ? "bg-brand-600 text-white" : "hover:bg-zinc-100 dark:hover:bg-zinc-800"}" data-cat="">All</div>`;
  const items = categories.map(c =>
    `<div class="cursor-pointer px-2 py-1 rounded-lg category-item flex justify-between ${state.category === c.name ? "bg-brand-600 text-white" : "hover:bg-zinc-100 dark:hover:bg-zinc-800"}" data-cat="${c.name}">
       <span>${c.name}</span><span class="text-xs opacity-60">${c.count}</span>
     </div>`
  ).join("");
  listDiv.innerHTML = allBtn + items;

  listDiv.querySelectorAll(".category-item").forEach(el => {
    el.addEventListener("click", () => {
      state.category = el.dataset.cat;
      state.offset = 0;
      fetchAndRenderProducts();
      loadCategories();
    });
  });
}

function buildQueryParams() {
  const params = new URLSearchParams();
  params.set("limit", PAGE_SIZE);
  params.set("offset", state.offset);
  if (state.category) params.set("category", state.category);
  if (state.minPrice) params.set("min_price", state.minPrice / 83);   // UI is INR, API filters in USD
  if (state.maxPrice) params.set("max_price", state.maxPrice / 83);
  if (state.minRating) params.set("min_rating", state.minRating);
  if (state.sortBy) params.set("sort_by", state.sortBy);
  return params;
}

async function fetchAndRenderProducts() {
  const grid = document.getElementById("products-grid");
  grid.innerHTML = `<p class="text-zinc-400 dark:text-zinc-500 text-sm">Loading...</p>`;

  const params = buildQueryParams();
  let url;
  if (state.query) {
    params.set("q", state.query);
    url = `${API}/products/search?${params}`;
  } else {
    url = `${API}/products?${params}`;
  }

  const res = await fetch(url);
  const data = await res.json();

  grid.innerHTML = data.items.length
    ? data.items.map(renderProductCard).join("")
    : `<p class="text-zinc-400 dark:text-zinc-500 text-sm col-span-3">No products match these filters.</p>`;

  const currentPage = Math.floor(state.offset / PAGE_SIZE) + 1;
  const totalPages = Math.max(1, Math.ceil(data.total / PAGE_SIZE));
  document.getElementById("results-count").textContent = `${data.total} products`;
  document.getElementById("page-info").textContent = `Page ${currentPage} of ${totalPages}`;
  document.getElementById("prev-page").disabled = state.offset === 0;
  document.getElementById("next-page").disabled = state.offset + PAGE_SIZE >= data.total;
}

let searchTimeout;
document.getElementById("search-box").addEventListener("input", (e) => {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => {
    state.query = e.target.value.trim();
    state.offset = 0;
    fetchAndRenderProducts();
  }, 250);
});

document.getElementById("sort-select").addEventListener("change", (e) => {
  state.sortBy = e.target.value;
  state.offset = 0;
  fetchAndRenderProducts();
});

document.getElementById("apply-filters").addEventListener("click", () => {
  state.minPrice = document.getElementById("min-price").value;
  state.maxPrice = document.getElementById("max-price").value;
  state.minRating = document.getElementById("min-rating").value;
  state.offset = 0;
  fetchAndRenderProducts();
});

document.getElementById("clear-filters").addEventListener("click", () => {
  state = { offset: 0, category: "", minPrice: "", maxPrice: "", minRating: "", sortBy: "", query: "" };
  document.getElementById("min-price").value = "";
  document.getElementById("max-price").value = "";
  document.getElementById("min-rating").value = "";
  document.getElementById("sort-select").value = "";
  document.getElementById("search-box").value = "";
  fetchAndRenderProducts();
  loadCategories();
});

document.getElementById("prev-page").addEventListener("click", () => {
  state.offset = Math.max(0, state.offset - PAGE_SIZE);
  fetchAndRenderProducts();
  window.scrollTo({ top: 0, behavior: "smooth" });
});

document.getElementById("next-page").addEventListener("click", () => {
  state.offset += PAGE_SIZE;
  fetchAndRenderProducts();
  window.scrollTo({ top: 0, behavior: "smooth" });
});

loadPopular();
loadCategories();
fetchAndRenderProducts();