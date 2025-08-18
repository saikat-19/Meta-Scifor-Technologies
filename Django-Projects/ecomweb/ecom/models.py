import random
import string
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.text import slugify
from decimal import Decimal
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.conf import settings

# Get the custom user model
User = get_user_model()

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text='Font Awesome icon class (e.g., fas fa-tshirt)'
    )
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='children')
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False, help_text='Show this category on the homepage')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    compare_at_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='products')
    sku = models.CharField(max_length=100, unique=True, blank=True, null=True)
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
        
    def generate_sku(self):
        """Generate a unique SKU for the product.
        Format: CATEGORY-NAME-XXXX where XXXX is a random 4-digit number
        """
        # Get first 3 letters of category
        category_prefix = self.category.name.upper()[:3]
        # Get first 3 letters of product name (alphanumeric only)
        name_prefix = ''.join(c for c in self.name.upper() if c.isalnum())[:3]
        # Generate random 4-digit number
        random_suffix = ''.join(random.choices(string.digits, k=4))
        
        sku = f"{category_prefix}-{name_prefix}-{random_suffix}"
        
        # Ensure SKU is unique
        while Product.objects.filter(sku=sku).exclude(pk=self.pk).exists():
            random_suffix = ''.join(random.choices(string.digits, k=4))
            sku = f"{category_prefix}-{name_prefix}-{random_suffix}"
            
        return sku
        
    def save(self, *args, **kwargs):
        # Generate SKU if not provided
        if not self.sku:
            self.sku = self.generate_sku()
            
        # Ensure slug is set
        if not self.slug:
            self.slug = slugify(self.name)
            
            # Ensure slug is unique
            original_slug = self.slug
            counter = 1
            while Product.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
                
        super().save(*args, **kwargs)

    @property
    def is_in_stock(self):
        return self.stock > 0

    @property
    def discount_percentage(self):
        if self.compare_at_price and self.compare_at_price > self.price:
            return int(((self.compare_at_price - self.price) / self.compare_at_price) * 100)
        return 0

class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.product.name}"

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='cart')
    session_key = models.CharField(max_length=40, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.user:
            return f"Cart for {self.user.username}"
        return f"Anonymous Cart ({self.session_key})"

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def subtotal(self):
        return sum(item.total_price for item in self.items.all())

    @property
    def shipping_cost(self):
        # Flat rate shipping for now, can be made dynamic later
        return Decimal('50.00')

    @property
    def total(self):
        return self.subtotal + self.shipping_cost

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('cart', 'product')

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    @property
    def unit_price(self):
        return self.product.price

    @property
    def total_price(self):
        return self.unit_price * self.quantity

class UserProfile(models.Model):
    """Extended user profile information."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text='Enter a valid phone number (e.g., +1234567890)'
    )
    address = models.TextField(
        blank=True,
        null=True,
        help_text='Your complete shipping address'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s profile"

class LicenseApplication(models.Model):
    """Model to track seller and moderator license applications"""
    APPLICATION_TYPES = [
        ('seller', 'Seller'),
        ('moderator', 'Moderator'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='license_applications')
    application_type = models.CharField(max_length=20, choices=APPLICATION_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    message = models.TextField(blank=True, null=True, help_text='Additional information from the applicant (optional)')
    admin_notes = models.TextField(blank=True, help_text='Internal notes for administrators')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='processed_applications'
    )
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'License Application'
        verbose_name_plural = 'License Applications'

    def __str__(self):
        return f"{self.get_application_type_display()} Application - {self.user.email} ({self.get_status_display()})"

    def approve(self, approved_by):
        self.status = 'approved'
        self.processed_by = approved_by
        self.processed_at = timezone.now()
        self.save()
        
        # Update user role if approved
        if self.application_type == 'seller':
            self.user.role = 'SELLER'
            self.user.is_approved = True
        elif self.application_type == 'moderator':
            self.user.role = 'MODERATOR'
            self.user.is_approved = True
        self.user.save()
        
        return True

    def reject(self, rejected_by, notes=''):
        self.status = 'rejected'
        self.processed_by = rejected_by
        self.processed_at = timezone.now()
        if notes:
            self.admin_notes = notes
        self.save()
        return True


# Signal to create/update the user profile
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    instance.profile.save()

