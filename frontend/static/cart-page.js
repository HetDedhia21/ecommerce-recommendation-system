function renderCart() {
  const cart = getCart();
  const itemsDiv = document.getElementById("cart-items");
  const summaryDiv = document.getElementById("cart-summary");
  summaryDiv.classList.remove("hidden");    

  if (cart.length === 0) {
    itemsDiv.innerHTML = `<p class="text-gray-400 text-sm">Your cart is empty. <a href="/app" class="underline">Browse products</a>.</p>`;
    summaryDiv.classList.add("hidden");
    return;
  }

  itemsDiv.innerHTML = cart.map(item => `
    <div class="bg-white rounded-xl border p-4 flex items-center gap-4">
      <img src="${item.image_url || 'https://placehold.co/80x80/f3f4f6/9ca3af?text=No+Image'}"
           class="w-16 h-16 object-contain bg-white rounded-lg border" alt="${item.title}">
      <div class="flex-1">
        <p class="text-xs text-gray-400">${item.brand_name || ""}</p>
        <p class="text-sm font-medium text-gray-900 line-clamp-1">${item.title}</p>
        <p class="text-sm text-gray-700 mt-1">$${(item.price_value || 0).toFixed(2)}</p>
      </div>
      <input type="number" min="1" value="${item.qty}"
             onchange="updateQty('${item.asin}', parseInt(this.value)); renderCart();"
             class="w-16 border rounded-lg px-2 py-1 text-sm text-center">
      <button onclick="removeFromCart('${item.asin}'); renderCart();"
              class="text-red-500 text-sm hover:underline">Remove</button>
    </div>
  `).join("");

  summaryDiv.innerHTML = `
    <span class="text-sm text-gray-500">${cartCount()} item(s)</span>
    <span class="text-lg font-semibold text-gray-900">$${cartTotal().toFixed(2)}</span>
  `;
}

renderCart();