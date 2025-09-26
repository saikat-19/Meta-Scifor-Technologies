from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.views import LoginView as BaseLoginView
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
from django.http import Http404
from django.conf import settings
from datetime import timedelta

User = get_user_model()

class LoginView(BaseLoginView):
    """Custom login view that extends the default login view."""
    template_name = 'registration/login_custom.html'
    form_class = AuthenticationForm
    redirect_authenticated_user = True
    
    def form_valid(self, form):
        user = form.get_user()
        
        # Check if email is verified if required
        if not user.email_verified:
            messages.warning(
                self.request,
                _('Please verify your email address before logging in. '
                  'Check your email for the verification link.')
            )
            return self.form_invalid(form)
            
        return super().form_valid(form)

class VerifyEmailView(View):
    """Handle email verification links."""
    @method_decorator(never_cache)
    def get(self, request, user_id, token):
        try:
            user = User.objects.get(pk=user_id)
            
            # Check if already verified
            if user.email_verified:
                return render(request, 'registration/verification_success.html', {
                    'user': user
                })
                
            # Check token
            if (user.verification_token == token and 
                user.verification_token_created_at and
                user.verification_token_created_at > timezone.now() - timedelta(days=settings.EMAIL_VERIFICATION_EXPIRE_DAYS)):
                
                # Mark as verified
                user.email_verified = True
                user.verification_token = None
                user.verification_token_created_at = None
                user.save()
                
                # Log the user in if not already
                if not request.user.is_authenticated:
                    user.backend = 'django.contrib.auth.backends.ModelBackend'
                    login(request, user)
                
                messages.success(
                    request,
                    _('Your email has been verified successfully!')
                )
                return render(request, 'registration/verification_success.html', {
                    'user': user
                })
            
            # Invalid or expired token
            return render(request, 'registration/verification_error.html', {
                'error': 'invalid'
            })
            
        except User.DoesNotExist:
            raise Http404("Invalid verification link.")

def resend_verification_email(request):
    """Resend verification email."""
    from .forms import ResendVerificationForm
    
    if request.method == 'POST':
        form = ResendVerificationForm(request.POST, request=request)
        if form.is_valid():
            try:
                user = form.get_user()
                user.send_verification_email()
                messages.success(
                    request,
                    _('A new verification email has been sent to %(email)s. Please check your inbox.') % 
                    {'email': user.email}
                )
                return redirect('login')
                
            except Exception as e:
                messages.error(
                    request,
                    _('Failed to send verification email. Please try again later.')
                )
    else:
        form = ResendVerificationForm(request=request)
    
    return render(request, 'registration/resend_verification.html', {'form': form})
