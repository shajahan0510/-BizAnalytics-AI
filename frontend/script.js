// ============================================================
//  script.js  –  Shared Utilities + Auth Guard
// ============================================================

/* ── Auth helpers ─────────────────────────────────────────── */

/** Save minimal session to localStorage */
function saveSession(email) {
  localStorage.setItem("ab_user", JSON.stringify({ email, loggedIn: true }));
}

/** Get current session; returns null if not logged in */
function getSession() {
  try {
    return JSON.parse(localStorage.getItem("ab_user")) || null;
  } catch {
    return null;
  }
}

/** Clear session and redirect to login */
function logout() {
  localStorage.removeItem("ab_user");
  window.location.href = "login.html";
}

/**
 * Call on protected pages.
 * Redirects to login.html if no session exists.
 */
function requireAuth() {
  const session = getSession();
  if (!session || !session.loggedIn) {
    window.location.href = "login.html";
    return null;
  }
  return session;
}

/** Populate the navbar user display */
function renderNavUser() {
  const session = getSession();
  if (!session) return;
  const nameEl = document.getElementById("nav-user-name");
  const avatarEl = document.getElementById("nav-avatar");
  if (nameEl) nameEl.textContent = session.email.split("@")[0];
  if (avatarEl) avatarEl.textContent = session.email[0].toUpperCase();
}

/* ── API helpers ──────────────────────────────────────────── */

async function apiFetch(path, options = {}) {
  const resp = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!resp.ok) throw new Error(`API error ${resp.status}: ${resp.statusText}`);
  return resp.json();
}

/* ── Number formatting ────────────────────────────────────── */

function formatCurrency(n) {
  if (n >= 1_000_000) return `₹${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000)     return `₹${(n / 1_000).toFixed(1)}K`;
  return `₹${n.toFixed(0)}`;
}

function formatNumber(n) {
  return new Intl.NumberFormat("en-IN").format(Math.round(n));
}

/* ── Toast notification ───────────────────────────────────── */

function showToast(msg, type = "info") {
  const existing = document.getElementById("global-toast");
  if (existing) existing.remove();

  const toast = document.createElement("div");
  toast.id = "global-toast";
  const colors = { info: "#3b82f6", success: "#10b981", error: "#f43f5e", warn: "#f59e0b" };
  Object.assign(toast.style, {
    position: "fixed", bottom: "1.5rem", right: "1.5rem", zIndex: "9999",
    padding: "0.85rem 1.25rem",
    background: "rgba(15,22,40,0.95)",
    border: `1px solid ${colors[type] || colors.info}`,
    borderRadius: "12px", color: "#f1f5f9",
    fontSize: "0.875rem", fontFamily: "'Inter', sans-serif",
    boxShadow: "0 8px 32px rgba(0,0,0,0.4)",
    animation: "fadeIn 0.3s ease",
    maxWidth: "320px", lineHeight: "1.5",
  });
  toast.textContent = msg;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

/* ── Chart.js global defaults ─────────────────────────────── */

if (typeof Chart !== "undefined") {
  Chart.defaults.color = "#94a3b8";
  Chart.defaults.borderColor = "rgba(255,255,255,0.06)";
  Chart.defaults.font.family = "'Inter', sans-serif";
  Chart.defaults.plugins.legend.labels.usePointStyle = true;
  Chart.defaults.plugins.legend.labels.padding = 16;
  Chart.defaults.plugins.tooltip.backgroundColor = "rgba(15,22,40,0.95)";
  Chart.defaults.plugins.tooltip.borderColor = "rgba(255,255,255,0.10)";
  Chart.defaults.plugins.tooltip.borderWidth = 1;
  Chart.defaults.plugins.tooltip.padding = 12;
  Chart.defaults.plugins.tooltip.cornerRadius = 10;
  Chart.defaults.plugins.tooltip.titleFont = { weight: "700", size: 13 };
}

/* ── Auto-apply auth guard on page load ───────────────────── */
document.addEventListener("DOMContentLoaded", () => {
  const page = document.body.dataset.page;
  if (page === "login" || page === "register") return; // public
  requireAuth(); // redirect if not logged in
  renderNavUser();

  // Wire logout buttons
  document.querySelectorAll(".logout-btn, #logout-btn").forEach(btn => {
    btn.addEventListener("click", logout);
  });
});
