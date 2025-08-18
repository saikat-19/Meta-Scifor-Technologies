from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        # print(f"DEBUG: Starting authentication. Username: {username}, Email: {kwargs.get('email')}")
        
        UserModel = get_user_model()
        
        # Get email from either username or email parameter
        email = kwargs.get('email', username)
        if not email:
            # print("DEBUG: No email provided")
            return None
            
        try:
            # print(f"DEBUG: Looking for user with email: {email}")
            # Try to find a user with the provided email (case-insensitive)
            user = UserModel.objects.filter(email__iexact=email).first()
            
            if user is None:
                # print(f"DEBUG: No user found with email: {email}")
                return None
                
            # print(f"DEBUG: Found user: {user.email}")
            # print(f"DEBUG: Checking password for user: {user.email}")
            
            # Verify the password
            if user.check_password(password):
                # print(f"DEBUG: Password valid for user: {user.email}")
                return user
            else:
                # print("DEBUG: Invalid password")
                return None
                
        except Exception as e:
            # print(f"DEBUG: Exception during authentication: {str(e)}")
            return None

    def get_user(self, user_id):
        UserModel = get_user_model()
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None
