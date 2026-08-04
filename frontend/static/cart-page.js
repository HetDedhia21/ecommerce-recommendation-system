function renderCart() {
  const cart = getCart();
  const itemsDiv = document.getElementById("cart-items");
  const summaryDiv = document.getElementById("cart-summary");
  summaryDiv.classList.remove("hidden");

  if (cart.length === 0) {
    itemsDiv.innerHTML = `<p class="text-zinc-400 dark:text-zinc-500 text-sm">Your cart is empty. <a href="/app" class="underline">Browse products</a>.</p>`;
    summaryDiv.classList.add("hidden");
    return;
  }

  itemsDiv.innerHTML = cart.map(item => `
    <div class="bg-white dark:bg-zinc-800 rounded-xl border border-zinc-200 dark:border-zinc-700 p-4 flex items-center gap-4">
      <img src="${item.image_url || 'https://placehold.co/80x80/f4f4f5/a1a1aa?text=No+Image'}"
           class="w-16 h-16 object-contain bg-white rounded-lg border dark:border-zinc-700" alt="${item.title}">
      <div class="flex-1">
        <p class="text-xs text-zinc-400 dark:text-zinc-500">${item.brand_name || ""}</p>
        <p class="text-sm font-medium text-zinc-900 dark:text-zinc-100 line-clamp-1">${item.title}</p>
        <p class="text-sm text-zinc-700 dark:text-zinc-300 mt-1">${formatINR(item.price_inr)}</p>
      </div>
      <input type="number" min="1" value="${item.qty}"
             onchange="updateQty('${item.asin}', parseInt(this.value)); renderCart();"
             class="w-16 border dark:border-zinc-600 dark:bg-zinc-700 dark:text-zinc-100 rounded-lg px-2 py-1 text-sm text-center">
      <button onclick="removeFromCart('${item.asin}'); renderCart();"
              class="text-red-500 text-sm hover:underline">Remove</button>
    </div>
  `).join("");

  summaryDiv.innerHTML = `
    <span class="text-sm text-zinc-500 dark:text-zinc-400">${cartCount()} item(s)</span>
    <span class="text-lg font-semibold text-zinc-900 dark:text-zinc-100">${formatINR(cartTotal())}</span>
  `;
}

renderCart();