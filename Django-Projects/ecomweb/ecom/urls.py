from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.decorators import login_required
from . import views
from . import cart_views
from . import dashboard_views
from . import product_views

app_name = 'ecom'

urlpatterns = [
    # Static Pages
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('faqs/', views.faqs, name='faqs'),
    path('shipping-policy/', views.shipping_policy, name='shipping_policy'),
    path('return-policy/', views.return_policy, name='return_policy'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms-conditions/', views.terms_conditions, name='terms_conditions'),
    
    # Product URLs
    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('products/<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
    
    # Cart URLs
    path('cart/', include([
        path('', cart_views.cart_detail, name='cart_detail'),
        path('add/<int:product_id>/', cart_views.cart_add, name='cart_add'),
        path('update/<int:item_id>/', cart_views.cart_update, name='cart_update'),
        path('remove/<int:item_id>/', cart_views.cart_remove, name='cart_remove'),
        path('api/count/', cart_views.cart_count, name='cart_count'),
    ])),
    
    # Checkout URLs
    path('checkout/', include([
        path('', cart_views.checkout, name='checkout'),
        path('payment-notice/', cart_views.checkout_payment_notice, name='checkout_payment_notice'),
    ])),
    path('order-confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    
    # Account URLs
    path('accounts/', include([
        path('login/', views.LoginView.as_view(template_name='pages/account/login.html'), name='login'),
        path('signup/', views.SignUpView.as_view(), name='signup'),
        path('logout/', views.LogoutView.as_view(next_page='ecom:home'), name='logout'),
        path('profile/', login_required(views.ProfileView.as_view()), name='profile'),
        path('orders/', login_required(views.OrderHistoryView.as_view()), name='order_history'),
    ])),
    
    # Dashboard URLs
    path('dashboard/', include([
        path('', login_required(dashboard_views.DashboardView.as_view()), name='dashboard'),
        path('apply-seller/', login_required(dashboard_views.ApplySellerView.as_view()), name='apply_seller'),
        path('apply-moderator/', login_required(dashboard_views.ApplyModeratorView.as_view()), name='apply_moderator'),
        # Admin/Moderator URLs
        path('pending-approvals/', login_required(dashboard_views.PendingApprovalsView.as_view()), name='pending_approvals'),
        path('admin/users/', login_required(dashboard_views.UserManagementView.as_view()), name='user_management'),
        
        # Product Management
        path('products/', include([
            path('', login_required(product_views.ProductListView.as_view()), name='seller_products'),
            path('add/', login_required(product_views.ProductCreateView.as_view()), name='product_create'),
            path('<slug:slug>/', login_required(product_views.ProductDetailView.as_view()), name='product_detail'),
            path('<slug:slug>/edit/', login_required(product_views.ProductUpdateView.as_view()), name='product_update'),
            path('<slug:slug>/delete/', login_required(product_views.ProductDeleteView.as_view()), name='product_delete'),
        ])),
    ])),
]