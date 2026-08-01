const CART_KEY = "shopsense_cart";

function getCart() {
  const raw = sessionStorage.getItem(CART_KEY);
  return raw ? JSON.parse(raw) : [];
}

function saveCart(cart) {
  sessionStorage.setItem(CART_KEY, JSON.stringify(cart));
  updateCartBadge();
}

function addToCart(product) {
  const cart = getCart();
  const existing = cart.find(item => item.asin === product.asin);
  if (existing) {
    existing.qty += 1;
  } else {
    cart.push({
      asin: product.asin,
      title: product.title,
      brand_name: product.brand_name,
      price_value: product.price_value,
      image_url: product.image_url,
      qty: 1,
    });
  }
  saveCart(cart);
}

function removeFromCart(asin) {
  saveCart(getCart().filter(item => item.asin !== asin));
}

function updateQty(asin, qty) {
  const cart = getCart();
  const item = cart.find(i => i.asin === asin);
  if (item) {
    item.qty = Math.max(1, qty);
    saveCart(cart);
  }
}

function cartTotal() {
  return getCart().reduce((sum, item) => sum + (item.price_value || 0) * item.qty, 0);
}

function cartCount() {
  return getCart().reduce((sum, item) => sum + item.qty, 0);
}

function updateCartBadge() {
  const badge = document.getElementById("cart-badge");
  if (badge) {
    const count = cartCount();
    badge.textContent = count;
    badge.classList.toggle("hidden", count === 0);
  }
}

document.addEventListener("DOMContentLoaded", updateCartBadge);