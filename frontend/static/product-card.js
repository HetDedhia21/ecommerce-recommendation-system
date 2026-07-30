function renderProductCard(product) {
  const price = product.price_value ? `$${product.price_value.toFixed(2)}` : "";
  const stars = product.rating_stars_clean ? `★ ${product.rating_stars_clean}` : "";
  const score = product.final_score ? `<span class="text-xs text-gray-400">match: ${(product.final_score * 100).toFixed(0)}%</span>` : "";

  return `
    <a href="/app/product.html?asin=${product.asin}"
       class="block bg-white rounded-xl border hover:shadow-md transition p-4">
      <p class="text-xs text-gray-400 mb-1">${product.brand_name || ""}</p>
      <p class="text-sm font-medium text-gray-900 line-clamp-2 mb-2" style="display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;">
        ${product.title}
      </p>
      <div class="flex items-center justify-between text-sm">
        <span class="text-gray-700">${price}</span>
        <span class="text-amber-600">${stars}</span>
      </div>
      ${score ? `<div class="mt-1">${score}</div>` : ""}
    </a>
  `;
}