"""
Create performance indexes for PostgreSQL tables based on Microsoft Azure PostgreSQL best practices
Reference: https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/generative-ai-age-performance
"""
from app import create_app
from models import db
from sqlalchemy import text

app = create_app()

INDEXES = [
    # Users table - BTREE indexes for primary key and foreign key lookups
    ('users_id_idx', 'CREATE INDEX IF NOT EXISTS users_id_idx ON users USING BTREE (id)'),
    ('users_username_idx', 'CREATE INDEX IF NOT EXISTS users_username_idx ON users USING BTREE (username)'),
    ('users_email_idx', 'CREATE INDEX IF NOT EXISTS users_email_idx ON users USING BTREE (email)'),
    ('users_city_idx', 'CREATE INDEX IF NOT EXISTS users_city_idx ON users USING BTREE (city)'),
    ('users_role_idx', 'CREATE INDEX IF NOT EXISTS users_role_idx ON users USING BTREE (role)'),
    
    # Menu items table - BTREE indexes
    ('menu_items_id_idx', 'CREATE INDEX IF NOT EXISTS menu_items_id_idx ON menu_items USING BTREE (id)'),
    ('menu_items_category_idx', 'CREATE INDEX IF NOT EXISTS menu_items_category_idx ON menu_items USING BTREE (category)'),
    ('menu_items_available_idx', 'CREATE INDEX IF NOT EXISTS menu_items_available_idx ON menu_items USING BTREE (available)'),
    
    # Orders table - BTREE indexes for relationships and filtering
    ('orders_id_idx', 'CREATE INDEX IF NOT EXISTS orders_id_idx ON orders USING BTREE (id)'),
    ('orders_user_id_idx', 'CREATE INDEX IF NOT EXISTS orders_user_id_idx ON orders USING BTREE (user_id)'),
    ('orders_status_idx', 'CREATE INDEX IF NOT EXISTS orders_status_idx ON orders USING BTREE (status)'),
    ('orders_created_at_idx', 'CREATE INDEX IF NOT EXISTS orders_created_at_idx ON orders USING BTREE (created_at DESC)'),
    ('orders_total_price_idx', 'CREATE INDEX IF NOT EXISTS orders_total_price_idx ON orders USING BTREE (total_price)'),
    
    # Order items table - BTREE indexes for join queries (edge table in graph context)
    ('order_items_id_idx', 'CREATE INDEX IF NOT EXISTS order_items_id_idx ON order_items USING BTREE (id)'),
    ('order_items_order_id_idx', 'CREATE INDEX IF NOT EXISTS order_items_order_id_idx ON order_items USING BTREE (order_id)'),
    ('order_items_menu_item_id_idx', 'CREATE INDEX IF NOT EXISTS order_items_menu_item_id_idx ON order_items USING BTREE (menu_item_id)'),
    
    # User locations table - BTREE indexes for graph analytics
    ('user_locations_id_idx', 'CREATE INDEX IF NOT EXISTS user_locations_id_idx ON user_locations USING BTREE (id)'),
    ('user_locations_user_id_idx', 'CREATE INDEX IF NOT EXISTS user_locations_user_id_idx ON user_locations USING BTREE (user_id)'),
    ('user_locations_ip_address_idx', 'CREATE INDEX IF NOT EXISTS user_locations_ip_address_idx ON user_locations USING BTREE (ip_address)'),
    ('user_locations_city_idx', 'CREATE INDEX IF NOT EXISTS user_locations_city_idx ON user_locations USING BTREE (city)'),
    ('user_locations_country_idx', 'CREATE INDEX IF NOT EXISTS user_locations_country_idx ON user_locations USING BTREE (country)'),
    ('user_locations_matches_idx', 'CREATE INDEX IF NOT EXISTS user_locations_matches_idx ON user_locations USING BTREE (matches_user_city)'),
    ('user_locations_action_idx', 'CREATE INDEX IF NOT EXISTS user_locations_action_idx ON user_locations USING BTREE (action)'),
    ('user_locations_timestamp_idx', 'CREATE INDEX IF NOT EXISTS user_locations_timestamp_idx ON user_locations USING BTREE (timestamp DESC)'),
    
    # Composite indexes for common query patterns
    ('orders_user_status_idx', 'CREATE INDEX IF NOT EXISTS orders_user_status_idx ON orders USING BTREE (user_id, status)'),
    ('orders_user_created_idx', 'CREATE INDEX IF NOT EXISTS orders_user_created_idx ON orders USING BTREE (user_id, created_at DESC)'),
    ('user_locations_user_action_idx', 'CREATE INDEX IF NOT EXISTS user_locations_user_action_idx ON user_locations USING BTREE (user_id, action)'),
    ('user_locations_ip_city_idx', 'CREATE INDEX IF NOT EXISTS user_locations_ip_city_idx ON user_locations USING BTREE (ip_address, city)'),
]

def create_indexes():
    """Create all performance indexes"""
    with app.app_context():
        print("=" * 70)
        print("Creating Performance Indexes for PostgreSQL")
        print("Based on Microsoft Azure PostgreSQL Best Practices")
        print("=" * 70)
        print()
        
        created = 0
        skipped = 0
        errors = 0
        
        for idx_name, sql in INDEXES:
            try:
                print(f"Creating index: {idx_name}...", end=" ")
                db.session.execute(text(sql))
                db.session.commit()
                print("✓ Created")
                created += 1
            except Exception as e:
                if "already exists" in str(e).lower():
                    print("⊙ Already exists")
                    skipped += 1
                    db.session.rollback()
                else:
                    print(f"✗ Error: {e}")
                    errors += 1
                    db.session.rollback()
        
        print()
        print("=" * 70)
        print("Index Creation Summary")
        print("=" * 70)
        print(f"Total indexes: {len(INDEXES)}")
        print(f"Created:       {created}")
        print(f"Skipped:       {skipped}")
        print(f"Errors:        {errors}")
        print()
        
        if errors == 0:
            print("✓ All indexes created successfully!")
        else:
            print(f"⚠ {errors} error(s) occurred. Check the output above.")
        
        print()
        print("Performance Benefits:")
        print("  • Faster user lookups by username/email")
        print("  • Optimized order queries by user_id and status")
        print("  • Improved graph analytics for location tracking")
        print("  • Faster fraud detection queries on IP addresses")
        print("  • Enhanced statistics aggregation queries")
        print()
        print("Query Performance Tips:")
        print("  • Use ORDER BY created_at DESC for recent orders")
        print("  • Filter by user_id + status for user order lists")
        print("  • Join order_items via order_id and menu_item_id")
        print("  • Group by city/country for location analytics")
        print()

def analyze_tables():
    """Run ANALYZE on all tables to update statistics"""
    with app.app_context():
        print("Running ANALYZE to update table statistics...")
        tables = ['users', 'menu_items', 'orders', 'order_items', 'user_locations']
        
        for table in tables:
            try:
                print(f"  Analyzing {table}...", end=" ")
                db.session.execute(text(f"ANALYZE {table}"))
                db.session.commit()
                print("✓")
            except Exception as e:
                print(f"✗ Error: {e}")
                db.session.rollback()
        
        print("✓ Table statistics updated!")
        print()

def show_index_usage():
    """Show index usage statistics"""
    with app.app_context():
        print("=" * 70)
        print("Index Usage Statistics")
        print("=" * 70)
        
        query = text("""
            SELECT 
                schemaname,
                tablename,
                indexname,
                idx_scan as scans,
                idx_tup_read as tuples_read,
                idx_tup_fetch as tuples_fetched
            FROM pg_stat_user_indexes
            WHERE schemaname = 'public'
            ORDER BY tablename, indexname
        """)
        
        try:
            result = db.session.execute(query)
            rows = result.fetchall()
            
            if rows:
                print(f"{'Table':<20} {'Index':<40} {'Scans':>10} {'Read':>10} {'Fetched':>10}")
                print("-" * 70)
                for row in rows:
                    print(f"{row[1]:<20} {row[2]:<40} {row[3]:>10} {row[4]:>10} {row[5]:>10}")
            else:
                print("No index statistics available yet.")
            
            print()
        except Exception as e:
            print(f"Could not retrieve index statistics: {e}")
            db.session.rollback()

if __name__ == '__main__':
    create_indexes()
    analyze_tables()
    
    print("=" * 70)
    print("Recommendations:")
    print("=" * 70)
    print("1. Monitor index usage with: SELECT * FROM pg_stat_user_indexes")
    print("2. Run ANALYZE periodically after bulk data loads")
    print("3. Use EXPLAIN ANALYZE to verify query plans use indexes")
    print("4. Consider VACUUM ANALYZE for maintenance")
    print()
    print("Example EXPLAIN query:")
    print("  EXPLAIN ANALYZE SELECT * FROM orders WHERE user_id = 1 AND status = 'pending';")
    print()
