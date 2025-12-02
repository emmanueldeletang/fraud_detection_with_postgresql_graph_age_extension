import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from config import Config
from urllib.parse import urlparse


def get_db_connection():
    """Get database connection"""
    db_url = Config.SQLALCHEMY_DATABASE_URI
    parsed = urlparse(db_url)
    
    conn = psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port,
        database=parsed.path[1:],
        user=parsed.username,
        password=parsed.password
    )
    return conn


def init_age_graph():
    """Initialize Apache AGE graph"""
    conn = get_db_connection()
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    
    try:
        # Create AGE extension if not exists
        print("Setting up Apache AGE extension...")
        cursor.execute("CREATE EXTENSION IF NOT EXISTS age;")
        
        # Load AGE
        cursor.execute("LOAD 'age';")
        
        # Set search path
        cursor.execute("SET search_path = ag_catalog, '$user', public;")
        
        # Create graph if not exists
        print("Creating restaurant_graph...")
        cursor.execute("""
            SELECT COUNT(*) FROM ag_catalog.ag_graph WHERE name = 'restaurant_graph';
        """)
        
        if cursor.fetchone()[0] == 0:
            cursor.execute("SELECT create_graph('restaurant_graph');")
            print("Graph 'restaurant_graph' created successfully!")
        else:
            print("Graph 'restaurant_graph' already exists.")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error initializing AGE: {e}")
        cursor.close()
        conn.close()
        return False


def add_order_to_graph(user, ip_address, city_detected, order_id):
    """
    Add order information to the graph database
    Creates vertices for: User, IP, City, Email
    Creates edges for: USED_IP, FROM_CITY, HAS_EMAIL, PLACED_ORDER
    """
    conn = get_db_connection()
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    
    try:
        # Load AGE and set search path
        cursor.execute("LOAD 'age';")
        cursor.execute("SET search_path = ag_catalog, '$user', public;")
        
        username = user.username
        email = user.email
        user_city = user.city
        
        # Create or merge User vertex
        cursor.execute(f"""
            SELECT * FROM cypher('restaurant_graph', $$
                MERGE (u:User {{username: '{username}', city: '{user_city}'}})
                RETURN u
            $$) AS (u agtype);
        """)
        
        # Create or merge Email vertex
        cursor.execute(f"""
            SELECT * FROM cypher('restaurant_graph', $$
                MERGE (e:Email {{address: '{email}'}})
                RETURN e
            $$) AS (e agtype);
        """)
        
        # Create or merge IP vertex
        cursor.execute(f"""
            SELECT * FROM cypher('restaurant_graph', $$
                MERGE (ip:IPAddress {{address: '{ip_address}'}})
                RETURN ip
            $$) AS (ip agtype);
        """)
        
        # Create or merge detected City vertex
        cursor.execute(f"""
            SELECT * FROM cypher('restaurant_graph', $$
                MERGE (c:City {{name: '{city_detected}'}})
                RETURN c
            $$) AS (c agtype);
        """)
        
        # Create or merge user's registered City vertex
        cursor.execute(f"""
            SELECT * FROM cypher('restaurant_graph', $$
                MERGE (c:City {{name: '{user_city}'}})
                RETURN c
            $$) AS (c agtype);
        """)
        
        # Create relationships: User HAS_EMAIL Email
        cursor.execute(f"""
            SELECT * FROM cypher('restaurant_graph', $$
                MATCH (u:User {{username: '{username}'}}), (e:Email {{address: '{email}'}})
                MERGE (u)-[r:HAS_EMAIL]->(e)
                RETURN r
            $$) AS (r agtype);
        """)
        
        # Create relationships: User USED_IP IPAddress
        cursor.execute(f"""
            SELECT * FROM cypher('restaurant_graph', $$
                MATCH (u:User {{username: '{username}'}}), (ip:IPAddress {{address: '{ip_address}'}})
                MERGE (u)-[r:USED_IP {{order_id: {order_id}}}]->(ip)
                RETURN r
            $$) AS (r agtype);
        """)
        
        # Create relationships: IPAddress FROM_CITY City (detected city)
        cursor.execute(f"""
            SELECT * FROM cypher('restaurant_graph', $$
                MATCH (ip:IPAddress {{address: '{ip_address}'}}), (c:City {{name: '{city_detected}'}})
                MERGE (ip)-[r:FROM_CITY]->(c)
                RETURN r
            $$) AS (r agtype);
        """)
        
        # Create relationships: User REGISTERED_IN City (user's city)
        cursor.execute(f"""
            SELECT * FROM cypher('restaurant_graph', $$
                MATCH (u:User {{username: '{username}'}}), (c:City {{name: '{user_city}'}})
                MERGE (u)-[r:REGISTERED_IN]->(c)
                RETURN r
            $$) AS (r agtype);
        """)
        
        print(f"Order #{order_id} added to graph: {username} -> {ip_address} -> {city_detected}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error adding order to graph: {e}")
        cursor.close()
        conn.close()
        return False


def query_user_graph(username):
    """Query graph for user relationships"""
    conn = get_db_connection()
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    
    try:
        cursor.execute("LOAD 'age';")
        cursor.execute("SET search_path = ag_catalog, '$user', public;")
        
        # Get user's IP addresses and cities
        cursor.execute(f"""
            SELECT * FROM cypher('restaurant_graph', $$
                MATCH (u:User {{username: '{username}'}})-[:USED_IP]->(ip:IPAddress)-[:FROM_CITY]->(c:City)
                RETURN u.username, ip.address, c.name
            $$) AS (username agtype, ip_address agtype, city agtype);
        """)
        
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return results
        
    except Exception as e:
        print(f"Error querying graph: {e}")
        cursor.close()
        conn.close()
        return []


def detect_fraud_patterns():
    """Detect potential fraud patterns in the graph"""
    conn = get_db_connection()
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    
    try:
        cursor.execute("LOAD 'age';")
        cursor.execute("SET search_path = ag_catalog, '$user', public;")
        
        # Find users using same IP
        cursor.execute("""
            SELECT * FROM cypher('restaurant_graph', $$
                MATCH (u1:User)-[:USED_IP]->(ip:IPAddress)<-[:USED_IP]-(u2:User)
                WHERE u1.username <> u2.username
                RETURN DISTINCT u1.username, u2.username, ip.address
            $$) AS (user1 agtype, user2 agtype, ip agtype);
        """)
        
        shared_ips = cursor.fetchall()
        
        # Find users with city mismatch
        cursor.execute("""
            SELECT * FROM cypher('restaurant_graph', $$
                MATCH (u:User)-[:REGISTERED_IN]->(reg_city:City),
                      (u)-[:USED_IP]->(ip:IPAddress)-[:FROM_CITY]->(det_city:City)
                WHERE reg_city.name <> det_city.name
                RETURN u.username, reg_city.name, det_city.name, ip.address
            $$) AS (username agtype, registered_city agtype, detected_city agtype, ip agtype);
        """)
        
        mismatches = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {
            'shared_ips': shared_ips,
            'city_mismatches': mismatches
        }
        
    except Exception as e:
        print(f"Error detecting fraud: {e}")
        cursor.close()
        conn.close()
        return {'shared_ips': [], 'city_mismatches': []}
