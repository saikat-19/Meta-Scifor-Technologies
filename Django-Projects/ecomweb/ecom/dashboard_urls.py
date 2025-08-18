from django.urls import path
from . import dashboard_views, product_views

app_name = 'ecom_dashboard'

urlpatterns = [
    # Dashboard
    path('', dashboard_views.DashboardView.as_view(), name='dashboard'),
    
    # Product Management
    path('products/', product_views.ProductListView.as_view(), name='seller_products'),
    path('products/add/', product_views.ProductCreateView.as_view(), name='product_create'),
    path('products/manage/<slug:slug>/', product_views.ProductDetailView.as_view(), name='product_manage'),
    path('products/<slug:slug>/edit/', product_views.ProductUpdateView.as_view(), name='product_update'),
    path('products/<slug:slug>/delete/', product_views.ProductDeleteView.as_view(), name='product_delete'),
]
