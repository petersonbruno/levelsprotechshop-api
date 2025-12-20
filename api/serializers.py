from rest_framework import serializers
import re
from .models import Product, ProductImage
from .utils import validate_price_format, validate_category, format_price_with_commas


class ProductImageSerializer(serializers.ModelSerializer):
    """Serializer for product images."""
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'image_url', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def get_image_url(self, obj):
        """Get full URL for image."""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product model with validation."""
    images = ProductImageSerializer(many=True, read_only=True)
    image_urls = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'category', 'price', 'specs', 
            'warranty', 'images', 'image_urls', 'created_at', 'updated_at', 'creator', 'trending'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'images', 'creator']
    
    def get_image_urls(self, obj):
        """Get list of image URLs."""
        request = self.context.get('request')
        image_urls = []
        for image in obj.images.all():
            if image.image:
                if request:
                    image_urls.append(request.build_absolute_uri(image.image.url))
                else:
                    image_urls.append(image.image.url)
        return image_urls
    
    def validate_name(self, value):
        """Validate product name."""
        if len(value) < 3:
            raise serializers.ValidationError("Product name must be at least 3 characters long.")
        if len(value) > 200:
            raise serializers.ValidationError("Product name must not exceed 200 characters.")
        return value
    
    def validate_category(self, value):
        """Validate category."""
        if not validate_category(value):
            raise serializers.ValidationError(
                "Category must be one of: Laptops, Desktops, Gaming PCs, Accessories"
            )
        return value
    
    def validate_price(self, value):
        """Validate and format price."""
        # Accept int, float, or string
        if isinstance(value, (int, float)):
            # Auto-format numbers with commas
            return format_price_with_commas(value)
        
        # Validate string format
        if not validate_price_format(value):
            raise serializers.ValidationError(
                "Price must be a number or in format: '720,000' or '720,000 TZS'"
            )
        
        # Format the price string (add commas if missing, keep TZS if present)
        price_str = str(value).strip()
        
        # If it's a plain number without commas, format it
        if re.match(r'^\d+$', price_str):
            return format_price_with_commas(price_str)
        
        # If it has TZS but no commas in the number part, format it
        if 'TZS' in price_str.upper():
            # Extract number part
            number_part = price_str.replace('TZS', '').replace(',', '').strip()
            if number_part.isdigit():
                formatted = format_price_with_commas(number_part)
                return f"{formatted} TZS"
        
        # Return as-is if already properly formatted
        return price_str
    
    def validate_specs(self, value):
        """Validate specs array."""
        if not isinstance(value, list):
            raise serializers.ValidationError("Specs must be an array.")
        for spec in value:
            if not isinstance(spec, str):
                raise serializers.ValidationError("Each spec must be a string.")
            if len(spec) > 500:
                raise serializers.ValidationError("Each spec must not exceed 500 characters.")
        return value


class ProductCreateSerializer(ProductSerializer):
    """Serializer for creating products with image handling."""
    images_data = serializers.ListField(
        child=serializers.CharField(required=False),
        write_only=True,
        required=False,
        help_text="Array of base64 image strings"
    )
    
    class Meta(ProductSerializer.Meta):
        fields = ProductSerializer.Meta.fields + ['images_data']
    
    def validate(self, attrs):
        """Validate that at least one image is provided."""
        images_data = attrs.get('images_data', [])
        # Check if images are provided via images_data or will be provided via multipart/form-data
        if not images_data and 'images' not in self.initial_data:
            raise serializers.ValidationError("At least one image is required.")
        if len(images_data) > 10:
            raise serializers.ValidationError("Maximum 10 images allowed per product.")
        return attrs
    
    def create(self, validated_data):
        """Create product with images."""
        images_data = validated_data.pop('images_data', [])
        product = Product.objects.create(**validated_data)
        
        # Handle base64 images
        for idx, image_data in enumerate(images_data):
            if image_data:
                from .utils import base64_to_image
                try:
                    image_file = base64_to_image(image_data, f"product_{product.id}_{idx}.png")
                    ProductImage.objects.create(product=product, image=image_file)
                except Exception as e:
                    raise serializers.ValidationError(f"Error processing image {idx + 1}: {str(e)}")
        
        return product
    
    def update(self, instance, validated_data):
        """Update product."""
        images_data = validated_data.pop('images_data', None)
        
        # Update product fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Handle new base64 images if provided
        if images_data:
            for idx, image_data in enumerate(images_data):
                if image_data:
                    from .utils import base64_to_image
                    try:
                        image_file = base64_to_image(image_data, f"product_{instance.id}_{idx}.png")
                        ProductImage.objects.create(product=instance, image=image_file)
                    except Exception as e:
                        raise serializers.ValidationError(f"Error processing image {idx + 1}: {str(e)}")
        
        return instance


