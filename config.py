"""
Site Configuration for The Masala Box
======================================
Edit this file to change site-wide settings.
"""

# Brand Settings
BRAND = {
    "name": "The Masala Box",
    "tagline": "Real Spices. Real Masalas",
    "logo_text": "MB",
    "year": 2026
}

# About Page Content
ABOUT = {
    "title": "Welcome to The Masala Box",
    "description": "We started with a passion for authentic spices, sourcing directly from farmers across India.",
    "mission": "To bring laboratory-grade precision to traditional spice blending, ensuring every blend is perfect.",
    "image_url": "/static/images/about-team.jpg"
}

# Shipping Configuration
SHIPPING = {
    "free_threshold": 500,  # Free delivery above this amount (INR)
    "delivery_fee": 50      # Delivery fee (INR)
}

# Promo Codes
# type: 'percent' for percentage discount, 'flat' for fixed amount
PROMO_CODES = {
    "WELCOME10": {"type": "percent", "value": 10},   # 10% off
    "FIRSTMASALA": {"type": "flat", "value": 50}     # INR 50 off
}

# Flask Configuration
FLASK_CONFIG = {
    "secret_key": "masala_box_secret_key_2026",
    "debug": True,
    "host": "0.0.0.0",
    "port": 5001
}

# Database
DATABASE = {
    "path": "masala_lab.db"
}

# WhatsApp Configuration
# Replace with your WhatsApp number (with country code, no + or spaces)
WHATSAPP = {
    "number": "917014182245",  # Format: country_code + number (e.g., 917014182245 for India)
    "default_message": "Hi! I'm interested in The Masala Box products."
}

# Razorpay Configuration
# Get your API keys from: https://dashboard.razorpay.com/app/keys
# Use TEST keys for development, LIVE keys for production
RAZORPAY = {
    "key_id": "rzp_test_xxxxxxxxxxxxx",      # Your Razorpay Key ID
    "key_secret": "xxxxxxxxxxxxxxxxxxxxxxxx",  # Your Razorpay Key Secret
    "currency": "INR"
}

# Email Configuration (Gmail)
# To use Gmail:
# 1. Enable 2-Factor Auth on your Google account
# 2. Generate an App Password: Google Account > Security > App Passwords
# 3. Use that app password below (not your regular password)
EMAIL = {
    "enabled": False,  # Set to True after configuring
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "devikbansal14@gmail.com",  # Your Gmail address
    "sender_password": "your-app-password",      # Gmail App Password (16 chars) - YOU NEED TO SET THIS
    "receiver_email": "devikbansal14@gmail.com"  # Where to receive contact form emails
}
