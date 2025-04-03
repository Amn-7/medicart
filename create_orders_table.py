import sqlite3

conn = sqlite3.connect("orders.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT,
    items TEXT,
    total INTEGER,
    timestamp TEXT
)
""")

conn.commit()
conn.close()
print("✅ orders table created or already exists.")
