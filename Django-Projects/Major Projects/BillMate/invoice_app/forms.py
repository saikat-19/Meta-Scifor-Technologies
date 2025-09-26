from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model, authenticate
from .models import Invoice, InvoiceItem, UserProfile, Client
from django.forms import inlineformset_factory
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from typing import Any, Dict, Optional, Type, TypeVar

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-input block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
        'placeholder': 'Enter your email'
    }))
    first_name = forms.CharField(required=True, widget=forms.TextInput(attrs={
        'class': 'form-input block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
        'placeholder': 'First name'
    }))
    last_name = forms.CharField(required=True, widget=forms.TextInput(attrs={
        'class': 'form-input block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
        'placeholder': 'Last name'
    }))

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Update widget attributes for built-in fields
        self.fields['username'].widget.attrs.update({
            'class': 'form-input block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
            'placeholder': 'Choose a username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-input block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
            'placeholder': 'Create a password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-input block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
            'placeholder': 'Confirm password'
        })
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user

class InvoiceForm(forms.ModelForm):
    client = forms.ModelChoiceField(
        queryset=None,  # Will be set in __init__
        required=False,
        empty_label="Select a client or enter manually",
        widget=forms.Select(attrs={
            'class': 'form-select w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500',
            'id': 'client-select'
        })
    )
    
    class Meta:
        model = Invoice
        fields = [
            'client', 'client_name', 'client_email', 'client_phone', 'client_address',
            'issue_date', 'due_date', 'status', 'notes', 'terms'
        ]
        widgets = {
            'issue_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'status': forms.Select(attrs={'class': 'form-select w-full'}),
            'client_address': forms.Textarea(attrs={'rows': 3, 'class': 'form-textarea'}),
            'notes': forms.Textarea(attrs={'rows': 2, 'class': 'form-textarea'}),
            'terms': forms.Textarea(attrs={'rows': 2, 'class': 'form-textarea'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)  # Get user from kwargs if provided
        super().__init__(*args, **kwargs)
        
        # Populate client dropdown with user's clients
        if self.user:
            # Import here to avoid circular imports
            from .models import Client
            self.fields['client'].queryset = Client.objects.filter(created_by=self.user).order_by('name')  # type: ignore[attr-defined]
        else:
            # Set empty queryset if no user
            from .models import Client
            self.fields['client'].queryset = Client.objects.none()  # type: ignore[attr-defined]
        
        # Set default due date to 15 days from now
        if not self.instance.pk:
            self.initial['issue_date'] = timezone.now().date()
            self.initial['due_date'] = timezone.now().date() + timezone.timedelta(days=15)
            self.initial['status'] = Invoice.Status.DRAFT  # Set default status
        
        # Add custom CSS classes to all fields
        for field_name, field in self.fields.items():
            if field_name == 'status':
                field.widget.attrs.update({
                    'class': 'form-select w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500',
                })
            elif field_name in ['notes', 'terms', 'client_address']:
                field.widget.attrs.update({
                    'class': 'form-control w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500',
                })
            elif field_name not in ['client']:  # Skip client field as it already has styling
                field.widget.attrs.update({
                    'class': 'form-control w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500',
                })


class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ['description', 'quantity', 'unit_price']
        widgets = {
            'description': forms.TextInput(attrs={
                'class': 'form-input block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
                'placeholder': 'Item description'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-input block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
                'min': '1',
                'step': '1',
                'placeholder': 'Qty'
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-input block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
                'min': '0.01',
                'step': '0.01',
                'placeholder': 'Price'
            }),
        }


# Formset for invoice items
InvoiceItemFormSet = inlineformset_factory(
    Invoice,
    InvoiceItem,
    form=InvoiceItemForm,
    extra=0,
    can_delete=True,
    min_num=0,
    validate_min=False
)


class UserProfileForm(forms.ModelForm):
    """Form for user profile/company information"""
    class Meta:
        model = UserProfile
        fields = [
            'company_name', 'address', 'city', 'state', 'postal_code',
            'country', 'phone', 'email', 'website'
        ]
        widgets = {
            'company_name': forms.TextInput(attrs={
                'class': 'form-control w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'Your Company Name'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'rows': 3,
                'placeholder': '123 Business Street'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'City'
            }),
            'state': forms.TextInput(attrs={
                'class': 'form-control w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'State'
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-control w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'placeholder': '12345'
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'India'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'placeholder': '(321) 456-7890'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'info@company.com'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'www.company.com'
            }),
        }


class ClientForm(forms.ModelForm):
    """Form for client information"""
    class Meta:
        model = Client
        fields = [
            'name', 'email', 'phone', 'address', 'city', 'state', 
            'postal_code', 'country', 'website'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'Client Name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'client@example.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'placeholder': '(123) 456-7890'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'rows': 3,
                'placeholder': '123 Client Street'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'City'
            }),
            'state': forms.TextInput(attrs={
                'class': 'form-control w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'State'
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-control w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'placeholder': '12345'
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'India'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'www.client.com'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
    def save(self, commit=True):
        client = super().save(commit=False)
        if self.user:
            client.created_by = self.user
        if commit:
            client.save()
        return client


class ResendVerificationForm(forms.Form):
    """Form for requesting a new verification email."""
    email = forms.EmailField(
        label=_('Email address'),
        widget=forms.EmailInput(attrs={
            'class': 'form-input w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
            'placeholder': _('Enter your email address'),
            'autocomplete': 'email',
            'autofocus': True,
        })
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    def clean_email(self) -> str:
        """Validate that a user exists with the given email and is not already verified."""
        email = self.cleaned_data.get('email')
        
        # Normalize the email address (case-insensitive lookup)
        email = email.lower()
        
        try:
            user = User.objects.get(email__iexact=email)
            if hasattr(user, 'email_verified') and user.email_verified:
                raise ValidationError(
                    _('This email is already verified. You can log in with your credentials.')
                )
            return email
        except User.DoesNotExist:
            raise ValidationError(
                _('No account is registered with this email address. Please check the email or register a new account.')
            )

    def get_user(self) -> Optional[Type[User]]:
        """Return the user with the given email, case-insensitive."""
        email = self.cleaned_data.get('email')
        if not email:
            return None
            
        try:
            return User.objects.get(email__iexact=email.lower())
        except User.DoesNotExist:
            return None
