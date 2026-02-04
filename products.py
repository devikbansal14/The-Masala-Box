"""
Product Catalog for The Masala Box
===================================

HOW TO ADD A NEW PRODUCT:
1. Add product dict to SIGNATURE_BLENDS or SINGLE_ORIGINS list
2. Run: python create_images.py (if new image needed)
3. Delete masala_lab.db and restart app

PRODUCT STRUCTURE:
{
    'name': 'Product Name',           # Display name
    'subtitle': 'Variant/Type',       # e.g., "Garam Masala"
    'tagline': 'Short catchy phrase', # e.g., "Warm, Aromatic & Comforting"
    'description': 'Full description of the product...',
    'price': 599,                     # Price in INR (no decimals)
    'category': 'signature_blend',    # or 'single_origin'
    'image_url': '/static/images/filename.jpg',
    'rating': 5,                      # 1-5 star rating
    'reviews': 100,                   # Number of reviews
    'allergy_info': 'Allergy warning or None',
    'ingredients': ['Item 1', 'Item 2', ...]  # Empty list for single origin
}
"""

# =============================================================================
# SIGNATURE BLENDS (Premium masala kits with multiple spices)
# =============================================================================

SIGNATURE_BLENDS = [
    {
        'name': 'The Heritage Blend',
        'subtitle': 'Garam Masala',
        'tagline': 'Warm, Aromatic & Comforting',
        'description': 'Experience the soul of Indian cooking. Our Heritage Blend Garam Masala kit provides purest whole spices in precise proportions for a warm, aromatic and comforting masala. Roast and grind at home for unparalleled flavor. Makes 200g of fresh masala.',
        'price': 599,
        'category': 'signature_blend',
        'image_url': '/static/images/garam-masala.png',
        'rating': 5,
        'reviews': 145,
        'allergy_info': 'Contains Nutmeg & Black Pepper. These ingredients in separate pods. Keep closed or discard if allergic.',
        'ingredients': [
            'Coriander Seeds',
            'Cumin Seeds',
            'Black Peppercorns',
            'Cinnamon Sticks',
            'Whole Cloves',
            'Black Cardamom',
            'Mace Blades',
            'Nutmeg'
        ]
    },
    {
        'name': 'The Mumbai Street',
        'subtitle': 'Pav Bhaji Masala',
        'tagline': 'Tangy, Spicy & Vibrant',
        'description': 'Capture the essence of Mumbai street food. Our Pav Bhaji Masala brings together the perfect balance of tangy, spicy, and aromatic flavors. Roast and grind for authentic street-style taste. Makes 200g of fresh masala.',
        'price': 549,
        'category': 'signature_blend',
        'image_url': '/static/images/pav-bhaji.png',
        'rating': 5,
        'reviews': 132,
        'allergy_info': 'Contains Fennel Seeds & Dried Mango. These ingredients in separate pods. Keep closed or discard if allergic.',
        'ingredients': [
            'Coriander Seeds',
            'Cumin Seeds',
            'Dried Red Chilies',
            'Dry Mango Powder (Amchur)',
            'Fennel Seeds',
            'Black Peppercorns',
            'Kasuri Methi (Dried Fenugreek)',
            'Black Salt'
        ]
    },
    {
        'name': 'The Royal Handi',
        'subtitle': 'Biryani Masala',
        'tagline': 'Bold, Fragrant & Complex',
        'description': 'Create restaurant-quality biryani at home. Our Royal Handi Biryani Masala features aromatic whole spices including precious saffron threads and dried rose petals. Roast and grind for an unforgettable biryani experience. Makes 200g of fresh masala.',
        'price': 699,
        'category': 'signature_blend',
        'image_url': '/static/images/biryani.png',
        'rating': 5,
        'reviews': 185,
        'allergy_info': 'Contains Star Anise & Cinnamon. These ingredients in separate pods. Simply keep closed or discard if allergic.',
        'ingredients': [
            'Green Cardamom',
            'Star Anise',
            'Bay Leaves',
            'Cinnamon Sticks',
            'Whole Cloves',
            'Mace Blades',
            'Saffron Threads',
            'Dried Rose Petals'
        ]
    },
    {
        'name': 'The Coastal Roast',
        'subtitle': 'Chicken Masala',
        'tagline': 'Robust & Flavorful',
        'description': 'Bring coastal Indian flavors to your kitchen. Our Chicken Masala combines robust spices with subtle coconut notes for the perfect chicken curry. Roast and grind at home for authentic taste. Makes 200g of fresh masala.',
        'price': 579,
        'category': 'signature_blend',
        'image_url': '/static/images/chicken-masala.png',
        'rating': 5,
        'reviews': 165,
        'allergy_info': 'Contains Coconut & Stone Flower. These ingredients in separate pods. Discard if allergic.',
        'ingredients': [
            'Coriander Seeds',
            'Black Cardamom',
            'Black Peppercorns',
            'Dried Red Chilies',
            'Cumin Seeds',
            'Fennel Seeds',
            'Stone Flower (Kalpasi)',
            'Coconut Bits'
        ]
    }
]

# =============================================================================
# SINGLE ORIGIN SPICES (Individual premium spices)
# =============================================================================

SINGLE_ORIGINS = [
    {
        'name': 'Kashmiri Fire',
        'subtitle': 'Whole Red Chilies',
        'tagline': 'Mild heat, vibrant color',
        'description': 'Premium Kashmiri red chilies known for their vibrant color and mild heat. Perfect for adding color without overwhelming spice.',
        'price': 299,
        'category': 'single_origin',
        'image_url': '/static/images/RedChilli.png',
        'rating': 5,
        'reviews': 89,
        'allergy_info': None,
        'ingredients': [],
        'weight_options': {
            '200g': 299,
            '500g': 649,
            '1000g': 1149
        }
    },
    {
        'name': 'Golden Root',
        'subtitle': 'Turmeric Fingers',
        'tagline': 'High curcumin content',
        'description': 'Whole turmeric fingers with high curcumin content for maximum health benefits. Sourced from Salem, Tamil Nadu.',
        'price': 349,
        'category': 'single_origin',
        # 'image_url': '/static/images/turmeric-fingers.jpg',
        'image_url': '/static/images/Turmeric.png',
        'rating': 5,
        'reviews': 76,
        'allergy_info': None,
        'ingredients': [],
        'weight_options': {
            '200g': 349,
            '500g': 749,
            '1000g': 1349
        }
    },
    {
        'name': 'Golden Dust',
        'subtitle': 'Turmeric Comfort',
        'tagline': 'Premium ground turmeric',
        'description': 'Finely ground premium turmeric powder for everyday cooking. Rich golden color and earthy aroma.',
        'price': 379,
        'category': 'single_origin',
        # 'image_url': '/static/images/turmeric-powder.jpg',
        'image_url': '/static/images/TurmericPowder.png',
        'rating': 5,
        'reviews': 95,
        'allergy_info': None,
        'ingredients': [],
        'weight_options': {
            '200g': 379,
            '500g': 849,
            '1000g': 1549
        }
    },
    {
        'name': 'Aroma Pods',
        'subtitle': 'Green Cardamom & Cloves',
        'tagline': 'Fragrant & aromatic',
        'description': 'Premium green cardamom from Kerala hills paired with aromatic whole cloves. Essential for chai and desserts.',
        'price': 449,
        'category': 'single_origin',
        # 'image_url': '/static/images/cardamom-cloves.jpg',
        'image_url': '/static/images/GreenCardamom.png',
        'rating': 5,
        'reviews': 112,
        'allergy_info': None,
        'ingredients': [],
        'weight_options': {
            '200g': 449,
            '500g': 999,
            '1000g': 1799
        }
    }
]

# =============================================================================
# COMBINED LIST (for easy iteration)
# =============================================================================

ALL_PRODUCTS = SIGNATURE_BLENDS + SINGLE_ORIGINS


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_product_by_name(name):
    """Find a product by its name."""
    for product in ALL_PRODUCTS:
        if product['name'].lower() == name.lower():
            return product
    return None


def get_products_by_category(category):
    """Get all products in a category."""
    return [p for p in ALL_PRODUCTS if p['category'] == category]


def get_product_count():
    """Get total number of products."""
    return len(ALL_PRODUCTS)
