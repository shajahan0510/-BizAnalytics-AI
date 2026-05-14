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


# ─────────────────────────────────────────────────────────────
#  Feature 1: Anomaly Detection (Isolation Forest)
# ─────────────────────────────────────────────────────────────

def detect_anomalies() -> dict:
    """
    Use Isolation Forest to detect anomalous sales records.
    Returns flagged records and summary statistics.
    """
    from sklearn.ensemble import IsolationForest

    df = _load_csv()

    features = df[["sales", "profit", "customers"]].values
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)

    iso_forest = IsolationForest(
        n_estimators=100,
        contamination=0.08,   # expect ~8% anomalies
        random_state=42,
    )
    labels = iso_forest.fit_predict(features_scaled)
    scores = iso_forest.decision_function(features_scaled)

    df["anomaly"] = labels          # -1 = anomaly, 1 = normal
    df["anomaly_score"] = scores    # lower = more anomalous

    anomalies = df[df["anomaly"] == -1].copy()
    anomalies["date"] = anomalies["date"].dt.strftime("%Y-%m-%d")

    return {
        "model": "Isolation Forest",
        "total_records": len(df),
        "anomaly_count": len(anomalies),
        "anomaly_pct": round(len(anomalies) / len(df) * 100, 1),
        "anomalies": anomalies[["date", "sales", "profit", "customers", "region", "product_category", "anomaly_score"]].to_dict(orient="records"),
        "summary": {
            "avg_anomaly_sales": round(float(anomalies["sales"].mean()), 2) if len(anomalies) > 0 else 0,
            "avg_normal_sales": round(float(df[df["anomaly"] == 1]["sales"].mean()), 2),
            "most_anomalous_region": anomalies["region"].mode().iloc[0] if len(anomalies) > 0 else "N/A",
            "most_anomalous_category": anomalies["product_category"].mode().iloc[0] if len(anomalies) > 0 else "N/A",
        },
    }


# ─────────────────────────────────────────────────────────────
#  Feature 2: Comparative Analytics
# ─────────────────────────────────────────────────────────────

def get_comparative_analytics(dimension: str = "region", val_a: str = "", val_b: str = "") -> dict:
    """
    Compare two values of a dimension (region or product_category).
    Returns side-by-side metrics for radar chart and KPI cards.
    """
    df = _load_csv()
    col = "region" if dimension == "region" else "product_category"

    available = sorted(df[col].unique().tolist())
    if not val_a or not val_b:
        val_a = available[0] if len(available) > 0 else ""
        val_b = available[1] if len(available) > 1 else val_a

    a_df = df[df[col] == val_a]
    b_df = df[df[col] == val_b]

    def _metrics(sub_df):
        return {
            "total_sales": round(float(sub_df["sales"].sum()), 2),
            "total_profit": round(float(sub_df["profit"].sum()), 2),
            "total_customers": int(sub_df["customers"].sum()),
            "avg_sales": round(float(sub_df["sales"].mean()), 2),
            "avg_profit": round(float(sub_df["profit"].mean()), 2),
            "avg_customers": round(float(sub_df["customers"].mean()), 1),
            "profit_margin": round(float(sub_df["profit"].sum() / sub_df["sales"].sum() * 100), 1) if sub_df["sales"].sum() > 0 else 0,
            "record_count": len(sub_df),
        }

    return {
        "dimension": dimension,
        "available_values": available,
        "comparison": {
            val_a: _metrics(a_df),
            val_b: _metrics(b_df),
        },
    }


# ─────────────────────────────────────────────────────────────
#  Feature 3: Growth Rates & Advanced Report
# ─────────────────────────────────────────────────────────────

def get_growth_rates() -> dict:
    """
    Calculate Week-over-Week and Month-over-Month growth rates.
    """
    df = _load_csv()

    # Monthly growth
    monthly = df.groupby(df["date"].dt.to_period("M")).agg(
        sales=("sales", "sum"),
        profit=("profit", "sum"),
        customers=("customers", "sum"),
    ).reset_index()
    monthly["date"] = monthly["date"].astype(str)

    mom_growth = []
    for i in range(1, len(monthly)):
        prev_s = monthly.iloc[i - 1]["sales"]
        curr_s = monthly.iloc[i]["sales"]
        prev_p = monthly.iloc[i - 1]["profit"]
        curr_p = monthly.iloc[i]["profit"]
        mom_growth.append({
            "period": monthly.iloc[i]["date"],
            "sales_growth_pct": round((curr_s - prev_s) / prev_s * 100, 1) if prev_s > 0 else 0,
            "profit_growth_pct": round((curr_p - prev_p) / prev_p * 100, 1) if prev_p > 0 else 0,
            "sales": round(float(curr_s), 2),
            "profit": round(float(curr_p), 2),
        })

    # Weekly growth
    weekly = df.groupby(df["date"].dt.isocalendar().week).agg(
        sales=("sales", "sum"),
        profit=("profit", "sum"),
    ).reset_index()

    wow_growth = []
    for i in range(1, len(weekly)):
        prev_s = weekly.iloc[i - 1]["sales"]
        curr_s = weekly.iloc[i]["sales"]
        wow_growth.append({
            "week": int(weekly.iloc[i]["week"]),
            "sales_growth_pct": round((curr_s - prev_s) / prev_s * 100, 1) if prev_s > 0 else 0,
            "sales": round(float(curr_s), 2),
        })

    return {
        "monthly_growth": mom_growth,
        "weekly_growth": wow_growth,
    }


def get_advanced_report() -> dict:
    """
    Comprehensive report data: profit margins, top/bottom performers,
    revenue breakdown, and category/region heatmap data.
    """
    df = _load_csv()

    # Profit margins by category
    cat_margins = []
    for cat in df["product_category"].unique():
        cdf = df[df["product_category"] == cat]
        cat_margins.append({
            "category": cat,
            "total_sales": round(float(cdf["sales"].sum()), 2),
            "total_profit": round(float(cdf["profit"].sum()), 2),
            "profit_margin": round(float(cdf["profit"].sum() / cdf["sales"].sum() * 100), 1) if cdf["sales"].sum() > 0 else 0,
            "avg_sales": round(float(cdf["sales"].mean()), 2),
            "record_count": len(cdf),
        })

    # Profit margins by region
    reg_margins = []
    for reg in df["region"].unique():
        rdf = df[df["region"] == reg]
        reg_margins.append({
            "region": reg,
            "total_sales": round(float(rdf["sales"].sum()), 2),
            "total_profit": round(float(rdf["profit"].sum()), 2),
            "profit_margin": round(float(rdf["profit"].sum() / rdf["sales"].sum() * 100), 1) if rdf["sales"].sum() > 0 else 0,
            "avg_sales": round(float(rdf["sales"].mean()), 2),
            "record_count": len(rdf),
        })

    # Top 5 and Bottom 5 sales days
    df_sorted = df.sort_values("sales", ascending=False)
    top5 = df_sorted.head(5).copy()
    top5["date"] = top5["date"].dt.strftime("%Y-%m-%d")
    bottom5 = df_sorted.tail(5).copy()
    bottom5["date"] = bottom5["date"].dt.strftime("%Y-%m-%d")

    # Revenue waterfall by category
    waterfall = []
    running = 0
    for cat_data in sorted(cat_margins, key=lambda x: x["total_sales"], reverse=True):
        waterfall.append({
            "label": cat_data["category"],
            "value": cat_data["total_sales"],
            "start": running,
            "end": running + cat_data["total_sales"],
        })
        running += cat_data["total_sales"]
    waterfall.append({"label": "Total", "value": running, "start": 0, "end": running})

    return {
        "category_margins": cat_margins,
        "region_margins": reg_margins,
        "top_performers": top5[["date", "sales", "profit", "customers", "region", "product_category"]].to_dict(orient="records"),
        "bottom_performers": bottom5[["date", "sales", "profit", "customers", "region", "product_category"]].to_dict(orient="records"),
        "waterfall": waterfall,
        "growth": get_growth_rates(),
    }


# ─────────────────────────────────────────────────────────────
#  Feature 5: Category-wise Demand Forecasting (Inventory)
# ─────────────────────────────────────────────────────────────

def get_category_forecast() -> dict:
    """
    Per-category sales velocity and simple demand forecast.
    Returns stock health indicators and restock recommendations.
    """
    df = _load_csv()

    categories = df["product_category"].unique().tolist()
    results = []

    for cat in categories:
        cdf = df[df["product_category"] == cat].copy()
        cdf["day_index"] = (cdf["date"] - cdf["date"].min()).dt.days

        # Velocity (avg daily sales for this category)
        avg_daily = float(cdf["sales"].mean())
        total_sales = float(cdf["sales"].sum())
        total_days = max(int(cdf["day_index"].max()), 1)

        # Simple linear forecast for next 30 days
        if len(cdf) >= 5:
            X = cdf[["day_index"]].values
            y = cdf["sales"].values
            sc = StandardScaler()
            X_sc = sc.fit_transform(X)
            lr = LinearRegression()
            lr.fit(X_sc, y)

            future = np.arange(total_days + 1, total_days + 31).reshape(-1, 1)
            future_sc = sc.transform(future)
            preds = lr.predict(future_sc)
            forecast_avg = round(float(preds.mean()), 2)
            forecast_trend = "up" if preds[-1] > preds[0] else "down"
        else:
            forecast_avg = avg_daily
            forecast_trend = "stable"

        # Stock health: based on profit margin
        margin = float(cdf["profit"].sum() / cdf["sales"].sum() * 100) if cdf["sales"].sum() > 0 else 0

        # Restock urgency
        if forecast_trend == "up" and margin > 25:
            restock = "high"
            recommendation = f"📈 Demand rising! Increase {cat} stock by 20-30%."
        elif forecast_trend == "down":
            restock = "low"
            recommendation = f"📉 Demand declining for {cat}. Reduce orders by 10-15%."
        else:
            restock = "medium"
            recommendation = f"➡️ {cat} demand is stable. Maintain current stock levels."

        results.append({
            "category": cat,
            "total_sales": round(total_sales, 2),
            "avg_daily_sales": round(avg_daily, 2),
            "record_count": len(cdf),
            "velocity_rank": 0,  # filled below
            "forecast_30d_avg": forecast_avg,
            "forecast_trend": forecast_trend,
            "profit_margin": round(margin, 1),
            "stock_health": "good" if margin > 25 else ("fair" if margin > 15 else "low"),
            "restock_urgency": restock,
            "recommendation": recommendation,
        })

    # Assign velocity ranks (1 = fastest seller)
    results.sort(key=lambda x: x["avg_daily_sales"], reverse=True)
    for i, r in enumerate(results):
        r["velocity_rank"] = i + 1

    return {
        "categories": results,
        "total_categories": len(results),
    }
