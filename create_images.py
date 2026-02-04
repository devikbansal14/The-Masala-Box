from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
import random
import math

# Spice colors for different products
SPICE_COLORS = {
    'garam-masala': [
        '#8B4513',  # Cinnamon brown
        '#DAA520',  # Cumin golden
        '#228B22',  # Green cardamom
        '#654321',  # Dark brown (cloves)
        '#FFD700',  # Yellow (turmeric hint)
        '#CD853F',  # Nutmeg
        '#A0522D',  # Mace
        '#2F4F4F',  # Black pepper
    ],
    'pav-bhaji': [
        '#DC143C',  # Red chili
        '#DAA520',  # Cumin
        '#2F4F4F',  # Black pepper
        '#8FBC8F',  # Dried fenugreek green
        '#FFD700',  # Amchur yellow
        '#8B4513',  # Coriander
        '#CD853F',  # Fennel
        '#696969',  # Black salt
    ],
    'biryani': [
        '#228B22',  # Green cardamom
        '#8B4513',  # Cinnamon
        '#654321',  # Cloves
        '#2F4F4F',  # Star anise
        '#FFD700',  # Saffron gold
        '#DEB887',  # Bay leaves
        '#CD853F',  # Mace
        '#FFC0CB',  # Rose petals
    ],
    'chicken-masala': [
        '#DAA520',  # Coriander
        '#2F4F4F',  # Black cardamom
        '#DC143C',  # Red chili
        '#8B4513',  # Cumin
        '#CD853F',  # Fennel
        '#696969',  # Stone flower
        '#F5DEB3',  # Coconut
        '#2F4F4F',  # Black pepper
    ],
    'red-chilies': [
        '#DC143C',  # Red chili
        '#B22222',  # Dark red
        '#8B0000',  # Deep red
        '#CD5C5C',  # Light red
    ],
    'turmeric-fingers': [
        '#FFD700',  # Golden
        '#FFA500',  # Orange
        '#DAA520',  # Dark golden
        '#F4A460',  # Sandy
    ],
    'turmeric-powder': [
        '#FFD700',  # Golden
        '#FFA500',  # Orange
        '#FFEC8B',  # Light yellow
        '#DAA520',  # Dark golden
    ],
    'cardamom-cloves': [
        '#228B22',  # Green cardamom
        '#654321',  # Brown cloves
        '#2E8B57',  # Dark green
        '#3D2914',  # Dark clove
    ],
}

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def draw_wood_grain(draw, x, y, width, height, base_color):
    """Draw wood grain texture"""
    r, g, b = hex_to_rgb(base_color)
    for i in range(height):
        grain_offset = random.randint(-5, 5)
        line_color = (
            max(0, min(255, r + grain_offset)),
            max(0, min(255, g + grain_offset)),
            max(0, min(255, b + grain_offset))
        )
        draw.line([(x, y + i), (x + width, y + i)], fill=line_color)

def draw_spice_compartment(draw, x, y, size, spice_color, is_filled=True):
    """Draw a single spice compartment"""
    # Inner compartment shadow
    shadow_offset = 3
    draw.rectangle(
        [x + shadow_offset, y + shadow_offset, x + size - 2, y + size - 2],
        fill='#1a1208'
    )

    # Compartment base
    draw.rectangle(
        [x + 2, y + 2, x + size - 4, y + size - 4],
        fill='#2d2216'
    )

    if is_filled:
        # Draw spice particles
        r, g, b = hex_to_rgb(spice_color)
        for _ in range(150):
            px = x + 8 + random.randint(0, size - 20)
            py = y + 8 + random.randint(0, size - 20)
            particle_size = random.randint(2, 6)
            variation = random.randint(-20, 20)
            color = (
                max(0, min(255, r + variation)),
                max(0, min(255, g + variation)),
                max(0, min(255, b + variation))
            )
            draw.ellipse(
                [px, py, px + particle_size, py + particle_size],
                fill=color
            )

def create_wooden_box_image(filepath, product_key, product_name):
    """Create a premium wooden box image with spice compartments"""

    # Image dimensions
    width, height = 800, 800

    # Create base image with dark background
    img = Image.new('RGB', (width, height), color='#0d0d0d')
    draw = ImageDraw.Draw(img)

    # Subtle radial gradient background
    center_x, center_y = width // 2, height // 2
    for r in range(400, 0, -1):
        alpha = int(15 * (1 - r / 400))
        color = (26 + alpha, 20 + alpha, 13 + alpha)
        draw.ellipse(
            [center_x - r, center_y - r, center_x + r, center_y + r],
            fill=color
        )

    # Box dimensions
    box_margin = 100
    box_x = box_margin
    box_y = box_margin
    box_width = width - 2 * box_margin
    box_height = height - 2 * box_margin

    # Outer box shadow
    shadow_size = 20
    for i in range(shadow_size):
        alpha = int(30 * (1 - i / shadow_size))
        shadow_color = (alpha, alpha, alpha)
        draw.rectangle(
            [box_x + i, box_y + i, box_x + box_width + shadow_size - i, box_y + box_height + shadow_size - i],
            outline=shadow_color
        )

    # Wood box frame (outer)
    wood_color = '#4a3828'
    draw.rectangle(
        [box_x, box_y, box_x + box_width, box_y + box_height],
        fill=wood_color,
        outline='#2d1f14',
        width=3
    )

    # Wood grain effect on frame
    for i in range(10):
        grain_y = box_y + i * (box_height // 10)
        grain_color = '#3d2e1f' if i % 2 == 0 else '#5a4433'
        draw.line(
            [(box_x, grain_y), (box_x + box_width, grain_y + random.randint(-5, 5))],
            fill=grain_color,
            width=2
        )

    # Inner compartment area
    inner_margin = 20
    inner_x = box_x + inner_margin
    inner_y = box_y + inner_margin
    inner_width = box_width - 2 * inner_margin
    inner_height = box_height - 2 * inner_margin

    # Get spice colors for this product
    spice_colors = SPICE_COLORS.get(product_key, SPICE_COLORS['garam-masala'])

    # Determine grid size based on product type
    if product_key in ['red-chilies', 'turmeric-fingers', 'turmeric-powder', 'cardamom-cloves']:
        # Single origin - 2x2 grid
        grid_size = 2
    else:
        # Signature blends - 3x3 or 4x2 grid
        grid_size = 3

    compartment_size = inner_width // grid_size

    # Draw compartments
    color_index = 0
    for row in range(grid_size):
        for col in range(grid_size):
            cx = inner_x + col * compartment_size
            cy = inner_y + row * compartment_size
            spice_color = spice_colors[color_index % len(spice_colors)]
            draw_spice_compartment(draw, cx, cy, compartment_size, spice_color)
            color_index += 1

    # Draw wood frame borders (overlapping compartments)
    frame_width = 8
    frame_color = '#3d2e1f'

    # Horizontal dividers
    for i in range(1, grid_size):
        y_pos = inner_y + i * compartment_size - frame_width // 2
        draw.rectangle(
            [inner_x, y_pos, inner_x + inner_width, y_pos + frame_width],
            fill=frame_color
        )

    # Vertical dividers
    for i in range(1, grid_size):
        x_pos = inner_x + i * compartment_size - frame_width // 2
        draw.rectangle(
            [x_pos, inner_y, x_pos + frame_width, inner_y + inner_height],
            fill=frame_color
        )

    # Gold accent corners
    corner_size = 15
    gold = '#d4a853'
    corners = [
        (box_x, box_y),  # Top-left
        (box_x + box_width - corner_size, box_y),  # Top-right
        (box_x, box_y + box_height - corner_size),  # Bottom-left
        (box_x + box_width - corner_size, box_y + box_height - corner_size),  # Bottom-right
    ]
    for cx, cy in corners:
        draw.rectangle(
            [cx, cy, cx + corner_size, cy + corner_size],
            fill=gold
        )

    # Add product name label
    try:
        font_large = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf', 32)
        font_small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Brand label at bottom
    brand_text = "THE MASALA BOX"
    bbox = draw.textbbox((0, 0), brand_text, font=font_small)
    text_width = bbox[2] - bbox[0]
    text_x = (width - text_width) // 2
    text_y = height - 50
    draw.text((text_x, text_y), brand_text, fill='#d4a853', font=font_small)

    # Apply subtle blur to soften edges
    img = img.filter(ImageFilter.GaussianBlur(radius=0.5))

    # Save with high quality
    img.save(filepath, 'JPEG', quality=95)
    print(f'Created: {filepath}')

def main():
    # Product specifications
    products = {
        'garam-masala.png': ('garam-masala', 'Heritage Blend'),
        'pav-bhaji.png': ('pav-bhaji', 'Mumbai Street'),
        'biryani.png': ('biryani', 'Royal Handi'),
        'chicken-masala.png': ('chicken-masala', 'Coastal Roast'),
        'red-chilies.jpg': ('red-chilies', 'Kashmiri Fire'),
        'turmeric-fingers.jpg': ('turmeric-fingers', 'Golden Root'),
        'turmeric-powder.jpg': ('turmeric-powder', 'Golden Dust'),
        'cardamom-cloves.jpg': ('cardamom-cloves', 'Aroma Pods'),
    }

    # Output directory
    base_path = '/home/devik.bansal/Documents/PERSONAL/masala_lab/static/images'
    os.makedirs(base_path, exist_ok=True)

    # Generate all images
    for filename, (product_key, product_name) in products.items():
        filepath = os.path.join(base_path, filename)
        create_wooden_box_image(filepath, product_key, product_name)

    print('\nAll premium wooden box images created successfully!')

if __name__ == '__main__':
    main()
