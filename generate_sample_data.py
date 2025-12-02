"""
Generate sample data: 10 users with 3-5 orders each
"""
from app import create_app
from models import db, User, MenuItem, Order, OrderItem, UserLocation
from utils import get_location_from_ip, DEMO_IPS
import random
from datetime import datetime, timedelta

app = create_app()

# Sample user data
SAMPLE_USERS = [
    {'username': 'alice', 'email': 'alice@example.com', 'city': 'Paris', 'password': 'password123'},
    {'username': 'bob', 'email': 'bob@example.com', 'city': 'London', 'password': 'password123'},
    {'username': 'charlie', 'email': 'charlie@example.com', 'city': 'Bordeaux', 'password': 'password123'},
    {'username': 'diana', 'email': 'diana@example.com', 'city': 'Lyon', 'password': 'password123'},
    {'username': 'edward', 'email': 'edward@example.com', 'city': 'Paris', 'password': 'password123'},
    {'username': 'fiona', 'email': 'fiona@example.com', 'city': 'London', 'password': 'password123'},
    {'username': 'george', 'email': 'george@example.com', 'city': 'Bordeaux', 'password': 'password123'},
    {'username': 'hannah', 'email': 'hannah@example.com', 'city': 'Lyon', 'password': 'password123'},
    {'username': 'ivan', 'email': 'ivan@example.com', 'city': 'Paris', 'password': 'password123'},
    {'username': 'julia', 'email': 'julia@example.com', 'city': 'London', 'password': 'password123'},
]

ORDER_STATUSES = ['pending', 'confirmed', 'preparing', 'delivered', 'cancelled']
ORDER_NOTES = [
    'Please add extra napkins',
    'Ring doorbell when arrived',
    'Leave at door',
    'Call when here',
    'No spicy please',
    'Extra sauce please',
    'Well done',
    None,
    None,
    None,  # More likely to have no notes
]

def create_users():
    """Create 10 sample users"""
    print("Creating 10 sample users...")
    users = []
    
    for user_data in SAMPLE_USERS:
        # Check if user already exists
        existing_user = User.query.filter_by(username=user_data['username']).first()
        if existing_user:
            print(f"  User '{user_data['username']}' already exists, skipping...")
            users.append(existing_user)
            continue
        
        user = User(
            username=user_data['username'],
            email=user_data['email'],
            city=user_data['city'],
            role='user'
        )
        user.set_password(user_data['password'])
        db.session.add(user)
        users.append(user)
        print(f"  Created user: {user_data['username']} ({user_data['city']})")
    
    db.session.commit()
    return users

def create_orders_for_user(user, menu_items):
    """Create 3-5 random orders for a user"""
    num_orders = random.randint(3, 5)
    print(f"\n  Creating {num_orders} orders for {user.username}...")
    
    for i in range(num_orders):
        # Random date in the last 30 days
        days_ago = random.randint(0, 30)
        order_date = datetime.utcnow() - timedelta(days=days_ago)
        
        # Random IP from demo IPs or user's city
        ip_data = random.choice(DEMO_IPS)
        ip_address = ip_data['ip']
        
        # Get location data
        location_data = get_location_from_ip(ip_address)
        
        # Check if city matches
        matches_city = location_data['city'].lower() == user.city.lower() if location_data['city'] else None
        
        # Create location record
        user_location = UserLocation(
            user_id=user.id,
            ip_address=ip_address,
            city=location_data['city'],
            region=location_data['region'],
            country=location_data['country'],
            latitude=location_data['latitude'],
            longitude=location_data['longitude'],
            matches_user_city=matches_city,
            action='order',
            timestamp=order_date
        )
        db.session.add(user_location)
        
        # Random number of items (1-4)
        num_items = random.randint(1, 4)
        selected_items = random.sample(menu_items, num_items)
        
        # Calculate total
        total_price = 0
        order_items_data = []
        
        for menu_item in selected_items:
            quantity = random.randint(1, 3)
            subtotal = menu_item.price * quantity
            total_price += subtotal
            order_items_data.append({
                'menu_item': menu_item,
                'quantity': quantity,
                'price': menu_item.price
            })
        
        # Create order
        order = Order(
            user_id=user.id,
            total_price=round(total_price, 2),
            status=random.choice(ORDER_STATUSES),
            notes=random.choice(ORDER_NOTES),
            created_at=order_date,
            updated_at=order_date
        )
        db.session.add(order)
        db.session.flush()  # Get order ID
        
        # Create order items
        for item_data in order_items_data:
            order_item = OrderItem(
                order_id=order.id,
                menu_item_id=item_data['menu_item'].id,
                quantity=item_data['quantity'],
                price_at_order=item_data['price']
            )
            db.session.add(order_item)
        
        print(f"    Order #{i+1}: ${total_price:.2f} - {num_items} items - {location_data['city']} ({ip_address})")
    
    db.session.commit()

def main():
    with app.app_context():
        print("=== Generating Sample Data ===\n")
        
        # Get all menu items
        menu_items = MenuItem.query.all()
        if not menu_items:
            print("ERROR: No menu items found! Please run init_db.py first.")
            return
        
        print(f"Found {len(menu_items)} menu items in database\n")
        
        # Create users
        users = create_users()
        print(f"\n✓ Total users: {len(users)}")
        
        # Create orders for each user
        print("\n=== Creating Orders ===")
        for user in users:
            create_orders_for_user(user, menu_items)
        
        # Print summary
        total_orders = Order.query.count()
        total_users = User.query.count()
        total_revenue = db.session.query(db.func.sum(Order.total_price)).scalar() or 0
        
        print("\n" + "="*50)
        print("✓ Sample Data Generation Complete!")
        print("="*50)
        print(f"Total Users:    {total_users}")
        print(f"Total Orders:   {total_orders}")
        print(f"Total Revenue:  ${total_revenue:.2f}")
        print(f"Menu Items:     {len(menu_items)}")
        print("\nYou can now:")
        print("1. Login as any user (password: 'password123')")
        print("2. View analytics at /admin/statistics")
        print("3. View graph at /admin/graph")
        print("4. View locations at /admin/locations")

if __name__ == '__main__':
    main()
