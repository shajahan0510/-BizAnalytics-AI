# ============================================================
#  ml_model.py  –  Machine Learning Engine
#  Linear Regression (sales forecast) + K-Means (segmentation)
# ============================================================

import os
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

# ── Path to CSV (fall-back when Supabase is not configured yet)
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "sales_data.csv")


def _load_csv() -> pd.DataFrame:
    """Load and return the local CSV as a DataFrame."""
    df = pd.read_csv(DATA_PATH, parse_dates=["date"])
    df.sort_values("date", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


# ── Singleton model state ─────────────────────────────────────
_reg_model: LinearRegression | None = None
_scaler: StandardScaler | None = None
_kmeans: KMeans | None = None
_df_cache: pd.DataFrame | None = None


def _ensure_models():
    """Train (or load from cache) both models."""
    global _reg_model, _scaler, _kmeans, _df_cache

    if _reg_model is not None:
        return  # already trained

    df = _load_csv()

    # ── 1. Linear Regression for Sales Prediction ────────────
    # Feature: integer day index from the start date
    df["day_index"] = (df["date"] - df["date"].min()).dt.days
    X = df[["day_index"]].values
    y = df["sales"].values

    _scaler = StandardScaler()
    X_scaled = _scaler.fit_transform(X)

    _reg_model = LinearRegression()
    _reg_model.fit(X_scaled, y)

    # ── 2. K-Means Customer Segmentation ─────────────────────
    seg_features = df[["customers", "profit"]].values
    seg_scaler = StandardScaler()
    seg_scaled = seg_scaler.fit_transform(seg_features)

    _kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    _kmeans.fit(seg_scaled)

    # Save cache AFTER all columns are added
    _df_cache = df.copy()


# ─────────────────────────────────────────────────────────────
#  Public API
# ─────────────────────────────────────────────────────────────

def predict_sales(days_ahead: int = 30) -> dict:
    """
    Predict future daily sales for the next `days_ahead` days.
    Returns a dict with dates and predicted values.
    """
    _ensure_models()
    df = _df_cache

    last_day = int(df["day_index"].max())
    future_indices = np.arange(last_day + 1, last_day + days_ahead + 1).reshape(-1, 1)
    future_scaled = _scaler.transform(future_indices)
    predictions = _reg_model.predict(future_scaled)

    base_date = df["date"].min()
    future_dates = [
        (base_date + pd.Timedelta(days=int(i))).strftime("%Y-%m-%d")
        for i in future_indices.flatten()
    ]

    return {
        "model": "Linear Regression",
        "days_ahead": days_ahead,
        "predictions": [
            {"date": d, "predicted_sales": round(float(v), 2)}
            for d, v in zip(future_dates, predictions)
        ],
        "summary": {
            "avg_predicted_sales": round(float(predictions.mean()), 2),
            "min_predicted_sales": round(float(predictions.min()), 2),
            "max_predicted_sales": round(float(predictions.max()), 2),
        },
    }


def get_segments() -> dict:
    """
    Return customer segments identified by K-Means clustering.
    """
    _ensure_models()
    df = _load_csv()  # always fresh, avoids stale cache issues

    seg_scaler = StandardScaler()
    seg_scaled = seg_scaler.fit_transform(df[["customers", "profit"]].values)
    labels = _kmeans.predict(seg_scaled)
    df["segment"] = labels

    segment_summary = []
    names = ["Premium", "Standard", "Entry-Level"]
    for i in range(3):
        seg_df = df[df["segment"] == i]
        segment_summary.append({
            "segment_id": i,
            "name": names[i],
            "count": len(seg_df),
            "avg_customers": round(seg_df["customers"].mean(), 1),
            "avg_profit": round(seg_df["profit"].mean(), 2),
            "avg_sales": round(seg_df["sales"].mean(), 2),
        })

    return {
        "model": "K-Means Clustering (k=3)",
        "segments": segment_summary,
    }


def get_analytics_summary(records: list | None = None) -> dict:
    """
    Compute KPI summary from CSV (or supplied records list).
    """
    if records:
        df = pd.DataFrame(records)
    else:
        df = _load_csv()

    return {
        "total_sales": round(float(df["sales"].sum()), 2),
        "total_profit": round(float(df["profit"].sum()), 2),
        "total_customers": int(df["customers"].sum()),
        "avg_daily_sales": round(float(df["sales"].mean()), 2),
        "avg_daily_profit": round(float(df["profit"].mean()), 2),
        "best_sales_day": pd.to_datetime(df.loc[df["sales"].idxmax(), "date"]).strftime("%Y-%m-%d") if "date" in df.columns else "N/A",
        "best_sales_value": round(float(df["sales"].max()), 2),
        "record_count": len(df),
    }
