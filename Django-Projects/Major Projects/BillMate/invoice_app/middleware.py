from django.shortcuts import redirect, reverse
from django.conf import settings
from django.contrib import messages
from django.utils.deprecation import MiddlewareMixin
from django.urls import resolve, reverse_lazy

class EmailVerificationMiddleware(MiddlewareMixin):
    """
    Middleware to ensure users have verified their email address
    before accessing protected views.
    """
    # List of URL names that don't require email verification
    EXEMPT_URL_NAMES = [
        'login',
        'logout',
        'register',
        'password_reset',
        'password_reset_done',
        'password_reset_confirm',
        'password_reset_complete',
        'verify_email',
        'resend_verification',
    ]
    
    # URL patterns that don't require email verification
    EXEMPT_URL_PATTERNS = [
        '/static/',
        '/media/',
        '/admin/',
        '/accounts/',  # Django-allauth URLs if used
    ]
    
    def process_request(self, request):
        # Skip middleware for unauthenticated users
        if not request.user.is_authenticated:
            return None
            
        # Skip for favicon.ico and other static files
        if any(request.path.startswith(p) for p in ['/static/', '/media/']) or request.path == '/favicon.ico':
            return None
            
        # Handle staff/superusers - ensure their email is marked as verified
        if request.user.is_superuser or request.user.is_staff:
            if hasattr(request.user, 'email_verified') and not request.user.email_verified:
                request.user.email_verified = True
                request.user.save(update_fields=['email_verified'])
            return None
            
        # Skip middleware for admin
        if request.path.startswith('/admin/'):
            return None
            
        try:
            # Get the current URL name safely
            try:
                resolver_match = resolve(request.path_info)
                url_name = resolver_match.url_name if hasattr(resolver_match, 'url_name') else ''
            except:
                # If URL resolution fails, it's probably not a URL we need to handle
                return None
            
            # Skip middleware for exempt URLs
            if url_name in self.EXEMPT_URL_NAMES or any(
                request.path.startswith(pattern) for pattern in self.EXEMPT_URL_PATTERNS
            ):
                return None
                
            # Check if the user model has email_verified attribute
            if hasattr(request.user, 'email_verified') and not request.user.email_verified:
                # Don't redirect if we're already on the verification page or on the logout page
                if url_name not in ['dashboard', 'logout', 'resend_verification', 'verify_email']:
                    # Only show the message if we're not already on the login page
                    if not request.path.startswith('/accounts/login/'):
                        messages.warning(
                            request,
                            'Please verify your email address before logging in. '
                            'Check your email for the verification link.'
                        )
                        return redirect('login')
                    
        except Exception as e:
            # Only log real errors, not 404s for favicon.ico and similar
            if not request.path == '/favicon.ico':
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f'Error in EmailVerificationMiddleware: {str(e)}')
            
        return None
