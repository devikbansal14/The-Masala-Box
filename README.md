# The Masala Box

> Real Spices. Real Masalas.

A full-featured e-commerce website for premium Indian spices and masala blends. Built with Flask, featuring user authentication, payment integration, order management, and an admin dashboard.

## Features

### Customer Features
- **User Authentication** - Signup, login, logout, forgot password
- **Product Catalog** - 4 Signature Blends + 4 Single Origin spices
- **Weight Options** - Single origin spices available in 200g, 500g, 1000g
- **Shopping Cart** - User-specific cart with quantity controls
- **Address Management** - Save multiple delivery addresses
- **Order Placement** - Complete checkout flow with address selection
- **Payment Integration** - Razorpay payment gateway (test mode supported)
- **Order History** - View past orders and their status
- **Search** - Find products by name, category, or description
- **Currency Selector** - INR (default), USD, GBP
- **Promo Codes** - WELCOME10 (10% off), FIRSTMASALA (INR 50 off)
- **Contact Form** - Send messages (stored in database)
- **WhatsApp Support** - Floating WhatsApp button for quick contact

### Admin Features
- **Secure Admin Panel** - Authentication required
- **Dashboard** - Orders, revenue, customers, products overview
- **Order Management** - View all orders, update status
- **Customer Management** - View all registered customers
- **Product Catalog** - View all products
- **Contact Messages** - View customer inquiries

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py

# Open in browser
http://localhost:5001

# Admin panel
http://localhost:5001/admin
```

## Project Structure

```
masala_lab/
├── app.py                  # Flask backend (routes & API)
├── config.py               # Site configuration
├── products.py             # Product catalog
├── create_images.py        # Product image generator
├── requirements.txt        # Python dependencies
├── masala_lab.db          # SQLite database (auto-generated)
│
├── static/
│   ├── css/styles.css     # All styles
│   ├── js/app.js          # Frontend JavaScript
│   └── images/            # Product images
│
├── templates/
│   ├── index.html         # Main storefront
│   └── admin.html         # Admin dashboard
│
├── README.md              # This file
├── GUIDE.md               # Developer guide
├── DESIGN.md              # Design system
└── CLAUDE.md              # AI assistant context
```

## User Flows

### Customer Journey
```
Homepage → Browse Products → Add to Cart → Login/Signup
    → Manage Addresses → Checkout → Payment → Order Confirmation
    → View Order History
```

### Admin Journey
```
/admin → Login (admin account) → Dashboard
    → Manage Orders (update status)
    → View Customers
    → View Contact Messages
```

## Configuration

Edit `config.py` to customize:

| Setting | Description |
|---------|-------------|
| `BRAND` | Name, tagline, logo text |
| `SHIPPING` | Free delivery threshold (INR 500), delivery fee (INR 50) |
| `PROMO_CODES` | Discount codes (percent or flat) |
| `WHATSAPP` | WhatsApp number for support |
| `EMAIL` | SMTP settings for notifications |
| `RAZORPAY` | Payment gateway credentials |
| `FLASK_CONFIG` | Port, debug mode, secret key |

## Creating an Admin User

1. First, create a regular account via signup
2. Then update the user in the database:

```bash
sqlite3 masala_lab.db "UPDATE users SET is_admin = 1 WHERE email = 'your-email@example.com';"
```

## API Endpoints

### Products
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/products` | List all products |
| GET | `/api/products/<id>` | Get product details |

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/signup` | Register new user |
| POST | `/api/auth/login` | Login |
| POST | `/api/auth/logout` | Logout |
| GET | `/api/auth/me` | Get current user |
| POST | `/api/auth/forgot-password` | Request password reset |
| POST | `/api/auth/reset-password` | Reset password with token |

### Cart (requires login)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/cart` | Get cart items |
| POST | `/api/cart/add` | Add to cart |
| POST | `/api/cart/update` | Update quantity |
| DELETE | `/api/cart/remove` | Remove from cart |

### Addresses (requires login)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/addresses` | List addresses |
| POST | `/api/addresses` | Add address |
| PUT | `/api/addresses/<id>` | Update address |
| DELETE | `/api/addresses/<id>` | Delete address |

### Orders (requires login)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/orders` | List user's orders |
| POST | `/api/orders` | Create order |
| GET | `/api/orders/<id>` | Get order details |

### Payment
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/payment/create` | Create Razorpay order |
| POST | `/api/payment/verify` | Verify payment |

### Admin (requires admin login)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/stats` | Dashboard statistics |
| GET | `/api/admin/orders` | All orders |
| PUT | `/api/admin/orders/<id>/status` | Update order status |
| GET | `/api/admin/customers` | All customers |
| GET | `/api/contact/messages` | Contact form messages |

## Products

### Signature Blends (200g kits)
| Product | Price (INR) |
|---------|-------------|
| The Heritage Blend - Garam Masala | 599 |
| The Mumbai Street - Pav Bhaji Masala | 549 |
| The Royal Handi - Biryani Masala | 699 |
| The Coastal Roast - Chicken Masala | 579 |

### Single Origin Spices (with weight options)
| Product | 200g | 500g | 1000g |
|---------|------|------|-------|
| Kashmiri Fire - Red Chilies | 299 | 649 | 1149 |
| Golden Root - Turmeric Fingers | 349 | 749 | 1349 |
| Golden Dust - Turmeric Powder | 379 | 849 | 1549 |
| Aroma Pods - Cardamom & Cloves | 449 | 999 | 1799 |

## Tech Stack

- **Backend:** Flask (Python 3.8+)
- **Database:** SQLite
- **Frontend:** Vanilla JavaScript (ES6+)
- **Styling:** Custom CSS with CSS variables
- **Fonts:** Playfair Display + Inter (Google Fonts)
- **Payment:** Razorpay
- **Auth:** Session-based with werkzeug password hashing

## Documentation

- **[GUIDE.md](GUIDE.md)** - Developer guide, API details, common tasks
- **[DESIGN.md](DESIGN.md)** - Design system, colors, typography, components

## Security Features

- Password hashing with werkzeug
- Session-based authentication
- Admin role protection
- Price validation (prevents manipulation)
- Protected admin API endpoints

## Browser Support

- Chrome, Firefox, Safari, Edge (latest versions)
- Mobile responsive (iOS Safari, Chrome Android)

---

Built with care for authentic Indian spices.

UPDATE users SET is_admin = 1 WHERE email = 'devikbansal14@gmail.com';