from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q
from django.forms import modelformset_factory

from .models import Product, ProductImage, Category
from .forms import ProductForm, ProductImageForm

class SellerRequiredMixin(UserPassesTestMixin):
    """Verify that the current user is a seller."""
    def test_func(self):
        return self.request.user.is_authenticated and (self.request.user.is_seller or self.request.user.is_admin)

class ProductListView(LoginRequiredMixin, SellerRequiredMixin, ListView):
    model = Product
    template_name = 'pages/dashboard/seller/products/list.html'
    context_object_name = 'products'
    paginate_by = 10

    def get_queryset(self):
        queryset = Product.objects.filter(seller=self.request.user)
        
        # Search functionality
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(sku__iexact=search_query)
            )
            
        # Filter by category
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
            
        # Filter by status
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
            
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['status_filter'] = self.request.GET.get('status', '')
        context['search_query'] = self.request.GET.get('search', '')
        return context

class ProductCreateView(LoginRequiredMixin, SellerRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'pages/dashboard/seller/products/form.html'
    success_url = reverse_lazy('ecom:seller_products')

    def form_valid(self, form):
        form.instance.seller = self.request.user
        response = super().form_valid(form)
        
        # Handle multiple image uploads
        images = self.request.FILES.getlist('images')
        if images:
            for image in images:
                ProductImage.objects.create(
                    product=self.object,
                    image=image,
                    alt_text=f"{self.object.name} image"
                )
            
            # Set the first uploaded image as primary
            if images:
                first_image = self.object.images.first()
                if first_image:
                    first_image.is_primary = True
                    first_image.save()
        
        messages.success(self.request, 'Product created successfully.')
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add New Product'
        context['submit_text'] = 'Create Product'
        context['categories'] = Category.objects.all()  # Add categories to context
        return context

class ProductUpdateView(LoginRequiredMixin, SellerRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'pages/dashboard/seller/products/form.html'
    context_object_name = 'product'
    slug_url_kwarg = 'slug'
    success_url = reverse_lazy('ecom:seller_products')

    def get_queryset(self):
        return Product.objects.filter(seller=self.request.user)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Handle multiple image uploads
        images = self.request.FILES.getlist('images')
        if images:
            for image in images:
                ProductImage.objects.create(
                    product=self.object,
                    image=image,
                    alt_text=f"{self.object.name} image"
                )
            
            # If no primary image set yet, set the first one as primary
            if not self.object.images.filter(is_primary=True).exists() and self.object.images.exists():
                first_image = self.object.images.first()
                first_image.is_primary = True
                first_image.save()
        
        messages.success(self.request, 'Product updated successfully.')
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Product'
        context['submit_text'] = 'Update Product'
        context['images'] = self.object.images.all()
        context['categories'] = Category.objects.all()  # Add categories to context
        return context

class ProductDeleteView(LoginRequiredMixin, SellerRequiredMixin, DeleteView):
    model = Product
    template_name = 'pages/dashboard/seller/products/confirm_delete.html'
    slug_url_kwarg = 'slug'
    success_url = reverse_lazy('ecom:seller_products')
    success_message = 'Product has been deleted.'

    def get_queryset(self):
        return Product.objects.filter(seller=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, self.success_message)
        return super().delete(request, *args, **kwargs)

class ProductDetailView(LoginRequiredMixin, DetailView):
    """
    View for viewing product details.
    Shows dashboard template to product owners, public template to others.
    """
    model = Product
    context_object_name = 'product'
    slug_url_kwarg = 'slug'
    
    def get_template_names(self):
        # Use dashboard template for product owner/admin, public template for others
        if (self.request.user == self.object.seller) or self.request.user.is_admin:
            return ['pages/dashboard/seller/products/detail.html']
        return ['pages/products/detail.html']

    def get_queryset(self):
        # Allow viewing all active products
        return Product.objects.filter(is_active=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add product images to the context
        context['images'] = self.object.images.all()
        # Add primary image for the main display
        context['primary_image'] = self.object.images.filter(is_primary=True).first() or self.object.images.first()
        # Add flag to check if current user is the product owner or admin
        context['is_owner'] = (self.request.user == self.object.seller) or self.request.user.is_admin
        return context
