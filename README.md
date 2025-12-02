# fraud_detection_with_postgresql_graph_age_extension

Flask-based REST API for a restaurant management system with user authentication, menu management, and order tracking with IP geolocation.

## Features

- **User Authentication**: Register and login with JWT tokens
- **Role-Based Access**: Admin and regular user roles
- **Menu Management**: Admins can add, modify, and remove menu items
- **Order System**: Users can place orders with real-time IP tracking
- **IP Geolocation**: Tracks user location and compares with registered city
- **Location Verification**: Detects if orders are placed from unexpected locations

## Tech Stack

- Flask
- PostgreSQL with SQLAlchemy
- JWT for authentication
- IP geolocation with ipapi.co

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

## Running the Application

```powershell
python app.py
```

The API will be available at `http://localhost:5000`

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
