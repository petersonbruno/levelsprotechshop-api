"""
Utility functions for API responses and validation.
"""
from rest_framework.response import Response
from rest_framework import status
import re
import base64
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys

# Optional PIL import for image processing
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None


def success_response(data=None, message=None, status_code=status.HTTP_200_OK):
    """Create a standardized success response."""
    response_data = {
        "success": True,
        "data": data,
    }
    if message:
        response_data["message"] = message
    return Response(response_data, status=status_code)


def error_response(error_message, details=None, status_code=status.HTTP_400_BAD_REQUEST):
    """Create a standardized error response."""
    response_data = {
        "success": False,
        "error": error_message,
    }
    if details:
        response_data["details"] = details
    return Response(response_data, status=status_code)


def format_price_with_commas(price_value):
    """Format a number or numeric string with commas every three digits."""
    # Remove any existing commas and whitespace
    if isinstance(price_value, str):
        # Remove commas, spaces, and "TZS" if present
        price_str = price_value.replace(',', '').replace(' ', '').replace('TZS', '').strip()
        try:
            price_value = int(price_str)
        except ValueError:
            return price_value  # Return as-is if not numeric
    elif not isinstance(price_value, (int, float)):
        return price_value
    
    # Format with commas
    return f"{price_value:,}"


def validate_price_format(price):
    """Validate price format: accepts '720,000' or '720,000 TZS' or plain numbers."""
    if isinstance(price, (int, float)):
        return True
    
    # Pattern 1: With commas and optional TZS: "720,000" or "720,000 TZS"
    pattern1 = r'^\d{1,3}(,\d{3})*(?:\s+TZS)?$'
    # Pattern 2: Plain number without commas: "720000"
    pattern2 = r'^\d+$'
    
    price_str = str(price).strip()
    return bool(re.match(pattern1, price_str) or re.match(pattern2, price_str))


def validate_category(category):
    """Validate category is one of the allowed values."""
    valid_categories = ['Laptops', 'Desktops', 'Gaming PCs', 'Accessories']
    return category in valid_categories


def base64_to_image(base64_string, filename='image.png'):
    """Convert base64 string to Django ImageField file."""
    if not PIL_AVAILABLE:
        raise ValueError("Pillow (PIL) is required for base64 image processing. Please install it with: pip install Pillow")
    
    try:
        # Remove data URL prefix if present
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        
        # Decode base64
        image_data = base64.b64decode(base64_string)
        
        # Open image with PIL
        image = Image.open(BytesIO(image_data))
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Save to BytesIO
        image_io = BytesIO()
        image.save(image_io, format='PNG')
        image_io.seek(0)
        
        # Create Django InMemoryUploadedFile
        file = InMemoryUploadedFile(
            image_io,
            None,
            filename,
            'image/png',
            sys.getsizeof(image_io),
            None
        )
        
        return file
    except Exception as e:
        raise ValueError(f"Invalid base64 image: {str(e)}")


def validate_image_file(image_file):
    """Validate image file (size, type)."""
    # Check file size (5MB max)
    max_size = 5 * 1024 * 1024  # 5MB in bytes
    if image_file.size > max_size:
        raise ValueError("Image size exceeds 5MB limit")
    
    # Check file type
    allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
    if image_file.content_type not in allowed_types:
        raise ValueError(f"Invalid image type. Allowed types: {', '.join(allowed_types)}")
    
    return True

