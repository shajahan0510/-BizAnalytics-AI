# ============================================================
#  app.py  –  Flask REST API
#  Endpoints: /api/analytics, /api/chat, /api/predict,
#             /api/segments, /api/data, /api/health
# ============================================================

import os
import json
import requests
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from dotenv import load_dotenv

import ml_model
import chatbot
import streamer

load_dotenv()  # loads .env if present

app = Flask(__name__)
CORS(app)   # allow all origins (open for dev / adjust for prod)

# ── Supabase config (optional – falls back to CSV when not set) ─
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SUPABASE_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}


def _supabase_available() -> bool:
    return bool(SUPABASE_URL and SUPABASE_KEY)


def _fetch_supabase_sales() -> list | None:
    """Fetch all rows from the Supabase 'sales' table."""
    if not _supabase_available():
        return None
    try:
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/sales?select=*&order=date.asc",
            headers=SUPABASE_HEADERS,
            timeout=8,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        app.logger.warning(f"Supabase fetch failed – using CSV. Error: {e}")
        return None


# ─────────────────────────────────────────────────────────────
#  Routes
# ─────────────────────────────────────────────────────────────

@app.route("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "supabase_connected": _supabase_available(),
        "message": "AI Business Analytics API is running 🚀",
    })


@app.route("/api/data")
def get_data():
    """Return raw sales data (Supabase if configured, else CSV)."""
    records = _fetch_supabase_sales()
    if records is None:
        import pandas as pd
        df = pd.read_csv(
            os.path.join(os.path.dirname(__file__), "..", "data", "sales_data.csv"),
            parse_dates=["date"],
        )
        df["date"] = df["date"].dt.strftime("%Y-%m-%d")
        records = df.to_dict(orient="records")
    return jsonify({"source": "supabase" if _supabase_available() else "csv", "data": records})


@app.route("/api/analytics")
def analytics():
    """KPI summary for dashboard cards + chart series."""
    records = _fetch_supabase_sales()
    summary = ml_model.get_analytics_summary(records)

    # Also return chart-ready series from CSV for consistency
    import pandas as pd
    df = pd.read_csv(
        os.path.join(os.path.dirname(__file__), "..", "data", "sales_data.csv"),
        parse_dates=["date"],
    )
    # Monthly aggregates for charts
    monthly = df.groupby(df["date"].dt.to_period("M")).agg(
        sales=("sales", "sum"),
        profit=("profit", "sum"),
        customers=("customers", "sum"),
    ).reset_index()
    monthly["date"] = monthly["date"].astype(str)

    # Category split for pie
    cat_split = df.groupby("product_category")["sales"].sum().to_dict()
    region_split = df.groupby("region")["sales"].sum().to_dict()

    return jsonify({
        "summary": summary,
        "monthly_trend": monthly.to_dict(orient="records"),
        "category_split": cat_split,
        "region_split": region_split,
    })


@app.route("/api/predict", methods=["GET"])
def predict():
    """Return 30-day sales forecast."""
    days = request.args.get("days", 30, type=int)
    days = max(1, min(days, 365))  # clamp 1–365
    result = ml_model.predict_sales(days_ahead=days)
    return jsonify(result)


@app.route("/api/segments", methods=["GET"])
def segments():
    """Return K-Means customer segments."""
    result = ml_model.get_segments()
    return jsonify(result)


@app.route("/api/chat", methods=["POST"])
def chat():
    """NLP chatbot endpoint. Expects JSON: { "message": "..." }"""
    body = request.get_json(silent=True) or {}
    message = body.get("message", "").strip()
    if not message:
        return jsonify({"error": "message is required"}), 400
    response = chatbot.process_message(message)
    return jsonify(response)


@app.route("/api/live_event")
def live_event():
    """Generates a real-time event statelessly for serverless Vercel polling."""
    import streamer
    event = streamer.generate_single_event()
    return jsonify(event)

# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    
    print("Starting AI Business Analytics API...")
    print("   Dashboard API : http://127.0.0.1:5000/api/analytics")
    print("   Chatbot API   : http://127.0.0.1:5000/api/chat  (POST)")
    print("   Predict API   : http://127.0.0.1:5000/api/predict")
    print("   Segments API  : http://127.0.0.1:5000/api/segments")
    print("   Live Stream   : http://127.0.0.1:5000/api/stream")
    app.run(debug=False, port=5000)
