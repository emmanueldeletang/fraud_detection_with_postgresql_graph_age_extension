"""
Query Performance Analyzer - Verify index usage and query plans
Based on Microsoft Azure PostgreSQL AGE best practices
"""
from app import create_app
from models import db
from sqlalchemy import text

app = create_app()

def analyze_query(query_sql, query_name):
    """Analyze a query and show if indexes are being used"""
    print(f"\n{'='*80}")
    print(f"Query: {query_name}")
    print(f"{'='*80}")
    print(f"SQL: {query_sql}")
    print(f"\n{'Plan:':-^80}")
    
    try:
        explain_query = f"EXPLAIN ANALYZE {query_sql}"
        result = db.session.execute(text(explain_query))
        
        for row in result:
            print(row[0])
        
        db.session.rollback()
    except Exception as e:
        print(f"Error: {e}")
        db.session.rollback()

def main():
    with app.app_context():
        print("\n" + "="*80)
        print("QUERY PERFORMANCE ANALYSIS")
        print("Verifying Index Usage on PostgreSQL")
        print("="*80)
        
        # Test queries that should use indexes
        queries = [
            (
                "User lookup by username",
                "SELECT * FROM users WHERE username = 'alice'"
            ),
            (
                "User lookup by email",
                "SELECT * FROM users WHERE email = 'alice@example.com'"
            ),
            (
                "Orders by user",
                "SELECT * FROM orders WHERE user_id = 2 ORDER BY created_at DESC"
            ),
            (
                "Orders by user and status",
                "SELECT * FROM orders WHERE user_id = 2 AND status = 'delivered'"
            ),
            (
                "User location tracking",
                "SELECT * FROM user_locations WHERE user_id = 2 AND action = 'order'"
            ),
            (
                "IP fraud detection",
                "SELECT ip_address, COUNT(DISTINCT user_id) as user_count FROM user_locations GROUP BY ip_address HAVING COUNT(DISTINCT user_id) > 1"
            ),
            (
                "Order items join",
                "SELECT o.id, oi.menu_item_id, oi.quantity FROM orders o JOIN order_items oi ON o.id = oi.order_id WHERE o.user_id = 2"
            ),
            (
                "Location by city and country",
                "SELECT * FROM user_locations WHERE city = 'Paris' AND country = 'France'"
            ),
        ]
        
        for query_name, query_sql in queries:
            analyze_query(query_sql, query_name)
        
        # Show index statistics
        print(f"\n\n{'='*80}")
        print("INDEX USAGE STATISTICS")
        print(f"{'='*80}\n")
        
        stats_query = text("""
            SELECT 
                schemaname || '.' || relname as table_name,
                indexrelname as index_name,
                idx_scan as scans,
                pg_size_pretty(pg_relation_size(indexrelid)) as size
            FROM pg_stat_user_indexes
            WHERE schemaname = 'public'
            ORDER BY idx_scan DESC, relname, indexrelname
        """)
        
        result = db.session.execute(stats_query)
        rows = result.fetchall()
        
        print(f"{'Table':<25} {'Index':<45} {'Scans':>10} {'Size':>10}")
        print("-" * 95)
        
        for row in rows:
            print(f"{row[0]:<25} {row[1]:<45} {row[2]:>10} {row[3]:>10}")
        
        # Show table sizes
        print(f"\n\n{'='*80}")
        print("TABLE SIZES")
        print(f"{'='*80}\n")
        
        size_query = text("""
            SELECT 
                tablename,
                pg_size_pretty(pg_total_relation_size(quote_ident(schemaname)||'.'||quote_ident(tablename))) as total_size,
                pg_size_pretty(pg_relation_size(quote_ident(schemaname)||'.'||quote_ident(tablename))) as table_size,
                pg_size_pretty(pg_total_relation_size(quote_ident(schemaname)||'.'||quote_ident(tablename)) - 
                              pg_relation_size(quote_ident(schemaname)||'.'||quote_ident(tablename))) as index_size
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(quote_ident(schemaname)||'.'||quote_ident(tablename)) DESC
        """)
        
        result = db.session.execute(size_query)
        rows = result.fetchall()
        
        print(f"{'Table':<25} {'Total Size':>15} {'Table Size':>15} {'Index Size':>15}")
        print("-" * 80)
        
        for row in rows:
            print(f"{row[0]:<25} {row[1]:>15} {row[2]:>15} {row[3]:>15}")
        
        print("\n" + "="*80)
        print("PERFORMANCE TIPS")
        print("="*80)
        print("""
1. Look for "Index Scan" or "Index Only Scan" in query plans (good!)
2. Avoid "Seq Scan" on large tables (may need better indexes)
3. "Bitmap Index Scan" is good for multiple conditions
4. Monitor index scans over time to identify unused indexes
5. Run VACUUM ANALYZE regularly to maintain statistics
6. Use composite indexes for common multi-column filters

Key Index Types Used:
  • BTREE: Fast lookups, range queries, sorting (ORDER BY)
  • Composite: Multiple columns (user_id + status, user_id + created_at)
  • DESC: Optimized for descending sorts (created_at DESC, timestamp DESC)

Azure PostgreSQL Features:
  • Connection pooling enabled (see config.py)
  • TCP keepalives prevent connection drops
  • pool_pre_ping validates connections before use
        """)

if __name__ == '__main__':
    main()
