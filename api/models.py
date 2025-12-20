from django.db import models
from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.contrib.auth.models import User
import uuid


class BaseModel(models.Model):
    """Abstract base model with common fields."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Product(BaseModel):
    """Product model for LevelsProShop e-commerce."""
    CATEGORY_CHOICES = [
        ('Laptops', 'Laptops'),
        ('Desktops', 'Desktops'),
        ('Gaming PCs', 'Gaming PCs'),
        ('Accessories', 'Accessories'),
        
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(
        max_length=200,
        validators=[MinLengthValidator(3), MaxLengthValidator(200)],
        help_text="Product name (3-200 characters)"
    )
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        help_text="Product category"
    )
    price = models.CharField(
        max_length=50,
        help_text="Price in format: '720,000' or '720,000 TZS' (commas auto-added)"
    )
    specs = models.JSONField(
        default=list,
        help_text="Array of specifications"
    )
    warranty = models.CharField(
        max_length=50,
        default="3 Months",
        help_text="Warranty period"
    )
    creator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_products',
        help_text="User who created this product"
    )
    trending = models.BooleanField(
        default=False,
        help_text="Whether this product is marked as trending"
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['name']),
            models.Index(fields=['created_at']),
            models.Index(fields=['creator']),
            models.Index(fields=['trending']),
        ]

    def __str__(self):
        return f"{self.name} ({self.category})"


class ProductImage(models.Model):
    """Product images model."""
    product = models.ForeignKey(
        Product,
        related_name='images',
        on_delete=models.CASCADE
    )
    image = models.ImageField(
        upload_to='products/',
        help_text="Product image (max 5MB)"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Image for {self.product.name}"


