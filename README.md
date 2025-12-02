# Restaurant Management System

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

- **users**: User accounts with authentication
- **menu_items**: Restaurant menu items
- **orders**: Customer orders
- **order_items**: Items within each order
- **user_locations**: IP tracking and geolocation history

## Development

To reset the database:
```powershell
python init_db.py
```

## License

MIT
