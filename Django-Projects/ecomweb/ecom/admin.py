from django.contrib import admin
from .models import Category, Product, ProductImage, Cart, CartItem, UserProfile, LicenseApplication

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'parent', 'is_active', 'is_featured', 'created_at')
    list_editable = ('is_active', 'is_featured')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'slug', 'description')
    list_filter = ('is_active', 'is_featured', 'created_at')
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'parent', 'description')
        }),
        ('Display', {
            'fields': ('icon', 'image', 'is_featured')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock', 'is_active', 'seller')
    list_filter = ('category', 'is_active', 'created_at')
    search_fields = ('name', 'description', 'sku')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline]

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_items', 'subtotal', 'created_at')
    list_filter = ('created_at', 'updated_at')

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product', 'quantity', 'total_price')
    list_filter = ('created_at', 'updated_at')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'created_at')
    search_fields = ('user__email', 'phone_number')

@admin.register(LicenseApplication)
class LicenseApplicationAdmin(admin.ModelAdmin):
    list_display = ('user', 'application_type', 'status', 'created_at', 'processed_at')
    list_filter = ('status', 'application_type', 'created_at')
    search_fields = ('user__email', 'message')
    actions = ['approve_applications', 'reject_applications']
    
    def approve_applications(self, request, queryset):
        for application in queryset.filter(status='pending'):
            application.approve(request.user)
    approve_applications.short_description = 'Approve selected applications'
    
    def reject_applications(self, request, queryset):
        for application in queryset.filter(status='pending'):
            application.reject(request.user, 'Bulk rejection')
    reject_applications.short_description = 'Reject selected applications'
