from graph_utils import init_age_graph

print("Initializing Apache AGE graph database...")
print("=" * 50)

if init_age_graph():
    print("\n✓ Graph database initialized successfully!")
    print("\nYou can now:")
    print("1. Place orders to populate the graph")
    print("2. View graph analytics at /admin/graph")
    print("3. Detect fraud patterns automatically")
else:
    print("\n✗ Failed to initialize graph database")
    print("\nMake sure:")
    print("1. Apache AGE extension is installed")
    print("2. You have proper database permissions")
    print("3. PostgreSQL version is compatible with AGE")
