from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User, Client, Invoice, InvoiceItem, UserProfile
from django.utils.translation import gettext_lazy as _

# Custom User Admin
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'email_verified')
    list_filter = ('is_staff', 'is_superuser', 'email_verified')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        (_('Email Verification'), {'fields': ('email_verified', 'verification_token', 'verification_token_created_at')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )

# Client Admin
@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'created_by', 'created_at')
    search_fields = ('name', 'email', 'phone')
    list_filter = ('created_at', 'country')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'

# Invoice Item Inline
class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    readonly_fields = ('total', 'created_at', 'updated_at')
    fields = ('description', 'quantity', 'unit_price', 'total', 'created_at', 'updated_at')

# Invoice Admin
@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'client_name', 'issue_date', 'due_date', 'status', 'total_amount', 'created_by')
    list_filter = ('status', 'issue_date', 'due_date')
    search_fields = ('invoice_number', 'client_name', 'client_email')
    readonly_fields = ('invoice_number', 'created_at', 'updated_at', 'view_token')
    date_hierarchy = 'issue_date'
    inlines = [InvoiceItemInline]
    
    fieldsets = (
        ('Invoice Information', {
            'fields': ('invoice_number', 'status', 'issue_date', 'due_date', 'view_token')
        }),
        ('Client Information', {
            'fields': ('client', 'client_name', 'client_email', 'client_phone', 'client_address')
        }),
        ('Financial Information', {
            'fields': ('subtotal', 'tax_amount', 'total')
        }),
        ('Additional Information', {
            'fields': ('notes', 'terms')
        }),
        ('System Information', {
            'classes': ('collapse',),
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )
    
    def total_amount(self, obj):
        return f"{obj.currency if hasattr(obj, 'currency') else '₹'}{obj.total}"
    total_amount.short_description = 'Total Amount'
    total_amount.admin_order_field = 'total'

# User Profile Admin
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'company_name', 'email', 'phone', 'created_at')
    search_fields = ('company_name', 'user__email', 'phone')
    readonly_fields = ('created_at', 'updated_at')
    
    def email(self, obj):
        return obj.user.email
    email.short_description = 'Email'
    email.admin_order_field = 'user__email'

# Register models that don't need custom admin
# admin.site.register(InvoiceItem)  # Already included as inline in InvoiceAdmin
