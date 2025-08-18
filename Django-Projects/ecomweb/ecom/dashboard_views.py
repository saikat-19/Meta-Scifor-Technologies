from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView, ListView, FormView
from django.utils import timezone
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.http import JsonResponse

from .models import LicenseApplication
from .forms import LicenseApplicationForm

class AdminDashboardMixin(UserPassesTestMixin):
    """Mixin to check if user has admin or moderator permissions"""
    login_url = reverse_lazy('ecom:login')
    
    def test_func(self):
        return self.request.user.is_authenticated and (self.request.user.is_admin or self.request.user.is_moderator)
    
    def handle_no_permission(self):
        messages.error(self.request, "You don't have permission to access this page.")
        return redirect('ecom:home')

class DashboardView(LoginRequiredMixin, TemplateView):
    """Main dashboard view that shows different content based on user role"""
    template_name = 'pages/dashboard/overview.html'
    login_url = reverse_lazy('ecom:login')
    
    def get_template_names(self):
        if self.request.user.is_admin or self.request.user.is_moderator:
            return ['pages/dashboard/admin/overview.html']
        elif self.request.user.is_seller:
            return ['pages/dashboard/seller/overview.html']
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        User = get_user_model()
        
        # Common context for all users
        context.update({
            'user': user,
        })
        
        # Role-specific context
        if user.is_admin or user.is_moderator:
            # Admin/Moderator specific context
            context.update({
                'is_admin': user.is_admin,
                'is_moderator': user.is_moderator,
                'recent_activity': [],  # TODO: Add recent activity logic
                'total_users': User.objects.count(),
                'active_users': User.objects.filter(is_active=True).count(),
                'pending_approvals_count': 0,  # TODO: Add actual pending approvals count
                'total_products': 0,  # TODO: Add actual products count
            })
        
        if user.is_seller or user.is_admin:
            # Seller specific context
            context.update({
                'is_seller': True,
                'products_count': 0,  # TODO: Add actual products count
                'orders_count': 0,    # TODO: Add actual orders count
            })
        
        return context
    
    def _get_order_count(self, user):
        """Get order count for the user"""
        # TODO: Implement actual order count logic
        return 0
    
    def _get_products_count(self, user):
        """Get product count for seller"""
        # TODO: Implement actual product count logic
        return 0
    
    def _get_pending_reviews_count(self):
        """Get count of pending reviews for moderators"""
        # TODO: Implement actual pending reviews count logic
        return 0
    
    def _get_total_users(self):
        """Get total users count for admin"""
        from django.contrib.auth import get_user_model
        return get_user_model().objects.count()
    
    def _get_recent_activity(self, user):
        """Get recent activity based on user role"""
        activity = []
        now = timezone.now()
        
        # Example activity - replace with actual activity from your models
        if user.is_admin:
            activity.extend([
                {'title': 'New user registered', 'description': 'A new user signed up', 'timestamp': now},
                {'title': 'System update', 'description': 'Updated to version 1.0.1', 'timestamp': now},
            ])
        elif user.is_seller:
            activity.append(
                {'title': 'New order received', 'description': 'Order #1234', 'timestamp': now}
            )
        elif user.is_moderator:
            activity.append(
                {'title': 'New review submitted', 'description': 'Needs approval', 'timestamp': now}
            )
        else:
            activity.append(
                {'title': 'Welcome to your dashboard', 'description': 'Start shopping now!', 'timestamp': now}
            )
            
        return activity


class ApplySellerView(LoginRequiredMixin, FormView):
    """View for normal users to apply for seller status"""
    template_name = 'pages/dashboard/apply_seller.html'
    form_class = LicenseApplicationForm
    login_url = reverse_lazy('ecom:login')
    success_url = reverse_lazy('ecom:home')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['has_pending_application'] = self._has_pending_application(self.request.user)
        return context
    
    def form_valid(self, form):
        user = self.request.user
        if not user.is_seller and not self._has_pending_application(user):
            # Create seller application
            LicenseApplication.objects.create(
                user=user,
                application_type='seller',
                message=form.cleaned_data.get('message', None)  # Will be None if empty
            )
            messages.success(self.request, 'Your application to become a seller has been submitted for review.')
        return super().form_valid(form)
    
    def _has_pending_application(self, user):
        return LicenseApplication.objects.filter(
            user=user, 
            application_type='seller',
            status='pending'
        ).exists()


class PendingApprovalsView(LoginRequiredMixin, AdminDashboardMixin, ListView):
    """View for moderators/admins to manage pending approvals"""
    template_name = 'pages/dashboard/admin/pending_approvals.html'
    context_object_name = 'pending_applications'
    paginate_by = 10
    
    def get_queryset(self):
        # Get pending applications based on user role
        queryset = LicenseApplication.objects.filter(status='pending').select_related('user')
        
        # If user is a moderator (not admin), only show seller applications
        if self.request.user.is_moderator and not self.request.user.is_admin:
            queryset = queryset.filter(application_type='seller')
            
        return queryset.order_by('created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_pending'] = self.get_queryset().count()
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle approval/rejection of applications"""
        if not (request.user.is_admin or request.user.is_moderator):
            return JsonResponse({'error': 'Permission denied'}, status=403)
            
        action = request.POST.get('action')
        application_id = request.POST.get('application_id')
        notes = request.POST.get('notes', '')
        
        try:
            application = LicenseApplication.objects.get(
                id=application_id,
                status='pending'  # Only process if still pending
            )
            
            if action == 'approve':
                application.approve(request.user)
                return JsonResponse({
                    'status': 'success',
                    'message': 'Application approved successfully',
                    'new_status': 'approved'
                })
                
            elif action == 'reject':
                application.reject(request.user, notes)
                return JsonResponse({
                    'status': 'success',
                    'message': 'Application rejected',
                    'new_status': 'rejected'
                })
                
        except LicenseApplication.DoesNotExist:
            return JsonResponse({'error': 'Application not found or already processed'}, status=404)
            
        return JsonResponse({'error': 'Invalid action'}, status=400)


class UserManagementView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """View for admins to manage users"""
    template_name = 'pages/dashboard/admin/user_management.html'
    context_object_name = 'users'
    paginate_by = 20
    
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin
    
    def get_queryset(self):
        User = get_user_model()
        return User.objects.all().order_by('-date_joined')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_users'] = get_user_model().objects.count()
        context['active_users'] = get_user_model().objects.filter(is_active=True).count()
        return context


class ApplyModeratorView(LoginRequiredMixin, FormView):
    """View for users to apply for moderator status"""
    template_name = 'pages/dashboard/apply_moderator.html'
    form_class = LicenseApplicationForm
    login_url = reverse_lazy('ecom:login')
    success_url = reverse_lazy('ecom:home')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['has_pending_application'] = self._has_pending_application(self.request.user)
        return context
    
    def form_valid(self, form):
        user = self.request.user
        if not (user.is_moderator or user.is_admin) and not self._has_pending_application(user):
            # Create moderator application
            LicenseApplication.objects.create(
                user=user,
                application_type='moderator',
                message=form.cleaned_data.get('message', None)  # Will be None if empty
            )
            messages.success(self.request, 'Your application to become a moderator has been submitted for review.')
        return super().form_valid(form)
    
    def _has_pending_application(self, user):
        return LicenseApplication.objects.filter(
            user=user, 
            application_type='moderator',
            status='pending'
        ).exists()
