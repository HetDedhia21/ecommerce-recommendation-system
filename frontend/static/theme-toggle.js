function initTheme() {
  const saved = localStorage.getItem("shopsense_theme");
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  const isDark = saved ? saved === "dark" : prefersDark;
  document.documentElement.classList.toggle("dark", isDark);
  updateToggleIcon(isDark);
}

function toggleTheme() {
  const isDark = document.documentElement.classList.toggle("dark");
  localStorage.setItem("shopsense_theme", isDark ? "dark" : "light");
  updateToggleIcon(isDark);
}

function updateToggleIcon(isDark) {
  const btn = document.getElementById("theme-toggle");
  if (btn) btn.textContent = isDark ? "☀️" : "🌙";
}

initTheme();