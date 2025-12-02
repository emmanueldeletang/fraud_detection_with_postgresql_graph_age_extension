# Restaurant Management System

WELCOME to Gemina trattoria ( why gemina , this was the name of my Grand mother who teach me how to cook , and she was an incredible mediteranean grand mother with all the advantage you can imagine for his grandchildren)
Full-stack Flask application with REST API and Web UI for restaurant management, featuring user authentication, menu management, order tracking, IP geolocation, fraud detection, and interactive graph analytics.

## Features

### Core Features
- **User Authentication**: Register and login with JWT tokens (API) and session-based auth (Web UI)
- **Role-Based Access**: Admin and regular user roles with different permissions
- **Menu Management**: Admins can add, modify, and remove menu items with images
- **Order System**: Users can place orders with real-time IP tracking
- **Shopping Cart**: Web-based shopping cart with quantity management
- **Order History**: Track order status and view detailed order information

### Security & Fraud Detection
- **IP Geolocation**: Tracks user location using ipapi.co and compares with registered city
- **Location Verification**: Detects if orders are placed from unexpected locations
- **Demo Mode**: Simulated IP addresses for testing (Paris, London, Bordeaux, Lyon)
- **Graph Analytics**: Interactive network visualization showing user-IP-location relationships
- **Fraud Alerts**: Automatic detection of suspicious patterns (shared IPs, city mismatches)

### Admin Dashboard
- **Statistics**: Revenue analytics, order counts, user spending patterns
- **Order Management**: View and update all orders, track order status
- **Menu Editor**: Full CRUD operations for menu items with image URLs
- **Location Tracking**: Monitor user locations and detect anomalies
- **Graph Visualization**: Interactive vis.js network showing fraud patterns
- **Settings**: Toggle demo mode and configure application behavior

### Performance Optimization
- **PostgreSQL Indexes**: 28 optimized BTREE and composite indexes
- **Connection Pooling**: Azure PostgreSQL-optimized connection handling
- **Query Optimization**: Based on Microsoft Azure best practices
- **TCP Keepalives**: Prevents connection drops on Azure

## Tech Stack

- **Backend**: Flask 3.0.0, Flask-SQLAlchemy, Flask-JWT-Extended
- **Database**: PostgreSQL (Azure Database for PostgreSQL compatible)
- **Authentication**: JWT tokens (API) + Flask sessions (Web)
- **Frontend**: Bootstrap 5, Bootstrap Icons, vis.js (graph visualization)
- **Geolocation**: ipapi.co API
- **Security**: bcrypt password hashing, CORS support

## Installation

1. **Clone the repository** (or ensure you're in the project directory)

2. **Create a virtual environment**:
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

3. **Install dependencies**:
```powershell
pip install -r requirements.txt
```

4. **Set up PostgreSQL database**:
   - Install PostgreSQL if not already installed
   - Create a database: `CREATE DATABASE restaurant_db;`

5. **Configure environment variables**:
```powershell
copy .env.example .env
```
   - Edit `.env` and update the database URL and JWT secret

6. **Initialize the database**:
```powershell
python init_db.py
```

7. **Create performance indexes** (optional but recommended):
```powershell
python create_indexes.py
```

8. **Generate sample data** (optional):
```powershell
python generate_sample_data.py
```
This creates 10 users with 3-5 orders each for testing.

## Running the Application

```powershell
python app.py
```

- **API**: Available at `http://localhost:5000/api/`
- **Web UI**: Available at `http://localhost:5000/`

## Web UI Routes

### Public Routes
- **`/`** - Home page
- **`/login`** - User login
- **`/register`** - User registration
- **`/menu`** - Browse menu items

### User Routes (authentication required)
- **`/cart`** - Shopping cart
- **`/checkout`** - Place order
- **`/orders`** - View order history

### Admin Routes (admin role required)
- **`/admin/menu`** - Manage menu items (add/edit/delete)
- **`/admin/orders`** - View and manage all orders
- **`/admin/statistics`** - Revenue and order analytics
- **`/admin/locations`** - User location tracking
- **`/admin/graph`** - Interactive graph analytics
- **`/admin/settings`** - Application settings (demo mode)

## API Endpoints

### Authentication (`/api/auth`)

- **POST `/api/auth/register`** - Register a new user
  ```json
  {
    "username": "john",
    "email": "john@example.com",
    "password": "password123",
    "city": "Los Angeles"
  }
  ```

- **POST `/api/auth/login`** - Login and get JWT token
  ```json
  {
    "username": "john",
    "password": "password123"
  }
  ```
  Returns: `access_token`, user info, and location tracking data

- **GET `/api/auth/me`** - Get current user info (requires auth)

- **GET `/api/auth/locations`** - Get user's location history (requires auth)

### Menu (`/api/menu`)

- **GET `/api/menu`** - Get all menu items (public)
  - Query params: `?category=appetizer&available=true`

- **GET `/api/menu/{id}`** - Get specific menu item (public)

- **POST `/api/menu`** - Create menu item (admin only)
  ```json
  {
    "name": "Burger",
    "description": "Delicious beef burger",
    "price": 12.99,
    "category": "main",
    "available": true
  }
  ```

- **PUT `/api/menu/{id}`** - Update menu item (admin only)

- **DELETE `/api/menu/{id}`** - Delete menu item (admin only)

- **GET `/api/menu/categories`** - Get all categories (public)

### Orders (`/api/orders`)

- **POST `/api/orders`** - Place an order (requires auth)
  ```json
  {
    "items": [
      {
        "menu_item_id": 1,
        "quantity": 2
      },
      {
        "menu_item_id": 3,
        "quantity": 1
      }
    ],
    "notes": "No onions please"
  }
  ```
  Returns: Order details + IP location tracking

- **GET `/api/orders`** - Get user's orders (or all orders for admin)

- **GET `/api/orders/{id}`** - Get specific order with location info

- **PUT `/api/orders/{id}/status`** - Update order status (admin only)
  ```json
  {
    "status": "confirmed"
  }
  ```
  Valid statuses: `pending`, `confirmed`, `preparing`, `delivered`, `cancelled`

- **DELETE `/api/orders/{id}`** - Cancel order (only pending orders)

- **GET `/api/orders/statistics`** - Get order statistics (admin only)
  Returns: Overall stats and per-user statistics

## Authentication

Include JWT token in headers for protected endpoints:
```
Authorization: Bearer <access_token>
```

## Default Users

After running `init_db.py`:

- **Admin**: username=`admin`, password=`admin123`
- **User**: username=`john`, password=`password123`

After running `generate_sample_data.py`:
- **10 additional users**: alice, bob, charlie, diana, edward, fiona, george, hannah, ivan, julia
- All passwords: `password123`
- Each user has 3-5 sample orders

## Demo Mode

Demo mode allows testing of IP geolocation features without real geographic diversity.

### Enable Demo Mode
1. Navigate to `/admin/settings` (requires admin login)
2. Toggle "Enable Demo Mode"
3. Restart the application

Or edit `.env`:
```env
DEMO_MODE=true
```

### Demo IP Addresses
- **195.154.122.113** - Paris, France
- **81.2.69.142** - London, United Kingdom
- **90.119.169.42** - Bordeaux, France
- **87.98.154.146** - Lyon, France

The system rotates through these IPs automatically for each order/login, creating realistic fraud detection scenarios.

See [DEMO_MODE.md](DEMO_MODE.md) for complete documentation.

## IP Geolocation Feature

When users login or place orders, the system:
1. Captures their IP address
2. Gets geolocation data (city, region, country, coordinates)
3. Compares detected city with registered city
4. Stores location history in the database
5. Warns if location doesn't match

This helps with:
- Security monitoring
- Fraud detection
- Analytics and insights

## Database Schema

### Tables
- **users**: User accounts with authentication (username, email, password_hash, city, role)
- **menu_items**: Restaurant menu items (name, description, price, category, image_url, available)
- **orders**: Customer orders (user_id, status, total_price, notes, timestamps)
- **order_items**: Items within each order (order_id, menu_item_id, quantity, price_at_order)
- **user_locations**: IP tracking and geolocation history (user_id, ip_address, city, region, country, coordinates, matches_user_city, action, timestamp)

### Indexes (28 total)
Based on [Microsoft Azure PostgreSQL Best Practices](https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/generative-ai-age-performance):

- **BTREE indexes**: Fast lookups on id, username, email, user_id, order_id, ip_address, city, status, created_at
- **Composite indexes**: Optimized for common queries (user_id+status, user_id+created_at, ip_address+city)
- **DESC indexes**: Optimized for recent data queries (created_at DESC, timestamp DESC)

Run `python create_indexes.py` to create all indexes.

### Connection Pool Configuration
Optimized for Azure PostgreSQL:
- Pool size: 10 connections
- Pool recycle: 3600 seconds
- Pre-ping: Enabled (validates connections before use)
- TCP keepalives: Prevents connection drops

## Development

### Reset the database
```powershell
python init_db.py
```

### Generate sample data
```powershell
python generate_sample_data.py
```
Creates 10 users with 37 orders totaling ~$1,850 in revenue.

### Create indexes
```powershell
python create_indexes.py
```
Creates 28 performance indexes for PostgreSQL.

### Analyze query performance
```powershell
python analyze_queries.py
```
Shows query execution plans and verifies index usage.

### Project Structure
```
restaurantpg/
├── app.py                      # Flask application factory
├── config.py                   # Configuration and connection pool
├── models.py                   # SQLAlchemy models
├── utils.py                    # Helper functions, IP handling, demo mode
├── graph_utils.py              # Graph analytics functions
├── routes_auth.py              # API: Authentication endpoints
├── routes_menu.py              # API: Menu endpoints
├── routes_orders.py            # API: Order endpoints
├── routes_web.py               # Web UI routes
├── init_db.py                  # Database initialization
├── generate_sample_data.py     # Sample data generator
├── create_indexes.py           # Index creation script
├── analyze_queries.py          # Query performance analyzer
├── templates/                  # Jinja2 templates
│   ├── base.html              # Base template with navigation
│   ├── index.html             # Home page
│   ├── login.html             # Login form
│   ├── register.html          # Registration form
│   ├── menu.html              # Menu display
│   ├── cart.html              # Shopping cart
│   ├── orders.html            # Order history
│   ├── admin_menu.html        # Admin menu management
│   ├── admin_menu_edit.html   # Edit menu item
│   ├── admin_orders.html      # Admin order management
│   ├── admin_statistics.html  # Revenue analytics
│   ├── admin_locations.html   # Location tracking
│   ├── admin_graph.html       # Graph visualization
│   └── admin_settings.html    # Settings page
├── .env                       # Environment variables
├── requirements.txt           # Python dependencies
├── README.md                  # This file
└── DEMO_MODE.md              # Demo mode documentation
```

## Features in Detail

### Graph Analytics
Interactive network visualization using vis.js showing:
- **Nodes**: Users (blue), Emails (yellow), IPs (red), Cities (green), Regions (purple), Countries (orange)
- **Edges**: Relationships between entities
- **Fraud Detection**: Highlights shared IPs and city mismatches
- **Statistics**: Total users, IPs, cities, regions, countries, suspicious IPs

### Statistics Dashboard
- **Overall Metrics**: Total revenue, order count, user count, average order value
- **User Analytics**: Per-user spending, order frequency, last order date
- **Order Details**: Expandable item lists with quantities and prices
- **Status Tracking**: Color-coded order statuses

### Location Tracking
- **Real-time Tracking**: Captures IP on every login and order
- **Geolocation Data**: City, region, country, latitude, longitude
- **Mismatch Detection**: Flags when detected city ≠ registered city
- **History**: Complete audit trail of all user locations

## Utilities

### Scripts
- **`init_db.py`** - Initialize database and create admin/test users
- **`generate_sample_data.py`** - Create 10 users with 3-5 orders each
- **`create_indexes.py`** - Create 28 PostgreSQL performance indexes
- **`analyze_queries.py`** - Analyze query plans and index usage
- **`check_db.py`** - Inspect database schema (if exists)

### Configuration Files
- **`.env`** - Database URL, JWT secret, demo mode flag
- **`requirements.txt`** - Python package dependencies
- **`config.py`** - Flask config, connection pool settings

## Troubleshooting

### Database Connection Errors
If you see `OperationalError: server closed the connection`:
1. Check `.env` has `?sslmode=require` for Azure PostgreSQL
2. Connection pool settings in `config.py` handle reconnections automatically
3. Retry logic is built into decorators (`@db_retry`, `@retry_on_db_error`)

### Demo Mode Not Working
1. Ensure `.env` has `DEMO_MODE=true`
2. Restart Flask application
3. Check banner appears at top of web pages

### Indexes Not Being Used
Small datasets use sequential scans (faster than indexes for <100 rows). Run `analyze_queries.py` to verify query plans. As data grows, PostgreSQL will automatically use indexes.

## Screenshots

### Web UI
- **Home Page**: Welcome page with menu preview
- **Menu**: Browse items by category with images
- **Cart**: Manage quantities and checkout
- **Orders**: Track order status and history

### Admin Dashboard
- **Statistics**: Revenue charts and user analytics
- **Graph**: Interactive network showing fraud patterns
- **Locations**: IP tracking with city mismatch alerts
- **Settings**: Toggle demo mode and view configuration

## API Examples

### Register User
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "email": "newuser@example.com",
    "password": "password123",
    "city": "Paris"
  }'
```

### Login
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "password": "password123"
  }'
```

### Place Order
```bash
curl -X POST http://localhost:5000/api/orders \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_token>" \
  -d '{
    "items": [
      {"menu_item_id": 1, "quantity": 2},
      {"menu_item_id": 3, "quantity": 1}
    ],
    "notes": "Extra napkins please"
  }'
```

### Get Statistics (Admin)
```bash
curl http://localhost:5000/api/orders/statistics \
  -H "Authorization: Bearer <admin_token>"
```

## Performance Benchmarks

Based on Microsoft Azure PostgreSQL best practices:
- **Query Response**: <50ms for indexed queries
- **Order Placement**: <200ms including IP geolocation
- **Graph Analytics**: <1s for 100+ users with 500+ relationships
- **Statistics**: <100ms for aggregations with indexes

## Security Considerations

- **Passwords**: Hashed with bcrypt
- **JWT Tokens**: 1-hour expiration
- **SQL Injection**: Protected by SQLAlchemy ORM
- **CORS**: Enabled for API access
- **IP Tracking**: Privacy considerations - stores user IPs
- **Demo Mode**: Should be disabled in production

## Future Enhancements

- [ ] Email notifications for orders
- [ ] Real-time order updates (WebSocket)
- [ ] Payment integration
- [ ] Delivery tracking
- [ ] Menu item ratings and reviews
- [ ] Multi-restaurant support
- [ ] Mobile app API
- [ ] Advanced fraud ML models
- [ ] Export analytics reports
- [ ] Custom notification rules

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT

