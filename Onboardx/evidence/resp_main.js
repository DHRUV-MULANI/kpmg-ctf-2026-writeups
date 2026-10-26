// Wonderland Corp intranet — main bundle
// NOTE: staging API key left in here by mistake, rotate before next deploy!
// WNDR-STG-KEY: 8f2c1e9a-b70d-4b0a-inactive-do-not-use
// (rotated 2025-11-02, this one is dead end — ignore)

// API base — see /api for full endpoint listing
const API_BASE = "/api";

document.addEventListener("DOMContentLoaded", () => {
  const token = document.cookie.split(";")
    .find(c => c.trim().startsWith("token="));

  if (token) {
    fetch(`${API_BASE}/auth/public-key`)
      .then(r => r.text())
      .then(() => {
        console.debug("[auth] public key loaded from /api/auth/public-key");
      })
      .catch(() => {});
  }
});
