# ============================================================
#  chatbot.py  –  NLP Intent Router + Response Engine
#  Rule-based NLP using regex patterns to answer business Q&A
# ============================================================

import re
import os
import json
import pandas as pd

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "sales_data.csv")


def _load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH, parse_dates=["date"])
    df.sort_values("date", inplace=True)
    return df


# ── Intent patterns (regex → handler key) ────────────────────
INTENTS = [
    (r"total\s+sales|sum.*sales|sales\s+total",           "total_sales"),
    (r"total\s+profit|profit\s+total|sum.*profit",        "total_profit"),
    (r"total\s+customers|customers\s+total|how many cust","total_customers"),
    (r"average\s+sales|avg\s+sales|mean\s+sales",         "avg_sales"),
    (r"average\s+profit|avg\s+profit|mean\s+profit",      "avg_profit"),
    (r"best\s+(day|date)|highest\s+sales|top\s+sales",    "best_day"),
    (r"worst\s+(day|date)|lowest\s+sales|min\s+sales",    "worst_day"),
    (r"predict|forecast|future|next\s+\d+|upcoming",      "predict"),
    (r"segment|cluster|customer\s+tier|group",            "segment"),
    (r"profit\s+on|sales\s+on|data\s+(for|on)\s+\d{4}",  "date_lookup"),
    (r"trend|monthly|by\s+month|month(?:ly)?\s+sales",    "monthly_trend"),
    (r"region|north|south|east|west|location",            "region_breakdown"),
    (r"categor|product|what.*sell|top.*product",          "category_breakdown"),
    (r"hello|hi|hey|greet",                               "greet"),
    (r"help|what can you|capabilities|commands",           "help"),
]


def _detect_intent(msg: str) -> str:
    msg_lower = msg.lower()
    for pattern, intent in INTENTS:
        if re.search(pattern, msg_lower):
            return intent
    return "unknown"


def _extract_date(msg: str) -> str | None:
    """Try to pull a YYYY-MM-DD or MM/DD/YYYY date from the message."""
    m = re.search(r"\d{4}-\d{2}-\d{2}", msg)
    if m:
        return m.group()
    m = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", msg)
    if m:
        return f"{m.group(3)}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
    return None


# ── Intent Handlers ───────────────────────────────────────────

def _handle(intent: str, msg: str, df: pd.DataFrame) -> dict:
    if intent == "greet":
        return {
            "reply": "👋 Hello! I'm your AI Business Analyst. Ask me about sales, profit, customers, predictions, or trends!",
            "data": None,
        }

    if intent == "help":
        return {
            "reply": (
                "🤖 **I can answer questions like:**\n"
                "• *What is total sales?*\n"
                "• *Show me total profit*\n"
                "• *Average daily sales?*\n"
                "• *Best sales day?*\n"
                "• *Profit on 2024-03-15*\n"
                "• *Show monthly trend*\n"
                "• *Sales by region*\n"
                "• *Top product category*\n"
                "• *Predict future sales*\n"
                "• *Show customer segments*"
            ),
            "data": None,
        }

    if intent == "total_sales":
        total = df["sales"].sum()
        return {
            "reply": f"💰 **Total Sales:** ₹{total:,.2f} across {len(df)} records.",
            "data": {"total_sales": round(float(total), 2)},
        }

    if intent == "total_profit":
        total = df["profit"].sum()
        return {
            "reply": f"📈 **Total Profit:** ₹{total:,.2f}",
            "data": {"total_profit": round(float(total), 2)},
        }

    if intent == "total_customers":
        total = df["customers"].sum()
        return {
            "reply": f"👥 **Total Customers Served:** {total:,}",
            "data": {"total_customers": int(total)},
        }

    if intent == "avg_sales":
        avg = df["sales"].mean()
        return {
            "reply": f"📊 **Average Daily Sales:** ₹{avg:,.2f}",
            "data": {"avg_sales": round(float(avg), 2)},
        }

    if intent == "avg_profit":
        avg = df["profit"].mean()
        return {
            "reply": f"📊 **Average Daily Profit:** ₹{avg:,.2f}",
            "data": {"avg_profit": round(float(avg), 2)},
        }

    if intent == "best_day":
        idx = df["sales"].idxmax()
        row = df.loc[idx]
        return {
            "reply": (
                f"🏆 **Best Sales Day:** {row['date'].strftime('%Y-%m-%d')}\n"
                f"Sales: ₹{row['sales']:,.0f} | Profit: ₹{row['profit']:,.0f} | Customers: {row['customers']}"
            ),
            "data": {"date": row['date'].strftime('%Y-%m-%d'), "sales": float(row['sales']), "profit": float(row['profit'])},
        }

    if intent == "worst_day":
        idx = df["sales"].idxmin()
        row = df.loc[idx]
        return {
            "reply": (
                f"📉 **Lowest Sales Day:** {row['date'].strftime('%Y-%m-%d')}\n"
                f"Sales: ₹{row['sales']:,.0f} | Profit: ₹{row['profit']:,.0f}"
            ),
            "data": {"date": row['date'].strftime('%Y-%m-%d'), "sales": float(row['sales'])},
        }

    if intent == "date_lookup":
        date_str = _extract_date(msg)
        if not date_str:
            return {"reply": "📅 Please include a date in YYYY-MM-DD format, e.g. *profit on 2024-03-15*", "data": None}
        match = df[df["date"] == pd.Timestamp(date_str)]
        if match.empty:
            return {"reply": f"❌ No data found for **{date_str}**.", "data": None}
        row = match.iloc[0]
        return {
            "reply": (
                f"📅 **Data for {date_str}:**\n"
                f"Sales: ₹{row['sales']:,.0f} | Profit: ₹{row['profit']:,.0f} | Customers: {row['customers']}"
            ),
            "data": {"date": date_str, "sales": float(row['sales']), "profit": float(row['profit']), "customers": int(row['customers'])},
        }

    if intent == "monthly_trend":
        monthly = df.groupby(df["date"].dt.to_period("M")).agg(
            sales=("sales", "sum"), profit=("profit", "sum"), customers=("customers", "sum")
        ).reset_index()
        monthly["date"] = monthly["date"].astype(str)
        rows_text = "\n".join(
            f"  {r['date']}: ₹{r['sales']:,.0f}" for _, r in monthly.iterrows()
        )
        return {
            "reply": f"📆 **Monthly Sales Trend:**\n{rows_text}",
            "data": monthly.to_dict(orient="records"),
        }

    if intent == "region_breakdown":
        by_region = df.groupby("region")["sales"].sum().sort_values(ascending=False)
        rows = "\n".join(f"  {k}: ₹{v:,.0f}" for k, v in by_region.items())
        return {
            "reply": f"🗺️ **Sales by Region:**\n{rows}",
            "data": by_region.to_dict(),
        }

    if intent == "category_breakdown":
        by_cat = df.groupby("product_category")["sales"].sum().sort_values(ascending=False)
        top = by_cat.index[0]
        rows = "\n".join(f"  {k}: ₹{v:,.0f}" for k, v in by_cat.items())
        return {
            "reply": f"🛒 **Sales by Category:**\n{rows}\n\n🏆 Top category: **{top}**",
            "data": by_cat.to_dict(),
        }

    if intent == "predict":
        from ml_model import predict_sales
        result = predict_sales(days_ahead=30)
        avg = result["summary"]["avg_predicted_sales"]
        return {
            "reply": (
                f"🔮 **30-Day Sales Forecast (Linear Regression):**\n"
                f"Average Predicted Sales: ₹{avg:,.2f}/day\n"
                f"Range: ₹{result['summary']['min_predicted_sales']:,.0f} – ₹{result['summary']['max_predicted_sales']:,.0f}"
            ),
            "data": result,
        }

    if intent == "segment":
        from ml_model import get_segments
        result = get_segments()
        rows = "\n".join(
            f"  {s['name']}: {s['count']} records | Avg Sales: ₹{s['avg_sales']:,.0f}"
            for s in result["segments"]
        )
        return {
            "reply": f"🎯 **Customer Segments (K-Means k=3):**\n{rows}",
            "data": result,
        }

    # ── fallback ─────────────────────────────────────────────
    return {
        "reply": (
            "🤔 I didn't quite understand that. Try asking:\n"
            "• *total sales*, *total profit*, *predict sales*, *best day*, *monthly trend* …\n"
            "Type **help** to see all commands."
        ),
        "data": None,
    }


def process_message(msg: str) -> dict:
    """Main entry point called by Flask."""
    df = _load_data()
    intent = _detect_intent(msg)
    result = _handle(intent, msg, df)
    result["intent"] = intent
    return result
