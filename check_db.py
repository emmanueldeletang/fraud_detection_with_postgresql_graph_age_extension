import psycopg2
from config import Config
from urllib.parse import urlparse

# Parse the database URL
db_url = Config.SQLALCHEMY_DATABASE_URI
parsed = urlparse(db_url)

# Connect to database
conn = psycopg2.connect(
    host=parsed.hostname,
    port=parsed.port,
    database=parsed.path[1:],
    user=parsed.username,
    password=parsed.password
)

cursor = conn.cursor()

# Check what tables exist
cursor.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public'
    ORDER BY table_name;
""")

tables = cursor.fetchall()

print("=== Tables in database ===")
for table in tables:
    print(f"  - {table[0]}")

print("\n=== Checking for Flask app tables ===")
flask_tables = ['users', 'menu_items', 'orders', 'order_items', 'user_locations']
existing_tables = [t[0] for t in tables]

for table in flask_tables:
    if table in existing_tables:
        print(f"  ✓ {table} exists")
    else:
        print(f"  ✗ {table} MISSING")

cursor.close()
conn.close()
