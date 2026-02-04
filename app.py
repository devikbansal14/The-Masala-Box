"""
The Masala Box - Flask Backend
==============================
Main application file handling routes and API endpoints.
"""

from flask import Flask, render_template, jsonify, request, session, redirect
import os
import uuid
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from werkzeug.security import generate_password_hash, check_password_hash
import re

# PostgreSQL
import psycopg2
import psycopg2.extras

# Import configuration
from config import BRAND, ABOUT, SHIPPING, PROMO_CODES, FLASK_CONFIG, WHATSAPP, EMAIL, RAZORPAY
from products import SIGNATURE_BLENDS, SINGLE_ORIGINS, ALL_PRODUCTS

# =============================================================================
# APP INITIALIZATION
# =============================================================================

app = Flask(__name__)
app.secret_key = FLASK_CONFIG['secret_key']

SITE_CONFIG = {
    "about_us": ABOUT,
    "shipping": SHIPPING
}

# =============================================================================
# DATABASE FUNCTIONS
# =============================================================================

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db():
    """Get a Postgres connection with dict cursor."""
    return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)

def init_db():
    """Initialize database tables in PostgreSQL."""
    conn = get_db()
    cursor = conn.cursor()

    # Products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            subtitle TEXT NOT NULL,
            tagline TEXT,
            description TEXT,
            price REAL NOT NULL,
            category TEXT NOT NULL,
            weight TEXT DEFAULT '200g',
            image_url TEXT,
            rating INTEGER DEFAULT 5,
            reviews INTEGER DEFAULT 0,
            allergy_info TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Ingredients table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ingredients (
            id SERIAL PRIMARY KEY,
            product_id INTEGER,
            ingredient_name TEXT NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')

    # Cart table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cart (
            id SERIAL PRIMARY KEY,
            user_id INTEGER,
            session_id TEXT,
            product_id INTEGER,
            quantity INTEGER DEFAULT 1,
            weight TEXT DEFAULT '200g',
            price_override REAL
        )
    ''')

    # Orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            order_number TEXT UNIQUE,
            user_id INTEGER,
            address_id INTEGER,
            subtotal REAL,
            discount REAL DEFAULT 0,
            delivery_fee REAL DEFAULT 0,
            total_amount REAL,
            promo_code TEXT,
            payment_status TEXT DEFAULT 'pending',
            payment_id TEXT,
            razorpay_order_id TEXT,
            order_status TEXT DEFAULT 'placed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Order items
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id SERIAL PRIMARY KEY,
            order_id INTEGER,
            product_id INTEGER,
            product_name TEXT,
            product_subtitle TEXT,
            weight TEXT DEFAULT '200g',
            quantity INTEGER,
            price REAL,
            FOREIGN KEY (order_id) REFERENCES orders(id)
        )
    ''')

    # Users
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            password_hash TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Password reset tokens
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            used INTEGER DEFAULT 0
        )
    ''')

    # Contact messages
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contact_messages (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            subject TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Addresses
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS addresses (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            label TEXT DEFAULT 'Home',
            full_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            address_line1 TEXT NOT NULL,
            address_line2 TEXT,
            city TEXT NOT NULL,
            state TEXT NOT NULL,
            pincode TEXT NOT NULL,
            is_default INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()

def seed_products():
    """Seed products from products.py if table is empty."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM products")
    count = cursor.fetchone()["count"]
    if count > 0:
        conn.close()
        return

    for product in ALL_PRODUCTS:
        cursor.execute('''
            INSERT INTO products (name, subtitle, tagline, description, price, category, image_url, rating, reviews, allergy_info)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            product['name'],
            product['subtitle'],
            product['tagline'],
            product['description'],
            product['price'],
            product['category'],
            product['image_url'],
            product['rating'],
            product['reviews'],
            product['allergy_info']
        ))
        pid = cursor.fetchone()["id"] if cursor.description else None

        for ingredient in product.get('ingredients', []):
            cursor.execute(
                "INSERT INTO ingredients (product_id, ingredient_name) VALUES (%s, %s)",
                (pid, ingredient)
            )

    conn.commit()
    conn.close()

# =============================================================================
# SESSION HELPERS
# =============================================================================

def get_session_id():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return session['session_id']

def is_admin():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT is_admin FROM users WHERE id = %s", (session.get('user_id'),))
    row = cursor.fetchone()
    conn.close()
    return row and row.get("is_admin") == 1

def require_admin():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Please login first'}), 401
    if not is_admin():
        return jsonify({'success': False, 'error': 'Admin access required'}), 403
    return None

def merge_guest_cart_to_user(user_id):
    session_id = session.get('session_id')
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT product_id, quantity, weight, price_override FROM cart WHERE session_id = %s AND user_id IS NULL", (session_id,))
    guests = cursor.fetchall()
    for item in guests:
        pid, qty, weight, po = item["product_id"], item["quantity"], item["weight"], item["price_override"]
        cursor.execute("SELECT id, quantity FROM cart WHERE user_id = %s AND product_id = %s AND weight = %s", (user_id, pid, weight))
        existing = cursor.fetchone()
        if existing:
            new_qty = existing["quantity"] + qty
            cursor.execute("UPDATE cart SET quantity = %s WHERE id = %s", (new_qty, existing["id"]))
        else:
            cursor.execute("INSERT INTO cart (user_id, product_id, quantity, weight, price_override) VALUES (%s, %s, %s, %s, %s)", (user_id, pid, qty, weight, po))
    cursor.execute("DELETE FROM cart WHERE session_id = %s AND user_id IS NULL", (session_id,))
    conn.commit()
    conn.close()

# =============================================================================
# REST OF ROUTES (UNCHANGED; omitted here for brevity)
# =============================================================================

# Paste your existing routes here EXACTLY as you already have them — 
# nothing needs to change because psycopg2 cursor returns dict-like rows.

# =============================================================================
# SERVER START
# =============================================================================

if __name__ == "__main__":
    with app.app_context():
        init_db()
        seed_products()
    app.run(
        debug=FLASK_CONFIG['debug'],
        host=FLASK_CONFIG['host'],
        port=FLASK_CONFIG['port']
    )
