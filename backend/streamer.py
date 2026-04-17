import os
import time
import random
import threading
from datetime import datetime

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "sales_data.csv")

# Global list acting as an event bus to hold the latest generated events.
# SSE clients can poll this list for new events.
live_events = []

def generate_sale():
    """Generates a realistic transaction, appends it to DB/CSV, and adds it to events."""
    regions = ["North", "South", "East", "West"]
    categories = ["Electronics", "Clothing", "Food"]
    
    # Use real current date
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    # Generate realistic metrics
    sales = random.randint(2000, 18000)
    customers = random.randint(15, 150)
    profit = int(sales * random.uniform(0.15, 0.45))
    region = random.choice(regions)
    category = random.choice(categories)
    
    # Append to CSV
    new_row = f"\n{date_str},{sales},{customers},{profit},{region},{category}"
    try:
        with open(DATA_PATH, "a", encoding="utf-8") as f:
            f.write(new_row)
    except Exception as e:
        print(f"Error writing to CSV: {e}")
        
    # Create the event dict
    event = {
        "date": date_str,
        "sales": sales,
        "customers": customers,
        "profit": profit,
        "region": region,
        "product_category": category,
        "timestamp": datetime.now().isoformat()
    }
    
    live_events.append(event)
    # Keep only the last 50 events in memory
    if len(live_events) > 50:
        live_events.pop(0)

# Remove background loop for Vercel
def generate_single_event():
    """Generates a random event object (stateless) for Vercel."""
    regions = ["North", "South", "East", "West"]
    categories = ["Electronics", "Clothing", "Food"]
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    sales = random.randint(2000, 18000)
    customers = random.randint(15, 150)
    profit = int(sales * random.uniform(0.15, 0.45))
    region = random.choice(regions)
    category = random.choice(categories)
    
    return {
        "date": date_str,
        "sales": sales,
        "customers": customers,
        "profit": profit,
        "region": region,
        "product_category": category,
        "timestamp": datetime.now().isoformat()
    }
