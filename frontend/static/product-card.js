function renderProductCard(product) {
  const price = product.price_inr ? formatINR(product.price_inr) : "";
  const stars = product.rating_stars_clean ? `★ ${product.rating_stars_clean}` : "";
  const score = product.final_score ? `<span class="text-xs text-zinc-400 dark:text-zinc-500">${(product.final_score * 100).toFixed(0)}% match</span>` : "";
  const img = product.image_url
    ? `<img src="${product.image_url}" alt="${product.title}" loading="lazy"
         class="w-full h-40 object-contain bg-white rounded-lg mb-3"
         onerror="this.onerror=null;this.src='https://placehold.co/300x300/f4f4f5/a1a1aa?text=No+Image';">`
    : `<div class="w-full h-40 bg-zinc-100 dark:bg-zinc-800 rounded-lg mb-3 flex items-center justify-center text-zinc-300 dark:text-zinc-600 text-xs">No image</div>`;

  const productJson = JSON.stringify(product).replace(/'/g, "&#39;");

  return `
    <div class="bg-white dark:bg-zinc-800 rounded-xl border border-zinc-200 dark:border-zinc-700 hover:border-zinc-300 dark:hover:border-zinc-600 hover:shadow-lg transition-all duration-150 p-3 group">
      <a href="/app/product.html?asin=${product.asin}">
        ${img}
        <p class="text-[11px] uppercase tracking-wide text-zinc-400 dark:text-zinc-500 mb-1">${product.brand_name || ""}</p>
        <p class="text-sm font-medium text-zinc-900 dark:text-zinc-100 mb-2 group-hover:text-brand-700 dark:group-hover:text-brand-500"
           style="display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;">
          ${product.title}
        </p>
        <div class="flex items-center justify-between text-sm">
          <span class="text-zinc-900 dark:text-zinc-100 font-semibold">${price}</span>
          <span class="text-amber-500 text-xs">${stars}</span>
        </div>
        ${score ? `<div class="mt-1.5">${score}</div>` : ""}
      </a>
      <button onclick='addToCart(${productJson}); event.stopPropagation();'
              class="w-full mt-2.5 bg-brand-600 text-white text-xs py-1.5 rounded-lg hover:bg-brand-700">
        Add to Cart
      </button>
    </div>
  `;
}