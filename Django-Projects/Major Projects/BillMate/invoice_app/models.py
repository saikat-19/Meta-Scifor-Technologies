from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MinValueValidator
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import send_mail
from decimal import Decimal
from typing import Any, Dict, Tuple
import uuid
import secrets
from django.conf import settings

class UserManager(BaseUserManager):
    """Custom user model manager with email as the unique identifier."""
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a user with the given email and password."""
        if not email:
            raise ValueError('The Email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    """Custom user model with email as the unique identifier."""
    email = models.EmailField(_('email address'), unique=True)
    email_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=64, blank=True, null=True)
    verification_token_created_at = models.DateTimeField(blank=True, null=True)
    
    # Set email as the USERNAME_FIELD
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # Remove email from REQUIRED_FIELDS
    
    objects = UserManager()
    
    def generate_verification_token(self):
        """Generate a new verification token."""
        self.verification_token = secrets.token_urlsafe(32)
        self.verification_token_created_at = timezone.now()
        self.save(update_fields=['verification_token', 'verification_token_created_at'])
        return self.verification_token
    
    def send_verification_email(self, request=None):
        """Send verification email to the user."""
        token = self.generate_verification_token()
        
        # Build verification URL
        verification_url = f"{settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000'}/verify-email/{self.id}/{token}/"
        
        # Render email template
        context = {
            'user': self,
            'verification_url': verification_url,
            'site_name': 'BillMate',
        }
        
        subject = 'Verify your email address'
        html_message = render_to_string('emails/verification_email.html', context)
        plain_message = strip_tags(html_message)
        
        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[self.email],
            html_message=html_message,
            fail_silently=False,
        )

class Client(models.Model):
    """Client model to store client information for invoices"""
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='India')
    website = models.URLField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='clients')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        unique_together = ['name', 'email', 'created_by']  # Prevent duplicate clients per user

    def __str__(self):
        return f"{self.name} ({self.email})"

    @property
    def full_address(self):
        """Return formatted full address"""
        address_parts = [self.address, self.city, self.state, self.postal_code, self.country]
        return ', '.join(part for part in address_parts if part)

class Invoice(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        SENT = 'sent', _('Sent')
        PAID = 'paid', _('Paid')
        OVERDUE = 'overdue', _('Overdue')
        CANCELLED = 'cancelled', _('Cancelled')

    invoice_number = models.CharField(max_length=50, unique=True, editable=False)
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    client_name = models.CharField(max_length=200)
    client_email = models.EmailField()
    client_phone = models.CharField(max_length=20, blank=True, null=True)
    client_address = models.TextField()
    issue_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    sent_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True, null=True)
    terms = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invoices')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    view_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, null=True, blank=True)

    class Meta:
        ordering = ['-issue_date']

    def __str__(self):
        return f"{self.invoice_number} - {self.client_name}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            date_str = timezone.now().strftime('%Y%m%d')
            random_str = str(uuid.uuid4().int)[:4].upper()
            self.invoice_number = f'INV-{date_str}-{random_str}'
        if not self.view_token:
            self.view_token = str(uuid.uuid4())
        super().save(*args, **kwargs)

    def update_totals(self):
        """Update subtotal, tax, and total based on line items"""
        self.subtotal = sum(item.total for item in self.items.all())
        self.tax_amount = self.subtotal * Decimal('0.10')  # 10% tax for example
        self.total = self.subtotal + self.tax_amount
        self.save(update_fields=['subtotal', 'tax_amount', 'total'])
        
    def send_email(self, request=None):
        """Send invoice email to client"""
        from django.template.loader import render_to_string
        from django.core.mail import EmailMultiAlternatives
        from django.conf import settings
        
        # Get company information
        company = self.created_by.profile if hasattr(self.created_by, 'profile') else None
        company_name = getattr(company, 'company_name', 'Our Company')
        
        # Build the public invoice URL using the view_token
        invoice_url = request.build_absolute_uri(
            reverse('invoice_app:public_invoice', kwargs={'token': str(self.view_token)})
        ) if (request and self.view_token) else f'#self.view_token'
        
        # Prepare email context
        context = {
            'invoice': self,
            'company_name': company_name,
            'invoice_url': invoice_url,
            'company': company,
        }
        
        # Render email content
        subject = f'Invoice #{self.invoice_number} from {company_name}'
        html_content = render_to_string('emails/invoice_email.html', context)
        text_content = f"Invoice #{self.invoice_number}\n"
        text_content += f"Amount Due: {self.currency if hasattr(self, 'currency') else '$'}{self.total}\n"
        text_content += f"Due Date: {self.due_date.strftime('%B %d, %Y')}\n"
        text_content += f"View your invoice: {invoice_url}"
        
        # Create email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[self.client_email],
            reply_to=[getattr(company, 'email', settings.DEFAULT_FROM_EMAIL)],
        )
        email.attach_alternative(html_content, "text/html")
        
        # Add PDF attachment (optional)
        # pdf = self.generate_pdf()
        # email.attach(f'invoice_{self.invoice_number}.pdf', pdf, 'application/pdf')
        
        # Send email
        try:
            email.send(fail_silently=False)
            # Update invoice status
            self.status = self.Status.SENT
            self.sent_date = timezone.now()
            self.save(update_fields=['status', 'sent_date'])
            return True, None
        except Exception as e:
            return False, str(e)


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(
        'Invoice',
        on_delete=models.CASCADE,
        related_name='items'
    )
    description = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    total = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.description} - {self.quantity} x {self.unit_price}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        # Convert both values to Decimal for proper calculation
        quantity_decimal = Decimal(str(self.quantity))
        unit_price_decimal = Decimal(str(self.unit_price))
        self.total = quantity_decimal * unit_price_decimal
        super().save(*args, **kwargs)
        # Update invoice totals when an item is saved
        self.invoice.update_totals()  # type: ignore[attr-defined]

    def delete(self, *args: Any, **kwargs: Any) -> Tuple[int, Dict[str, int]]:
        invoice = self.invoice
        result = super().delete(*args, **kwargs)
        # Update invoice totals when an item is deleted
        invoice.update_totals()  # type: ignore[attr-defined]
        return result


class UserProfile(models.Model):
    """User profile model to store company information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    company_name = models.CharField(max_length=200, default='BillMate')
    address = models.TextField(default='123 Business Street')
    city = models.CharField(max_length=100, default='City')
    state = models.CharField(max_length=100, default='State')
    postal_code = models.CharField(max_length=20, default='12345')
    country = models.CharField(max_length=100, default='India')
    phone = models.CharField(max_length=20, default='(321) 456-7890')
    email = models.EmailField(default='info@billmate.com')
    website = models.URLField(blank=True, null=True, default='www.billmate.com')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.company_name} - {self.user.username}"  # type: ignore[attr-defined]

    @property
    def full_address(self):
        """Return formatted full address"""
        return f"{self.address}\n{self.city}, {self.state} {self.postal_code}\n{self.country}"

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
