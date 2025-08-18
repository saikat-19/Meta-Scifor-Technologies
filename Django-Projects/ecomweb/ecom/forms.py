from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.exceptions import ValidationError
from .models import LicenseApplication, Product, Category, ProductImage
from django.utils.text import slugify

# Get the custom user model
User = get_user_model()

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'compare_at_price', 'category', 'stock', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-input'}),
            'price': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'compare_at_price': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'stock': forms.NumberInput(attrs={'min': '0'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        compare_at_price = cleaned_data.get('compare_at_price')
        price = cleaned_data.get('price')
        
        if compare_at_price and price and compare_at_price <= price:
            raise forms.ValidationError("Compare at price must be greater than the selling price.")
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.slug:
            instance.slug = slugify(instance.name)
            # Ensure slug is unique
            if Product.objects.filter(slug=instance.slug).exists():
                instance.slug = f"{instance.slug}-{Product.objects.count() + 1}"
        if commit:
            instance.save()
        return instance

class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image', 'alt_text', 'is_primary']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-input'}),
            'alt_text': forms.TextInput(attrs={'class': 'form-input'}),
        }

class SignUpForm(UserCreationForm):
    email = forms.EmailField(
        max_length=254,
        required=True,
        help_text='Required. Enter a valid email address.',
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': 'Email address'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': 'First name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': 'Last name'
        })
    )
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': 'Phone number (optional)'
        })
    )
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': 'Your address (optional)',
            'rows': 2
        })
    )
    
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'phone_number', 'address')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove the username field as we're using email
        if 'username' in self.fields:
            del self.fields['username']
            
        # Add Tailwind classes to form fields
        self.fields['password1'].widget.attrs.update({
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': 'Password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': 'Confirm Password'
        })
        
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already in use. Please use a different email address.")
        return email
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove the username field as we're using email
        if 'username' in self.fields:
            del self.fields['username']
            
        # Add Tailwind classes to form fields
        self.fields['password1'].widget.attrs.update({
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': 'Password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': 'Confirm Password'
        })
        
    def save(self, commit=True):
        # Save the user with the email as the username
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.username = self.cleaned_data['email']  # Use email as username
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            # Save the user first
            user.save()
            
            # Get or create user profile
            from .models import UserProfile
            profile, created = UserProfile.objects.get_or_create(user=user)
            
            # Update profile fields if they exist in the form data
            if 'phone_number' in self.cleaned_data and self.cleaned_data['phone_number']:
                profile.phone_number = self.cleaned_data['phone_number']
            if 'address' in self.cleaned_data and self.cleaned_data['address']:
                profile.address = self.cleaned_data['address']
                
            # Save the profile
            profile.save()
            
        return user


class LicenseApplicationForm(forms.ModelForm):
    """Form for submitting license applications (seller/moderator)"""
    message = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': 'Tell us why you want to become a seller/moderator (optional)',
            'rows': 4
        }),
        help_text='Optional: Provide any additional information that might help with your application.'
    )
    
    class Meta:
        model = LicenseApplication
        fields = ['message']
        
    def clean_message(self):
        message = self.cleaned_data.get('message', '').strip()
        return message if message else None
class UserProfileForm(forms.ModelForm):
    # User model fields
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': 'Email address'
        })
    )
    first_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': 'First name'
        })
    )
    last_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': 'Last name'
        })
    )
    
    # UserProfile model fields
    phone_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': 'Phone number (e.g., +1234567890)'
        })
    )
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': 'Your complete shipping address',
            'rows': 3
        })
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial values from the user instance
        if self.instance and self.instance.pk:
            self.fields['email'].initial = self.instance.email
            self.fields['first_name'].initial = self.instance.first_name
            self.fields['last_name'].initial = self.instance.last_name
            
            # Set initial values from user profile if it exists
            if hasattr(self.instance, 'profile'):
                self.fields['phone_number'].initial = self.instance.profile.phone_number
                self.fields['address'].initial = self.instance.profile.address
        
    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Get the current user's email from the instance
        current_email = self.instance.email if self.instance and hasattr(self.instance, 'email') else None
        
        # Only validate if the email has changed
        if email != current_email:
            # Check if email is already in use by another user
            if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
                raise ValidationError('This email is already in use. Please use a different email address.')
        return email
        
    def save(self, commit=True):
        user = super().save(commit=False)
        
        if commit:
            user.save()
            
            # Get or create user profile
            from .models import UserProfile
            profile, created = UserProfile.objects.get_or_create(user=user)
            
            # Update profile fields
            profile.phone_number = self.cleaned_data['phone_number']
            profile.address = self.cleaned_data['address']
            profile.save()
            
        return user
