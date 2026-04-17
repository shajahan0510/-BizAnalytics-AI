"""Quick integration test for all backend modules."""
import sys, json
sys.path.insert(0, '.')

from ml_model import get_analytics_summary, predict_sales, get_segments
from chatbot import process_message

print("=== Analytics Summary ===")
s = get_analytics_summary()
print(f"  Total Sales:     {s['total_sales']:,}")
print(f"  Total Profit:    {s['total_profit']:,}")
print(f"  Total Customers: {s['total_customers']:,}")
print(f"  Best Day:        {s['best_sales_day']}")

print()
print("=== 7-Day Sales Prediction ===")
p = predict_sales(7)
print(f"  Model: {p['model']}")
print(f"  Days Ahead: {p['days_ahead']}")
print(f"  Avg Predicted: {p['summary']['avg_predicted_sales']:,}")
for row in p['predictions'][:3]:
    print(f"  {row['date']}: {row['predicted_sales']:,}")

print()
print("=== Customer Segments ===")
seg = get_segments()
for seg_item in seg['segments']:
    print(f"  {seg_item['name']}: {seg_item['count']} records | Avg Sales: {seg_item['avg_sales']:,}")

print()
print("=== Chatbot Tests ===")
tests = ["total sales", "best day", "average profit", "monthly trend", "predict sales", "hello"]
for t in tests:
    r = process_message(t)
    preview = r['reply'][:65].replace('\n', ' ')
    print(f"  [{r['intent']:20s}] {preview}...")

print()
print("=" * 40)
print("ALL BACKEND TESTS PASSED!")
