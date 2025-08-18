from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, TemplateView, CreateView, UpdateView
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm, UserChangeForm
from django.contrib.auth.views import LoginView as BaseLoginView, LogoutView as BaseLogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django import forms
from .models import Product, User, Category
from .forms import SignUpForm, UserProfileForm

# Authentication Views
class SignUpView(CreateView):
    form_class = SignUpForm
    success_url = reverse_lazy('ecom:home')
    template_name = 'pages/account/signup.html'
    
    def form_valid(self, form):
        # Save the user first
        user = form.save()
        # Log the user in with the appropriate backend
        from django.contrib.auth import login
        from django.contrib.auth.backends import ModelBackend
        from django.conf import settings
        
        # Get the first authentication backend
        backend = settings.AUTHENTICATION_BACKENDS[0]
        user.backend = backend
        
        # Log the user in
        login(self.request, user)
        messages.success(self.request, 'Account created successfully! Welcome to ShopEase.')
        return super().form_valid(form)

# Static Page Views
def get_default_categories():
    """Return a list of default categories with icons"""
    return [
        {'name': 'Fashion', 'slug': 'fashion', 'icon': 'fas fa-tshirt'},
        {'name': 'Electronics', 'slug': 'electronics', 'icon': 'fas fa-mobile-alt'},
        {'name': 'Home & Living', 'slug': 'home-living', 'icon': 'fas fa-home'},
        {'name': 'Beauty', 'slug': 'beauty', 'icon': 'fas fa-spa'},
        {'name': 'Sports', 'slug': 'sports', 'icon': 'fas fa-futbol'},
        {'name': 'Books', 'slug': 'books', 'icon': 'fas fa-book'},
    ]

def home(request):
    # Get featured products (first 8 active products)
    featured_products = Product.objects.filter(is_active=True)[:8]
    
    # Get featured categories (marked as featured and active)
    featured_categories = Category.objects.filter(
        is_featured=True,
        is_active=True,
        parent__isnull=True  # Only top-level categories
    ).distinct()[:8]  # Limit to 8 categories for the grid
    
    # If no featured categories are set, get some active categories with products
    if not featured_categories.exists():
        featured_categories = Category.objects.filter(
            is_active=True,
            parent__isnull=True,
            products__isnull=False
        ).distinct()[:6]
    
    # Prepare default categories (used as fallback if no categories exist)
    default_categories = []
    if not featured_categories.exists():
        default_categories = get_default_categories()
    
    return render(request, 'pages/home.html', {
        'featured_products': featured_products,
        'featured_categories': featured_categories,
        'default_categories': default_categories,
        'show_categories_section': bool(featured_categories.exists() or default_categories)
    })

def about(request):
    return render(request, 'pages/about.html')

def contact(request):
    return render(request, 'pages/contact.html')

def faqs(request):
    return render(request, 'pages/customer-service/faqs.html')

def shipping_policy(request):
    return render(request, 'pages/customer-service/shipping-policy.html')

def return_policy(request):
    return render(request, 'pages/customer-service/return-policy.html')

def privacy_policy(request):
    return render(request, 'pages/customer-service/privacy-policy.html')

def terms_conditions(request):
    return render(request, 'pages/customer-service/terms-conditions.html')

# Product Views
class ProductListView(ListView):
    template_name = 'pages/products/list.html'
    context_object_name = 'products'
    paginate_by = 12
    model = Product

    def get_queryset(self):
        # Start with all active products
        queryset = Product.objects.filter(is_active=True).select_related('category').prefetch_related('images')
        
        # Filter by category if specified in the URL
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
            
        return queryset
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add all active categories to the context for the dropdown
        context['categories'] = Category.objects.filter(is_active=True).order_by('name')
        # Add the current category filter (if any)
        context['current_category'] = self.request.GET.get('category', '')
        return context

class ProductDetailView(DetailView):
    template_name = 'pages/products/detail.html'
    context_object_name = 'product'
    model = Product
    
    def get_queryset(self):
        # Prefetch related data to avoid N+1 queries
        return Product.objects.filter(is_active=True).select_related('category').prefetch_related('images')
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get all images for the product
        context['images'] = self.object.images.all()
        # Get the primary image (or first image if none is marked as primary)
        context['primary_image'] = self.object.images.filter(is_primary=True).first() or self.object.images.first()
        return context

# Cart and Checkout Views
def cart(request):
    return render(request, 'cart/cart.html')

def checkout(request):
    return render(request, 'checkout/checkout.html')

def order_confirmation(request, order_id):
    return render(request, 'checkout/order_confirmation.html', {'order_id': order_id})

# User Account Views
class LoginView(BaseLoginView):
    template_name = 'pages/account/login.html'
    redirect_authenticated_user = True
    next_page = 'ecom:home'  # Redirect to home page after login
    
    def get_form_class(self):
        # Use Django's AuthenticationForm but customize it to use email field
        from django.contrib.auth.forms import AuthenticationForm
        
        class EmailAuthenticationForm(AuthenticationForm):
            username = forms.EmailField(
                label='Email',
                widget=forms.TextInput(attrs={
                    'class': 'appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
                    'autocomplete': 'email',
                    'placeholder': 'Email address',
                })
            )
            
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.fields['password'].widget.attrs.update({
                    'class': 'appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
                    'placeholder': 'Password',
                })
            
            def clean_username(self):
                # Return the email as the username for authentication
                return self.cleaned_data.get('username')
        
        return EmailAuthenticationForm
    
    def form_valid(self, form):
        # Get the email and password from the form
        email = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        # print(f"DEBUG: Attempting to authenticate user with email: {email}")
        
        # Authenticate the user - explicitly pass email as both username and in kwargs
        from django.contrib.auth import authenticate, login
        user = authenticate(
            request=self.request, 
            username=email,  
            password=password,
            email=email  # Also pass email in kwargs for the backend
        )
        
        if user is not None:
            # print(f"DEBUG: Authentication successful for user: {user.email}")
            # User is valid, log them in
            login(self.request, user, backend='ecom.backends.EmailBackend')
            
            # Handle remember me
            remember_me = form.cleaned_data.get('remember_me', False)
            if not remember_me:
                # Set session to expire when browser is closed
                self.request.session.set_expiry(0)
                # Set session as modified to force data updates/cookie to be saved
                self.request.session.modified = True
            
            # Ensure the user has a profile using get_or_create to avoid race conditions
            from .models import UserProfile
            UserProfile.objects.get_or_create(user=user)
            
            # Add welcome message
            messages.success(self.request, f'Welcome back, {user.first_name or user.email}!')
            
            # Redirect to the next page or home
            redirect_to = self.get_success_url()
            # print(f"DEBUG: Redirecting to: {redirect_to}")
            return redirect(redirect_to)
        else:
            # print(f"DEBUG: Authentication failed for email: {email}")
            # Authentication failed, return to form with error
            messages.error(self.request, 'Invalid email or password. Please try again.')
            return self.form_invalid(form)
        
    def form_invalid(self, form):
        # Clear the password field for security
        if 'password' in form.cleaned_data:
            form.cleaned_data['password'] = ''
        return super().form_invalid(form)

class LogoutView(BaseLogoutView):
    next_page = 'ecom:home'

class ProfileView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserProfileForm
    template_name = 'pages/account/profile.html'
    success_url = reverse_lazy('ecom:profile')
    
    def get_object(self, queryset=None):
        user = self.request.user
        # Ensure the user has a profile
        if not hasattr(user, 'profile'):
            from .models import UserProfile
            UserProfile.objects.create(user=user)
        return user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add any additional context data here
        return context
        
    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully!')
        return super().form_valid(form)

class OrderHistoryView(LoginRequiredMixin, ListView):
    template_name = 'pages/account/orders.html'
    context_object_name = 'orders'
    paginate_by = 10
    
    def get_queryset(self):
        # Return empty queryset for now - implement when order model is available
        return []

