const API = "http://127.0.0.1:8000";

async function loadRecommendations() {
  const userId = document.getElementById("user-input").value.trim();
  const grid = document.getElementById("recs-grid");

  if (!userId) {
    grid.innerHTML = `<p class="text-gray-400 text-sm">Enter a user ID above.</p>`;
    return;
  }

  grid.innerHTML = `<p class="text-gray-400 text-sm">Loading...</p>`;

  const res = await fetch(`${API}/recommendations/for-user/${userId}?top_n=12`);
  if (!res.ok) {
    grid.innerHTML = `<p class="text-red-500 text-sm">No recommendations found for that user ID.</p>`;
    return;
  }

  const data = await res.json();
  grid.innerHTML = data.map(renderProductCard).join("");
}

document.getElementById("load-btn").addEventListener("click", loadRecommendations);
document.getElementById("user-input").addEventListener("keypress", (e) => {
  if (e.key === "Enter") loadRecommendations();
});

// Pre-fill with a known test user for convenience
document.getElementById("user-input").value = "synth_user_2101";
loadRecommendations();