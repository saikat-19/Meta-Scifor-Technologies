from django.urls import path
from .auth_views import SignUpView

# No app_name here since this is included under the 'resumes' namespace in the main urls.py
urlpatterns = [
    path('', SignUpView.as_view(), name='signup'),
]
