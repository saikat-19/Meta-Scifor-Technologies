from django.urls import path
from django.contrib.auth.decorators import login_required
from . import views
from .views import register_view, static_page_view
from .auth_views import VerifyEmailView, resend_verification_email

app_name = 'invoice_app'  # This sets the application namespace

urlpatterns = [
    # Home page
    path('', views.home, name='home'),
    
    # Authentication URLs
    path('register/', register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # Email Verification URLs
    path('verify-email/<int:user_id>/<str:token>/', 
         VerifyEmailView.as_view(), 
         name='verify_email'),
    path('resend-verification/', 
         resend_verification_email, 
         name='resend_verification'),
    
    # Dashboard URL
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # User Profile URL
    path('profile/', login_required(views.user_profile), name='user_profile'),
    
    # Invoice URLs
    path('invoices/', login_required(views.invoice_list), name='invoice_list'),
    path('invoices/create/', login_required(views.invoice_create), name='invoice_create'),
    path('invoices/<int:pk>/', login_required(views.invoice_detail), name='invoice_detail'),
    path('invoices/<int:pk>/update/', login_required(views.invoice_update), name='invoice_update'),
    path('invoices/<int:pk>/delete/', login_required(views.invoice_delete), name='invoice_delete'),
    path('invoices/<int:pk>/send/', login_required(views.send_invoice_email), name='send_invoice_email'),
    
    # Client URLs
    path('clients/', login_required(views.client_list), name='client_list'),
    path('clients/create/', login_required(views.client_create), name='client_create'),
    path('clients/<int:pk>/', login_required(views.client_detail), name='client_detail'),
    path('clients/<int:pk>/update/', login_required(views.client_update), name='client_update'),
    path('clients/<int:pk>/delete/', login_required(views.client_delete), name='client_delete'),
    
    # Public invoice access
    path('public/invoice/<uuid:token>/', views.public_invoice_view, name='public_invoice'),
    
    # API Endpoints
    path('api/invoice/<int:invoice_id>/items/', 
         login_required(views.get_invoice_items), 
         name='api_invoice_items'),
    path('api/client/<int:pk>/data/', 
         login_required(views.get_client_data), 
         name='api_client_data'),
         
    # Static Pages
    path('about/', views.static_page_view, {'template_name': 'about'}, name='about'),
    path('privacy/', views.static_page_view, {'template_name': 'privacy'}, name='privacy'),
    path('terms/', views.static_page_view, {'template_name': 'terms'}, name='terms'),
]
