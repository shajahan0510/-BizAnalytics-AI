// ============================================================
//  config.js  –  Supabase Configuration
//  Replace the placeholder values below with your own keys
//  from https://supabase.com → Project Settings → API
// ============================================================

const SUPABASE_CONFIG = {
  url: "https://YOUR_PROJECT_ID.supabase.co",   // ← replace
  anonKey: "YOUR_SUPABASE_ANON_KEY",            // ← replace
};

// Dynamic API URL: use local Flask server in dev, and relative '/api' in production (Vercel)
const isLocalhost = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
const API_BASE = isLocalhost ? "http://127.0.0.1:5000" : "";
