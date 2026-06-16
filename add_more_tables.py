"""
Add more tables for complex JOIN queries
Run: python add_more_tables.py
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

conn = sqlite3.connect("sales.db")

# ==================== CUSTOMERS TABLE ====================
print("🔄 Creating customers table...")
customers_data = []
for i in range(1, 101):
    # Fix: Convert numpy datetime to string properly
    random_date = pd.date_range("2020-01-01", "2023-12-31")[np.random.randint(0, 1461)]
    customers_data.append({
        "customer_id": i,
        "customer_name": f"Customer_{i}",
        "email": f"customer{i}@email.com",
        "city": np.random.choice(["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", 
                                  "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose"]),
        "state": np.random.choice(["CA", "NY", "TX", "FL", "IL", "PA", "OH", "GA", "NC", "MI"]),
        "join_date": random_date.strftime("%Y-%m-%d"),
        "customer_segment": np.random.choice(["Premium", "Gold", "Silver", "Bronze"], p=[0.1, 0.2, 0.3, 0.4])
    })

customers_df = pd.DataFrame(customers_data)
customers_df.to_sql("customers", conn, if_exists="replace", index=False)
print(f"   ✅ {len(customers_df)} customers added")

# ==================== PRODUCTS TABLE ====================
print("🔄 Creating products table...")
products_data = [
    {"product_id": 1, "product_name": "Laptop", "category": "Electronics", "supplier": "TechCorp", "cost": 600},
    {"product_id": 2, "product_name": "Phone", "category": "Electronics", "supplier": "MobileInc", "cost": 400},
    {"product_id": 3, "product_name": "Tablet", "category": "Electronics", "supplier": "TechCorp", "cost": 250},
    {"product_id": 4, "product_name": "Headphones", "category": "Accessories", "supplier": "SoundCo", "cost": 40},
    {"product_id": 5, "product_name": "Monitor", "category": "Electronics", "supplier": "DisplayPro", "cost": 120},
    {"product_id": 6, "product_name": "Keyboard", "category": "Accessories", "supplier": "TypeMaster", "cost": 25},
    {"product_id": 7, "product_name": "Mouse", "category": "Accessories", "supplier": "ClickTech", "cost": 15},
    {"product_id": 8, "product_name": "Desk Chair", "category": "Furniture", "supplier": "ComfortZone", "cost": 120},
    {"product_id": 9, "product_name": "Webcam", "category": "Accessories", "supplier": "VisionPro", "cost": 35},
    {"product_id": 10, "product_name": "USB Cable", "category": "Accessories", "supplier": "CableMasters", "cost": 5}
]

products_df = pd.DataFrame(products_data)
products_df.to_sql("products", conn, if_exists="replace", index=False)
print(f"   ✅ {len(products_df)} products added")

# ==================== REGIONS TABLE ====================
print("🔄 Creating regions table...")
regions_data = [
    {"region_id": 1, "region_name": "North", "manager": "Alice Johnson", "office": "Boston"},
    {"region_id": 2, "region_name": "South", "manager": "Bob Smith", "office": "Atlanta"},
    {"region_id": 3, "region_name": "East", "manager": "Carol Davis", "office": "New York"},
    {"region_id": 4, "region_name": "West", "manager": "Dave Wilson", "office": "San Francisco"},
    {"region_id": 5, "region_name": "Central", "manager": "Eve Brown", "office": "Chicago"}
]

regions_df = pd.DataFrame(regions_data)
regions_df.to_sql("regions", conn, if_exists="replace", index=False)
print(f"   ✅ {len(regions_df)} regions added")

# ==================== VERIFY ====================
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cursor.fetchall()]
print("\n📊 Tables in database:")
for table in tables:
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f"   - {table}: {count:,} rows")

conn.close()
print("\n🎉 More tables added! Run 'streamlit run app.py' to test JOIN queries.")