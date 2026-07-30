function renderProductCard(product) {
  const price = product.price_value ? `$${product.price_value.toFixed(2)}` : "";
  const stars = product.rating_stars_clean ? `★ ${product.rating_stars_clean}` : "";
  const score = product.final_score ? `<span class="text-xs text-gray-400">${(product.final_score * 100).toFixed(0)}% match</span>` : "";
  const img = product.image_url
    ? `<img src="${product.image_url}" alt="${product.title}" loading="lazy"
         class="w-full h-40 object-contain bg-white rounded-lg mb-3"
         onerror="this.onerror=null;this.src='https://placehold.co/300x300/f3f4f6/9ca3af?text=No+Image';">`
    : `<div class="w-full h-40 bg-gray-100 rounded-lg mb-3 flex items-center justify-center text-gray-300 text-xs">No image</div>`;

  return `
    <a href="/app/product.html?asin=${product.asin}"
       class="block bg-white rounded-xl border border-gray-200 hover:border-gray-300 hover:shadow-lg transition-all duration-150 p-3 group">
      ${img}
      <p class="text-[11px] uppercase tracking-wide text-gray-400 mb-1">${product.brand_name || ""}</p>
      <p class="text-sm font-medium text-gray-900 mb-2 group-hover:text-gray-700"
         style="display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;">
        ${product.title}
      </p>
      <div class="flex items-center justify-between text-sm">
        <span class="text-gray-900 font-semibold">${price}</span>
        <span class="text-amber-500 text-xs">${stars}</span>
      </div>
      ${score ? `<div class="mt-1.5">${score}</div>` : ""}
    </a>
  `;
}