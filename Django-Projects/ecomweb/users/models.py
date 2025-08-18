from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _

class UserManager(BaseUserManager):
    """Custom user model manager where email is the unique identifier"""
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', User.Role.ADMIN)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    """Custom user model with role-based access control"""
    class Role(models.TextChoices):
        NORMAL = 'NORMAL', _('Normal User')
        SELLER = 'SELLER', _('Seller')
        MODERATOR = 'MODERATOR', _('Moderator')
        ADMIN = 'ADMIN', _('Admin')

    # Remove username field and use email as the unique identifier
    username = None
    email = models.EmailField(_('email address'), unique=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.NORMAL)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    is_approved = models.BooleanField(default=False)  # For seller/moderator approval
    
    # Additional fields for seller/moderator applications
    application_date = models.DateTimeField(null=True, blank=True)
    application_notes = models.TextField(blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

    @property
    def is_normal_user(self):
        return self.role == self.Role.NORMAL
    
    @property
    def is_seller(self):
        return self.role == self.Role.SELLER or self.is_superuser
    
    @property
    def is_moderator(self):
        return self.role == self.Role.MODERATOR or self.is_superuser
    
    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
