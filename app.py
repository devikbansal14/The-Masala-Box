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
            RETURNING id
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
        pid = cursor.fetchone()["id"]

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

app = Flask(__name__)
app.secret_key = FLASK_CONFIG['secret_key']
with app.app_context():
    init_db()
    seed_products()

# =============================================================================
# REST OF ROUTES (UNCHANGED; omitted here for brevity)
# =============================================================================

@app.route('/')
def home():
    """Render homepage."""
    return render_template('index.html',
                           whatsapp_number=WHATSAPP['number'],
                           whatsapp_message=WHATSAPP['default_message'])


@app.route('/about')
def about():
    """Render about page."""
    return render_template('about.html', info=SITE_CONFIG['about_us'])


@app.route('/checkout', methods=['GET', 'POST'])
def checkout_page():
    """Render checkout page."""
    session_id = get_session_id()
    conn = get_db()
    cursor = conn.cursor()

    # Handle promo code submission
    token_received = ""
    if request.method == 'POST':
        token_received = request.form.get('token', '').upper()

    # Fetch cart items
    cursor.execute('''
        SELECT c.quantity, p.price
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.session_id = %s
    ''', (session_id,))
    items = cursor.fetchall()

    if not items and request.method == 'GET':
        return redirect('/')

    subtotal = sum(item['price'] * item['quantity'] for item in items)

    # Calculate discount (check if user has already used the promo code)
    discount = 0
    promo_error = None
    if token_received and token_received in PROMO_CODES:
        # Check if logged-in user has already used this promo code
        if 'user_id' in session:
            cursor.execute('''
                SELECT id FROM orders
                WHERE user_id = %s AND promo_code = %s
            ''', (session['user_id'], token_received))
            already_used = cursor.fetchone()
            if already_used:
                promo_error = f'You have already used the promo code {token_received}'
                token_received = ""
            else:
                promo = PROMO_CODES[token_received]
                if promo['type'] == 'percent':
                    discount = subtotal * (promo['value'] / 100)
                else:
                    discount = promo['value']
        else:
            promo = PROMO_CODES[token_received]
            if promo['type'] == 'percent':
                discount = subtotal * (promo['value'] / 100)
            else:
                discount = promo['value']
    elif token_received and token_received not in PROMO_CODES:
        promo_error = 'Invalid promo code'

    # Calculate delivery
    delivery_fee = 0 if subtotal >= SHIPPING['free_threshold'] else SHIPPING['delivery_fee']
    total = max(0, subtotal + delivery_fee - discount)

    conn.close()

    return render_template(
        'checkout.html',
        subtotal=subtotal,
        delivery_fee=delivery_fee,
        total=total,
        token_msg=token_received,
        promo_error=promo_error
    )


# =============================================================================
# PRODUCT API
# =============================================================================

@app.route('/api/products')
def get_products():
    """Get all products."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products ORDER BY category, id')
    products = [dict(row) for row in cursor.fetchall()]
    conn.close()

    # Add weight_options from products.py for single origin items
    for product in products:
        if product['category'] == 'single_origin':
            # Find matching product in SINGLE_ORIGINS
            for orig in SINGLE_ORIGINS:
                if orig['name'] == product['name']:
                    product['weight_options'] = orig.get('weight_options', {})
                    break

    return jsonify(products)


@app.route('/api/products/<int:product_id>')
def get_product(product_id):
    """Get single product with ingredients."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM products WHERE id = %s', (product_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return jsonify({'error': 'Product not found'}), 404

    product = dict(row)

    cursor.execute('SELECT ingredient_name FROM ingredients WHERE product_id = %s', (product_id,))
    ingredients = [row['ingredient_name'] for row in cursor.fetchall()]
    product['ingredients'] = ingredients

    conn.close()
    return jsonify(product)


# =============================================================================
# CART API
# =============================================================================

@app.route('/api/cart')
def get_cart():
    """Get cart items for current user or guest session."""
    conn = get_db()
    cursor = conn.cursor()

    # Check if user is logged in
    if 'user_id' in session:
        cursor.execute('''
            SELECT c.id, c.quantity, c.product_id, c.weight, c.price_override, p.*
            FROM cart c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = %s
        ''', (session['user_id'],))
    else:
        # Guest cart using session_id
        session_id = get_session_id()
        cursor.execute('''
            SELECT c.id, c.quantity, c.product_id, c.weight, c.price_override, p.*
            FROM cart c
            JOIN products p ON c.product_id = p.id
            WHERE c.session_id = %s AND c.user_id IS NULL
        ''', (session_id,))

    cart_items = []
    for row in cursor.fetchall():
        item = dict(row)
        # Use price_override if available, otherwise use default product price
        if item.get('price_override'):
            item['price'] = item['price_override']
        cart_items.append(item)

    conn.close()

    return jsonify(cart_items)


@app.route('/api/cart/add', methods=['POST'])
def add_to_cart():
    data = request.json or {}

    product_id = data.get('product_id')
    quantity = int(data.get('quantity', 1))
    weight = data.get('weight', '200g')
    price_override = data.get('price_override')

    if not product_id:
        return jsonify({'success': False, 'error': 'Product ID required'}), 400

    conn = get_db()
    cursor = conn.cursor()

    # 1️⃣ Validate product
    cursor.execute('SELECT * FROM products WHERE id = %s', (product_id,))
    product = cursor.fetchone()

    if not product:
        conn.close()
        return jsonify({'success': False, 'error': 'Product not found'}), 404

    # 2️⃣ Resolve correct price
    valid_price = product['price']

    if product['category'] == 'single_origin':
        for orig in SINGLE_ORIGINS:
            if orig['name'] == product['name']:
                weight_options = orig.get('weight_options', {})
                if weight not in weight_options:
                    conn.close()
                    return jsonify({'success': False, 'error': 'Invalid weight'}), 400
                valid_price = weight_options[weight]
                break

    if price_override is not None and float(price_override) != float(valid_price):
        conn.close()
        return jsonify({'success': False, 'error': 'Price tampering detected'}), 400

    price_override = valid_price

    # 3️⃣ Logged-in user cart
    if 'user_id' in session:
        cursor.execute(
            '''
            SELECT id, quantity FROM cart
            WHERE user_id = %s AND product_id = %s AND weight = %s
            ''',
            (session['user_id'], product_id, weight)
        )
        existing = cursor.fetchone()

        if existing:
            cursor.execute(
                'UPDATE cart SET quantity = %s WHERE id = %s',
                (existing['quantity'] + quantity, existing['id'])
            )
        else:
            cursor.execute(
                '''
                INSERT INTO cart (user_id, product_id, quantity, weight, price_override)
                VALUES (%s, %s, %s, %s, %s)
                ''',
                (session['user_id'], product_id, quantity, weight, price_override)
            )

    # 4️⃣ Guest cart
    else:
        session_id = get_session_id()
        cursor.execute(
            '''
            SELECT id, quantity FROM cart
            WHERE session_id = %s AND user_id IS NULL
              AND product_id = %s AND weight = %s
            ''',
            (session_id, product_id, weight)
        )
        existing = cursor.fetchone()

        if existing:
            cursor.execute(
                'UPDATE cart SET quantity = %s WHERE id = %s',
                (existing['quantity'] + quantity, existing['id'])
            )
        else:
            cursor.execute(
                '''
                INSERT INTO cart (session_id, product_id, quantity, weight, price_override)
                VALUES (%s, %s, %s, %s, %s)
                ''',
                (session_id, product_id, quantity, weight, price_override)
            )

    conn.commit()
    conn.close()

    return jsonify({'success': True})



@app.route('/api/cart/update', methods=['POST'])
def update_cart_quantity():
    """Update item quantity in cart (works for both logged-in users and guests)."""
    data = request.json
    product_id = data.get('product_id')
    action = data.get('action')  # 'increase' or 'decrease'
    weight = data.get('weight', '200g')

    conn = get_db()
    cursor = conn.cursor()

    # Check if user is logged in or guest
    if 'user_id' in session:
        cursor.execute(
            'SELECT id, quantity FROM cart WHERE user_id = %s AND product_id = %s AND weight = %s',
            (session['user_id'], product_id, weight)
        )
    else:
        session_id = get_session_id()
        cursor.execute(
            'SELECT id, quantity FROM cart WHERE session_id = %s AND user_id IS NULL AND product_id = %s AND weight = %s',
            (session_id, product_id, weight)
        )

    row = cursor.fetchone()

    if row:
        cart_id = row['id']
        current_qty = row['quantity']
        new_qty = current_qty + 1 if action == 'increase' else current_qty - 1

        if new_qty <= 0:
            cursor.execute('DELETE FROM cart WHERE id = %s', (cart_id,))
        else:
            cursor.execute('UPDATE cart SET quantity = %s WHERE id = %s', (new_qty, cart_id))

    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/cart/remove', methods=['DELETE'])
def remove_from_cart():
    """Remove item from cart (works for both logged-in users and guests)."""
    product_id = request.json.get('product_id')
    weight = request.json.get('weight', '200g')

    conn = get_db()
    cursor = conn.cursor()

    # Check if user is logged in or guest
    if 'user_id' in session:
        cursor.execute(
            'DELETE FROM cart WHERE user_id = %s AND product_id = %s AND weight = %s',
            (session['user_id'], product_id, weight)
        )
    else:
        session_id = get_session_id()
        cursor.execute(
            'DELETE FROM cart WHERE session_id = %s AND user_id IS NULL AND product_id = %s AND weight = %s',
            (session_id, product_id, weight)
        )

    conn.commit()
    conn.close()

    return jsonify({'success': True})


@app.route('/api/promo/validate', methods=['POST'])
def validate_promo_code():
    """Validate a promo code and check if user has already used it."""
    data = request.json
    promo_code = data.get('promo_code', '').upper().strip()

    if not promo_code:
        return jsonify({'valid': False, 'error': 'Promo code is required'}), 400

    # Check if promo code exists
    if promo_code not in PROMO_CODES:
        return jsonify({'valid': False, 'error': 'Invalid promo code'}), 400

    # If user is logged in, check if they've already used this code
    if 'user_id' in session:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id FROM orders
            WHERE user_id = %s AND promo_code = %s
        ''', (session['user_id'], promo_code))
        already_used = cursor.fetchone()
        conn.close()

        if already_used:
            return jsonify({
                'valid': False,
                'error': f'You have already used the promo code {promo_code}'
            }), 400

    # Promo code is valid and available for use
    promo = PROMO_CODES[promo_code]
    return jsonify({
        'valid': True,
        'promo_code': promo_code,
        'type': promo['type'],
        'value': promo['value']
    })


# =============================================================================
# AUTHENTICATION API
# =============================================================================

def validate_email(email):
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


@app.route('/api/auth/signup', methods=['POST'])
def signup():
    """Register a new user."""
    data = request.json
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    phone = data.get('phone', '').strip()
    password = data.get('password', '')

    # Validation
    if not name or len(name) < 2:
        return jsonify({'success': False, 'error': 'Name must be at least 2 characters'}), 400

    if not validate_email(email):
        return jsonify({'success': False, 'error': 'Invalid email address'}), 400

    if len(password) < 6:
        return jsonify({'success': False, 'error': 'Password must be at least 6 characters'}), 400

    conn = get_db()
    cursor = conn.cursor()

    # Check if email already exists
    cursor.execute('SELECT id FROM users WHERE email = %s', (email,))
    if cursor.fetchone():
        conn.close()
        return jsonify({'success': False, 'error': 'Email already registered'}), 400

    # Create user
    password_hash = generate_password_hash(password)
    cursor.execute(
        '''
        INSERT INTO users (name, email, phone, password_hash)
        VALUES (%s, %s, %s, %s)
        RETURNING id
        ''',
        (name, email, phone, password_hash)
    )
    user_id = cursor.fetchone()['id']
    conn.commit()
    conn.close()

    # Set session
    session['user_id'] = user_id
    session['user_name'] = name
    session['user_email'] = email

    # Merge guest cart into user's cart
    merge_guest_cart_to_user(user_id)

    return jsonify({
        'success': True,
        'user': {'id': user_id, 'name': name, 'email': email}
    })


@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login user."""
    data = request.json
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'success': False, 'error': 'Email and password required'}), 400

    conn = get_db()
    # conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
    user = cursor.fetchone()
    conn.close()

    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({'success': False, 'error': 'Invalid email or password'}), 401

    # Set session
    session['user_id'] = user['id']
    session['user_name'] = user['name']
    session['user_email'] = user['email']

    # Merge guest cart into user's cart
    merge_guest_cart_to_user(user['id'])

    return jsonify({
        'success': True,
        'user': {'id': user['id'], 'name': user['name'], 'email': user['email']}
    })


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Logout user."""
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('user_email', None)
    return jsonify({'success': True})


@app.route('/api/auth/me')
def get_current_user():
    """Get current logged in user."""
    if 'user_id' in session:
        return jsonify({
            'logged_in': True,
            'user': {
                'id': session['user_id'],
                'name': session['user_name'],
                'email': session['user_email']
            }
        })
    return jsonify({'logged_in': False})


@app.route('/api/auth/forgot-password', methods=['POST'])
def forgot_password():
    """Request password reset."""
    import secrets
    from datetime import timedelta

    data = request.json
    email = data.get('email', '').strip().lower()

    if not email:
        return jsonify({'success': False, 'error': 'Email is required'}), 400

    conn = get_db()
    # conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Find user by email
    cursor.execute('SELECT id, name FROM users WHERE email = %s', (email,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        # Don't reveal if email exists or not (security)
        return jsonify({
            'success': True,
            'message': 'If an account with that email exists, a reset link has been sent.'
        })

    # Generate reset token
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(hours=1)  # Token valid for 1 hour

    # Invalidate any existing tokens for this user
    cursor.execute('UPDATE password_reset_tokens SET used = 1 WHERE user_id = %s', (user['id'],))

    # Create new token
    cursor.execute('''
        INSERT INTO password_reset_tokens (user_id, token, expires_at)
        VALUES (%s, %s, %s)
    ''', (user['id'], token, expires_at))

    conn.commit()
    conn.close()

    # In a real app, send email here. For now, we'll return the token for testing
    # (In production, NEVER return the token in response - only send via email)
    reset_url = f"/reset-password?token={token}"

    # Try to send email if configured
    if EMAIL.get('enabled'):
        try:
            msg = MIMEMultipart()
            msg['From'] = EMAIL['sender_email']
            msg['To'] = email
            msg['Subject'] = "Password Reset - The Masala Box"

            body = f"""
Hi {user['name']},

You requested a password reset for your Masala Box account.

Click this link to reset your password (valid for 1 hour):
{reset_url}

If you didn't request this, please ignore this email.

- The Masala Box Team
            """

            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP(EMAIL['smtp_server'], EMAIL['smtp_port'])
            server.starttls()
            server.login(EMAIL['sender_email'], EMAIL['sender_password'])
            server.send_message(msg)
            server.quit()
        except Exception as e:
            print(f"Failed to send reset email: {e}")

    # For testing purposes, return the token (remove in production!)
    return jsonify({
        'success': True,
        'message': 'If an account with that email exists, a reset link has been sent.',
        'debug_token': token  # Remove this in production
    })


@app.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    """Reset password using token."""
    data = request.json
    token = data.get('token', '').strip()
    new_password = data.get('password', '')

    if not token:
        return jsonify({'success': False, 'error': 'Reset token is required'}), 400

    if len(new_password) < 6:
        return jsonify({'success': False, 'error': 'Password must be at least 6 characters'}), 400

    conn = get_db()
    # conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Find valid token
    cursor.execute('''
        SELECT t.*, u.email, u.name FROM password_reset_tokens t
        JOIN users u ON t.user_id = u.id
        WHERE t.token = %s AND t.used = 0 AND t.expires_at > NOW()
    ''', (token,))
    token_row = cursor.fetchone()

    if not token_row:
        conn.close()
        return jsonify({'success': False, 'error': 'Invalid or expired reset link'}), 400

    # Update password
    password_hash = generate_password_hash(new_password)
    cursor.execute('UPDATE users SET password_hash = %s WHERE id = %s', (password_hash, token_row['user_id']))

    # Mark token as used
    cursor.execute('UPDATE password_reset_tokens SET used = 1 WHERE id = %s', (token_row['id'],))

    conn.commit()
    conn.close()

    return jsonify({
        'success': True,
        'message': 'Password has been reset successfully. You can now login.'
    })


# =============================================================================
# ADDRESS API
# =============================================================================

@app.route('/api/addresses')
def get_addresses():
    """Get all addresses for logged in user."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Please login first'}), 401

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT * FROM addresses WHERE user_id = %s ORDER BY is_default DESC, created_at DESC',
        (session['user_id'],)
    )
    addresses = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return jsonify({'success': True, 'addresses': addresses})


@app.route('/api/addresses', methods=['POST'])
def add_address():
    """Add a new address."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Please login first'}), 401

    data = request.json
    required_fields = ['full_name', 'phone', 'address_line1', 'city', 'state', 'pincode']

    for field in required_fields:
        if not data.get(field, '').strip():
            return jsonify({'success': False, 'error': f'{field.replace("_", " ").title()} is required'}), 400

    conn = get_db()
    cursor = conn.cursor()

    # If this is the first address or marked as default, update others
    is_default = data.get('is_default', False)
    if is_default:
        cursor.execute('UPDATE addresses SET is_default = 0 WHERE user_id = %s', (session['user_id'],))

    # Check if this is user's first address (make it default)
    cursor.execute('SELECT COUNT(*) FROM addresses WHERE user_id = %s', (session['user_id'],))
    if cursor.fetchone()['count'] == 0:
        is_default = True

    cursor.execute('''
        INSERT INTO addresses (user_id, label, full_name, phone, address_line1, address_line2, city, state, pincode, is_default)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    ''', (
        session['user_id'],
        data.get('label', 'Home'),
        data['full_name'].strip(),
        data['phone'].strip(),
        data['address_line1'].strip(),
        data.get('address_line2', '').strip(),
        data['city'].strip(),
        data['state'].strip(),
        data['pincode'].strip(),
        1 if is_default else 0
    ))

    address_id = cursor.fetchone()['id']
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'address_id': address_id})


@app.route('/api/addresses/<int:address_id>', methods=['PUT'])
def update_address(address_id):
    """Update an existing address."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Please login first'}), 401

    data = request.json

    conn = get_db()
    cursor = conn.cursor()

    # Verify address belongs to user
    cursor.execute('SELECT id FROM addresses WHERE id = %s AND user_id = %s', (address_id, session['user_id']))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'success': False, 'error': 'Address not found'}), 404

    # If setting as default, unset others
    if data.get('is_default'):
        cursor.execute('UPDATE addresses SET is_default = 0 WHERE user_id = %s', (session['user_id'],))

    cursor.execute('''
        UPDATE addresses SET
            label = %s, full_name = %s, phone = %s, address_line1 = %s,
            address_line2 = %s, city = %s, state = %s, pincode = %s, is_default = %s
        WHERE id = %s AND user_id = %s
    ''', (
        data.get('label', 'Home'),
        data.get('full_name', ''),
        data.get('phone', ''),
        data.get('address_line1', ''),
        data.get('address_line2', ''),
        data.get('city', ''),
        data.get('state', ''),
        data.get('pincode', ''),
        1 if data.get('is_default') else 0,
        address_id,
        session['user_id']
    ))

    conn.commit()
    conn.close()

    return jsonify({'success': True})


@app.route('/api/addresses/<int:address_id>', methods=['DELETE'])
def delete_address(address_id):
    """Delete an address."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Please login first'}), 401

    conn = get_db()
    cursor = conn.cursor()

    # Verify address belongs to user
    cursor.execute('SELECT is_default FROM addresses WHERE id = %s AND user_id = %s', (address_id, session['user_id']))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({'success': False, 'error': 'Address not found'}), 404

    was_default = row['is_default']

    cursor.execute('DELETE FROM addresses WHERE id = %s AND user_id = %s', (address_id, session['user_id']))

    # If deleted address was default, make another one default
    if was_default:
        cursor.execute('''
            UPDATE addresses SET is_default = 1
            WHERE id = (
                SELECT id FROM addresses
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT 1
            )
        ''', (session['user_id'],))

    conn.commit()
    conn.close()

    return jsonify({'success': True})


@app.route('/api/addresses/<int:address_id>/default', methods=['POST'])
def set_default_address(address_id):
    """Set an address as default."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Please login first'}), 401

    conn = get_db()
    cursor = conn.cursor()

    # Verify address belongs to user
    cursor.execute('SELECT id FROM addresses WHERE id = %s AND user_id = %s', (address_id, session['user_id']))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'success': False, 'error': 'Address not found'}), 404

    # Unset all defaults, then set this one
    cursor.execute('UPDATE addresses SET is_default = 0 WHERE user_id = %s', (session['user_id'],))
    cursor.execute('UPDATE addresses SET is_default = 1 WHERE id = %s', (address_id,))

    conn.commit()
    conn.close()

    return jsonify({'success': True})


# =============================================================================
# ORDER MANAGEMENT API
# =============================================================================

def generate_order_number():
    """Generate unique order number."""
    import random
    import string
    timestamp = datetime.now().strftime('%Y%m%d')
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"MB{timestamp}{random_str}"


@app.route('/api/orders', methods=['POST'])
def create_order():
    """Create a new order."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Please login first'}), 401

    data = request.json
    address_id = data.get('address_id')
    promo_code = data.get('promo_code', '').upper()

    if not address_id:
        return jsonify({'success': False, 'error': 'Please select a delivery address'}), 400

    conn = get_db()
    # conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Verify address belongs to user
    cursor.execute('SELECT * FROM addresses WHERE id = %s AND user_id = %s', (address_id, session['user_id']))
    address = cursor.fetchone()
    if not address:
        conn.close()
        return jsonify({'success': False, 'error': 'Invalid address'}), 400

    # Get cart items
    cursor.execute('''
        SELECT c.*, p.name, p.subtitle, p.price as product_price
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = %s
    ''', (session['user_id'],))
    cart_items = cursor.fetchall()

    if not cart_items:
        conn.close()
        return jsonify({'success': False, 'error': 'Cart is empty'}), 400

    # Calculate totals
    subtotal = sum((item['price_override'] or item['product_price']) * item['quantity'] for item in cart_items)

    # Apply promo code (only if user hasn't used it before)
    discount = 0
    promo_error = None
    if promo_code and promo_code in PROMO_CODES:
        # Check if user has already used this promo code
        cursor.execute('''
            SELECT id FROM orders
            WHERE user_id = %s AND promo_code = %s
        ''', (session['user_id'], promo_code))
        already_used = cursor.fetchone()

        if already_used:
            promo_error = f'You have already used the promo code {promo_code}'
            promo_code = None  # Don't apply the code
        else:
            promo = PROMO_CODES[promo_code]
            if promo['type'] == 'percent':
                discount = subtotal * (promo['value'] / 100)
            else:
                discount = min(promo['value'], subtotal)
    elif promo_code and promo_code not in PROMO_CODES:
        promo_error = 'Invalid promo code'
        promo_code = None

    # Delivery fee
    delivery_fee = 0 if subtotal >= SHIPPING['free_threshold'] else SHIPPING['delivery_fee']
    total_amount = subtotal - discount + delivery_fee

    # Create order
    order_number = generate_order_number()
    cursor.execute('''
        INSERT INTO orders (order_number, user_id, address_id, subtotal, discount, delivery_fee, total_amount, promo_code)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    ''', (order_number, session['user_id'], address_id, subtotal, discount, delivery_fee, total_amount, promo_code or None))

    order_id = cursor.fetchone()['id']

    # Add order items
    for item in cart_items:
        price = item['price_override'] or item['product_price']
        cursor.execute('''
            INSERT INTO order_items (order_id, product_id, product_name, product_subtitle, weight, quantity, price)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (order_id, item['product_id'], item['name'], item['subtitle'], item['weight'], item['quantity'], price))

    # Clear cart
    cursor.execute('DELETE FROM cart WHERE user_id = %s', (session['user_id'],))

    conn.commit()
    conn.close()

    response = {
        'success': True,
        'order': {
            'id': order_id,
            'order_number': order_number,
            'total_amount': total_amount
        }
    }
    if promo_error:
        response['promo_warning'] = promo_error
    return jsonify(response)


@app.route('/api/orders')
def get_user_orders():
    """Get all orders for logged in user."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Please login first'}), 401

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT o.*, a.full_name as address_name, a.city, a.pincode
        FROM orders o
        LEFT JOIN addresses a ON o.address_id = a.id
        WHERE o.user_id = %s
        ORDER BY o.created_at DESC
    ''', (session['user_id'],))
    orders = [dict(row) for row in cursor.fetchall()]

    # Get items for each order
    for order in orders:
        cursor.execute('SELECT * FROM order_items WHERE order_id = %s', (order['id'],))
        order['items'] = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return jsonify({'success': True, 'orders': orders})


@app.route('/api/orders/<int:order_id>')
def get_order_details(order_id):
    """Get details of a specific order."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Please login first'}), 401

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT o.*, a.*
        FROM orders o
        LEFT JOIN addresses a ON o.address_id = a.id
        WHERE o.id = %s AND o.user_id = %s
    ''', (order_id, session['user_id']))
    order = cursor.fetchone()

    if not order:
        conn.close()
        return jsonify({'success': False, 'error': 'Order not found'}), 404

    order_dict = dict(order)

    cursor.execute('SELECT * FROM order_items WHERE order_id = %s', (order_id,))
    order_dict['items'] = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return jsonify({'success': True, 'order': order_dict})


# =============================================================================
# PAYMENT API (Razorpay)
# =============================================================================

@app.route('/api/payment/create', methods=['POST'])
def create_payment():
    """Create Razorpay payment order."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Please login first'}), 401

    data = request.json
    order_id = data.get('order_id')

    conn = get_db()
    cursor = conn.cursor()

    # Get order
    cursor.execute('SELECT * FROM orders WHERE id = %s AND user_id = %s', (order_id, session['user_id']))
    order = cursor.fetchone()

    if not order:
        conn.close()
        return jsonify({'success': False, 'error': 'Order not found'}), 404

    order_dict = dict(order)

    # Check if Razorpay is enabled
    if not RAZORPAY_ENABLED or not razorpay_client:
        conn.close()
        return jsonify({
            'success': True,
            'test_mode': True,
            'order_id': order_id,
            'amount': order_dict['total_amount'],
            'message': 'Razorpay not configured. Use test mode.'
        })

    try:
        # Create Razorpay order
        amount_paise = int(order_dict['total_amount'] * 100)  # Convert to paise
        razorpay_order = razorpay_client.order.create({
            'amount': amount_paise,
            'currency': RAZORPAY['currency'],
            'receipt': order_dict['order_number'],
            'payment_capture': 1
        })

        # Update order with razorpay order id
        cursor.execute(
            'UPDATE orders SET razorpay_order_id = %s WHERE id = %s',
            (razorpay_order['id'], order_id)
        )
        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'razorpay_order_id': razorpay_order['id'],
            'razorpay_key': RAZORPAY['key_id'],
            'amount': amount_paise,
            'currency': RAZORPAY['currency'],
            'order_number': order_dict['order_number']
        })

    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/payment/verify', methods=['POST'])
def verify_payment():
    """Verify Razorpay payment."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Please login first'}), 401

    data = request.json
    order_id = data.get('order_id')
    razorpay_payment_id = data.get('razorpay_payment_id')
    razorpay_order_id = data.get('razorpay_order_id')
    razorpay_signature = data.get('razorpay_signature')
    test_mode = data.get('test_mode', False)

    conn = get_db()
    cursor = conn.cursor()

    # Get order
    cursor.execute('SELECT * FROM orders WHERE id = %s AND user_id = %s', (order_id, session['user_id']))
    order = cursor.fetchone()

    if not order:
        conn.close()
        return jsonify({'success': False, 'error': 'Order not found'}), 404

    if test_mode or not RAZORPAY_ENABLED:
        # Test mode - mark as paid without verification
        cursor.execute('''
            UPDATE orders SET payment_status = 'paid', payment_id = %s, order_status = 'confirmed', updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        ''', (f'TEST_{order_id}', order_id))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Payment successful (test mode)'})

    try:
        # Verify signature
        import hmac
        import hashlib

        message = f"{razorpay_order_id}|{razorpay_payment_id}"
        generated_signature = hmac.new(
            RAZORPAY['key_secret'].encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()

        if generated_signature != razorpay_signature:
            conn.close()
            return jsonify({'success': False, 'error': 'Payment verification failed'}), 400

        # Update order
        cursor.execute('''
            UPDATE orders SET payment_status = 'paid', payment_id = %s, order_status = 'confirmed', updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        ''', (razorpay_payment_id, order_id))
        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Payment verified successfully'})

    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# CONTACT FORM API
# =============================================================================

def send_email(name, email, subject, message):
    """Send contact form email."""
    if not EMAIL.get('enabled'):
        print(f"Email disabled. Contact form submission from {name} ({email}): {subject}")
        return True  # Return success even if email is disabled (for testing)

    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL['sender_email']
        msg['To'] = EMAIL['receiver_email']
        msg['Subject'] = f"[The Masala Box] Contact: {subject}"

        body = f"""
New contact form submission from The Masala Box website:

Name: {name}
Email: {email}
Subject: {subject}

Message:
{message}

---
This email was sent from your website's contact form.
        """

        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(EMAIL['smtp_server'], EMAIL['smtp_port'])
        server.starttls()
        server.login(EMAIL['sender_email'], EMAIL['sender_password'])
        server.send_message(msg)
        server.quit()

        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False


@app.route('/api/contact', methods=['POST'])
def contact_form():
    """Handle contact form submission."""
    data = request.json
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    subject = data.get('subject', '').strip()
    message = data.get('message', '').strip()

    # Validation
    if not all([name, email, subject, message]):
        return jsonify({'success': False, 'error': 'All fields are required'}), 400

    # Store in database
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO contact_messages (name, email, subject, message) VALUES (%s, %s, %s, %s)',
        (name, email, subject, message)
    )
    conn.commit()
    conn.close()

    # Also try to send email
    send_email(name, email, subject, message)

    return jsonify({'success': True, 'message': 'Message sent successfully!'})


@app.route('/api/contact/messages')
def get_contact_messages():
    """Get all contact form messages (admin only)."""
    auth_error = require_admin()
    if auth_error:
        return auth_error
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM contact_messages ORDER BY created_at DESC')
    messages = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({'success': True, 'messages': messages})


# =============================================================================
# ADMIN API
# =============================================================================

@app.route('/admin')
def admin_panel():
    """Render admin panel."""
    # Check if user is logged in and is admin
    if 'user_id' not in session:
        return render_template('admin.html', authenticated=False, is_admin=False)
    if not is_admin():
        return render_template('admin.html', authenticated=True, is_admin=False)
    return render_template('admin.html', authenticated=True, is_admin=True)


@app.route('/api/admin/stats')
def admin_stats():
    """Get dashboard statistics."""
    auth_error = require_admin()
    if auth_error:
        return auth_error
    conn = get_db()
    cursor = conn.cursor()

    # Total orders
    cursor.execute('SELECT COUNT(*) FROM orders')
    total_orders = cursor.fetchone()['count']

    # Total revenue (only paid orders)
    cursor.execute("""
        SELECT COALESCE(SUM(total_amount), 0) AS total_revenue
        FROM orders
        WHERE payment_status = 'paid'
    """)
    total_revenue = cursor.fetchone()['total_revenue']

    # Total customers
    cursor.execute('SELECT COUNT(*) FROM users')
    total_customers = cursor.fetchone()['count']

    # Total products
    cursor.execute('SELECT COUNT(*) FROM products')
    total_products = cursor.fetchone()['count']

    # Recent orders
    cursor.execute('''
        SELECT o.*, u.name as customer_name
        FROM orders o
        LEFT JOIN users u ON o.user_id = u.id
        ORDER BY o.created_at DESC
        LIMIT 5
    ''')
    recent_orders = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return jsonify({
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'total_customers': total_customers,
        'total_products': total_products,
        'recent_orders': recent_orders
    })


@app.route('/api/admin/orders')
def admin_orders():
    """Get all orders for admin."""
    auth_error = require_admin()
    if auth_error:
        return auth_error
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT o.*, u.name as customer_name, u.email as customer_email,
               (SELECT COUNT(*) FROM order_items WHERE order_id = o.id) as item_count
        FROM orders o
        LEFT JOIN users u ON o.user_id = u.id
        ORDER BY o.created_at DESC
    ''')
    orders = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return jsonify({'orders': orders})


@app.route('/api/admin/orders/<int:order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    """Update order status."""
    auth_error = require_admin()
    if auth_error:
        return auth_error
    data = request.json
    new_status = data.get('status')

    valid_statuses = ['placed', 'confirmed', 'shipped', 'delivered', 'cancelled']
    if new_status not in valid_statuses:
        return jsonify({'success': False, 'error': 'Invalid status'}), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        'UPDATE orders SET order_status = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s',
        (new_status, order_id)
    )

    conn.commit()
    conn.close()

    return jsonify({'success': True})


@app.route('/api/admin/auth/check')
def admin_auth_check():
    """Check if current user is authenticated as admin."""
    if 'user_id' not in session:
        return jsonify({'authenticated': False, 'is_admin': False})
    return jsonify({
        'authenticated': True,
        'is_admin': is_admin(),
        'user': {
            'id': session.get('user_id'),
            'name': session.get('user_name'),
            'email': session.get('user_email')
        }
    })


@app.route('/api/admin/customers')
def admin_customers():
    """Get all customers for admin."""
    auth_error = require_admin()
    if auth_error:
        return auth_error
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT u.*, (SELECT COUNT(*) FROM orders WHERE user_id = u.id) as order_count
        FROM users u
        ORDER BY u.created_at DESC
    ''')
    customers = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return jsonify({'customers': customers})


# Paste your existing routes here EXACTLY as you already have them — 
# nothing needs to change because psycopg2 cursor returns dict-like rows.

# =============================================================================
# SERVER START
# =============================================================================

