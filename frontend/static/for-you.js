const API = "http://127.0.0.1:8000";
let selectedUserId = null;

async function loadDemoUsers() {
  const res = await fetch(`${API}/demo-users`);
  const users = await res.json();

  document.getElementById("user-chips").innerHTML = users.map(u => `
    <button data-user="${u.user_id}"
            class="user-chip px-4 py-2 rounded-full text-sm border transition-colors
                   ${u.user_id === selectedUserId
                     ? 'bg-brand-600 text-white border-brand-600'
                     : 'bg-white dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 border-zinc-200 dark:border-zinc-700 hover:border-brand-400'}">
      ${u.display_name}
    </button>
  `).join("");

  document.querySelectorAll(".user-chip").forEach(btn => {
    btn.addEventListener("click", () => {
      selectedUserId = btn.dataset.user;
      loadDemoUsers();
      loadRecommendations();
    });
  });

  if (!selectedUserId && users.length > 0) {
    selectedUserId = users[0].user_id;
    loadDemoUsers();
    loadRecommendations();
  }
}

async function loadRecommendations() {
  const grid = document.getElementById("recs-grid");
  if (!selectedUserId) return;

  grid.innerHTML = `<p class="text-zinc-400 dark:text-zinc-500 text-sm">Loading...</p>`;

  const res = await fetch(`${API}/recommendations/for-user/${selectedUserId}?top_n=12`);
  if (!res.ok) {
    grid.innerHTML = `<p class="text-red-500 text-sm">No recommendations found.</p>`;
    return;
  }

  const data = await res.json();
  grid.innerHTML = data.map(renderProductCard).join("");
}

loadDemoUsers();