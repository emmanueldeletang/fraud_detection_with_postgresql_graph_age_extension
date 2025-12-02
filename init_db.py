from app import create_app
from models import db, User, MenuItem
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Drop all views first (they depend on tables)
    print("Dropping views...")
    views = ['v_user_order_summary', 'v_order_details_full', 'v_fraud_detection_ip', 'v_user_locations']
    for view in views:
        try:
            db.session.execute(text(f"DROP VIEW IF EXISTS {view} CASCADE"))
        except Exception as e:
            print(f"Note: {e}")
    
    # Drop all tables from the SQL schema (order_details, etc.)
    print("Dropping SQL schema tables...")
    sql_tables = ['order_items', 'order_details', 'orders', 'menu', 'users', 'user_locations', 'menu_items']
    for table in sql_tables:
        try:
            db.session.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
        except Exception as e:
            print(f"Note: {e}")
    
    db.session.commit()
    
    # Now create Flask tables
    print("Creating Flask tables...")
    db.create_all()
    
    print("Database initialized!")
    
    # Create admin user
    admin = User(
        username='admin',
        email='admin@restaurant.com',
        city='New York',
        role='admin'
    )
    admin.set_password('admin123')
    db.session.add(admin)
    
    # Create sample user
    user = User(
        username='john',
        email='john@example.com',
        city='Los Angeles',
        role='user'
    )
    user.set_password('password123')
    db.session.add(user)
    
    # Create sample menu items
    menu_items = [
        MenuItem(name='Caesar Salad', description='Fresh romaine lettuce with Caesar dressing', price=8.99, category='appetizer', image_url='https://images.unsplash.com/photo-1546793665-c74683f339c1?w=400', available=True),
        MenuItem(name='Bruschetta', description='Toasted bread with tomatoes and basil', price=7.50, category='appetizer', image_url='https://images.unsplash.com/photo-1572695157366-5e585ab2b69f?w=400', available=True),
        MenuItem(name='Grilled Chicken', description='Juicy grilled chicken breast with herbs', price=15.99, category='main', image_url='https://images.unsplash.com/photo-1598103442097-8b74394b95c6?w=400', available=True),
        MenuItem(name='Ribeye Steak', description='Premium ribeye steak cooked to perfection', price=28.99, category='main', image_url='https://images.unsplash.com/photo-1600891964092-4316c288032e?w=400', available=True),
        MenuItem(name='Margherita Pizza', description='Classic pizza with tomato, mozzarella, and basil', price=12.99, category='main', image_url='https://images.unsplash.com/photo-1574071318508-1cdbab80d002?w=400', available=True),
        MenuItem(name='Pasta Carbonara', description='Creamy pasta with bacon and parmesan', price=13.50, category='main', image_url='https://images.unsplash.com/photo-1612874742237-6526221588e3?w=400', available=True),
        MenuItem(name='Tiramisu', description='Italian dessert with coffee and mascarpone', price=6.99, category='dessert', image_url='https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=400', available=True),
        MenuItem(name='Chocolate Lava Cake', description='Warm chocolate cake with molten center', price=7.50, category='dessert', image_url='https://images.unsplash.com/photo-1624353365286-3f8d62daad51?w=400', available=True),
        MenuItem(name='Coca-Cola', description='Classic soft drink', price=2.50, category='drink', image_url='https://images.unsplash.com/photo-1554866585-cd94860890b7?w=400', available=True),
        MenuItem(name='Sparkling Water', description='Refreshing sparkling mineral water', price=2.00, category='drink', image_url='https://images.unsplash.com/photo-1548839140-29a749e1cf4d?w=400', available=True),
    ]
    
    for item in menu_items:
        db.session.add(item)
    
    db.session.commit()
    
    print("\nSample data created:")
    print(f"- Admin user: username='admin', password='admin123'")
    print(f"- Regular user: username='john', password='password123'")
    print(f"- {len(menu_items)} menu items created")
    print("\nDatabase ready to use!")
