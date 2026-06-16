"""
Database Setup Script - Run this ONCE to create your sales database
Run command: python setup_database.py
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime

print("🔄 Creating database with 10,000+ rows...")

# Connect to SQLite database (creates file if doesn't exist)
conn = sqlite3.connect("sales.db")

# Define product categories with realistic prices
products_data = {
    "Laptop": {"price_range": (800, 2500), "category": "Electronics"},
    "Phone": {"price_range": (500, 1200), "category": "Electronics"},
    "Tablet": {"price_range": (300, 900), "category": "Electronics"},
    "Headphones": {"price_range": (50, 300), "category": "Accessories"},
    "Monitor": {"price_range": (150, 600), "category": "Electronics"},
    "Keyboard": {"price_range": (30, 150), "category": "Accessories"},
    "Mouse": {"price_range": (20, 80), "category": "Accessories"},
    "Desk Chair": {"price_range": (150, 500), "category": "Furniture"},
    "Webcam": {"price_range": (40, 200), "category": "Accessories"},
    "USB Cable": {"price_range": (10, 30), "category": "Accessories"}
}

customers = [f"Customer_{i}" for i in range(1, 101)]  # 100 unique customers
regions = ["North", "South", "East", "West", "Central"]

# Generate date range for the past 2 years
dates = pd.date_range("2023-01-01", "2024-12-31")

print(f"📅 Date range: {dates[0].date()} to {dates[-1].date()}")
print(f"👥 Customers: {len(customers)}")
print(f"📦 Products: {len(products_data)}")

# Generate random sales data
np.random.seed(42)  # For reproducible results
data = []

for transaction_id in range(10000):  # 10,000 transactions
    product = np.random.choice(list(products_data.keys()))
    product_info = products_data[product]
    price = np.random.randint(product_info["price_range"][0], product_info["price_range"][1])
    quantity = np.random.randint(1, 11)  # 1-10 units
    revenue = price * quantity
    
    # Fixed: Convert numpy datetime to pandas datetime first
    random_date = dates[np.random.randint(0, len(dates))]
    
    data.append({
        "transaction_id": transaction_id + 1,
        "date": random_date.strftime("%Y-%m-%d"),
        "customer": np.random.choice(customers),
        "region": np.random.choice(regions),
        "product": product,
        "category": product_info["category"],
        "quantity": quantity,
        "price": price,
        "revenue": revenue
    })

# Create DataFrame
df = pd.DataFrame(data)

# Add month and year columns for easier aggregation
df["date"] = pd.to_datetime(df["date"])
df["month"] = df["date"].dt.month
df["year"] = df["date"].dt.year
df["quarter"] = df["date"].dt.quarter

# Save to SQLite
df.to_sql("sales", conn, if_exists="replace", index=False)

# Verify
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM sales")
count = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(DISTINCT product) FROM sales")
products_count = cursor.fetchone()[0]

print(f"\n✅ Database created successfully!")
print(f"   📊 Total records: {count:,}")
print(f"   🏷️  Unique products: {products_count}")
print(f"   💰 Total revenue: ${df['revenue'].sum():,.2f}")
print(f"   📅 Date range: {df['date'].min().date()} to {df['date'].max().date()}")

# Show sample data
print("\n📋 Sample data (first 10 rows):")
print(df.head(10).to_string())

conn.close()
print("\n🎉 Setup complete! Run 'streamlit run app.py' to start the dashboard.")