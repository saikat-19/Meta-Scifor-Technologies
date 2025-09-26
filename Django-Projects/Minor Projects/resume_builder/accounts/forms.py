from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'username', 'phone_number', 'profile_picture')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove the help text for password fields
        self.fields['password1'].help_text = None
        self.fields['password2'].help_text = None
        
        # Update field attributes
        self.fields['first_name'].widget.attrs.update({'class': 'form-input', 'placeholder': 'Enter your first name'})
        self.fields['last_name'].widget.attrs.update({'class': 'form-input', 'placeholder': 'Enter your last name'})
        self.fields['email'].widget.attrs.update({'class': 'form-input', 'placeholder': 'Enter your email'})
        self.fields['username'].widget.attrs.update({'class': 'form-input', 'placeholder': 'Choose a username'})
        self.fields['phone_number'].widget.attrs.update({'class': 'form-input', 'placeholder': 'Enter your phone number'})
        self.fields['profile_picture'].widget.attrs.update({'class': 'form-input'})
        
        # Add labels
        self.fields['profile_picture'].label = 'Profile Picture (Optional)'

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'username', 'phone_number', 'profile_picture')
