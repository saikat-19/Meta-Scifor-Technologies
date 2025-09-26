import os
from django.db import models
from django.core.validators import FileExtensionValidator, URLValidator, MinValueValidator, MaxValueValidator
from django.conf import settings
from django.utils.text import slugify
from django.utils import timezone
import uuid
import re
from django.core.exceptions import ValidationError

def resume_profile_pic_path(instance, filename):
    # File will be uploaded to MEDIA_ROOT/resume_pics/resume_<id>/<timestamp>.<ext>
    ext = filename.split('.')[-1]
    timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
    filename = f'profile_{timestamp}.{ext}'
    return os.path.join('resume_pics', f'resume_{instance.id}', filename)

def generate_resume_id():
    """
    Generate a resume ID in the format: RBYYYYMMDDN000001
    """
    # Get current date in YYYYMMDD format
    date_str = timezone.now().strftime('%Y%m%d')
    
    # Find the highest existing resume number for today
    today_resumes = Resume.objects.filter(
        resume_id__startswith=f'RB{date_str}N'
    ).order_by('-resume_id').first()
    
    if today_resumes:
        # Extract the number part and increment
        last_number = int(today_resumes.resume_id[11:])  # Get the number part after 'RBYYYYMMDDN'
        new_number = last_number + 1
    else:
        # First resume of the day
        new_number = 1
    
    # Format with leading zeros
    return f'RB{date_str}N{new_number:08d}'

class Resume(models.Model):
    TEMPLATE_CHOICES = [
        ('modern', 'Modern'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resume_id = models.CharField(
        max_length=20, 
        unique=True, 
        editable=False,
        default=generate_resume_id
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='resumes', null=True, blank=True)
    title = models.CharField(max_length=200, default='My Resume')
    _full_name = models.CharField(max_length=100, blank=True)  # This will be set from first_name + last_name
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    about = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to=resume_profile_pic_path,
        null=True,
        blank=True,
        help_text='Upload a profile picture for your resume (optional)',
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'gif'],
                message='Only image files (JPEG, PNG, GIF) are allowed.'
            )
        ]
    )
    template = models.CharField(max_length=20, choices=TEMPLATE_CHOICES, default='modern')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def full_name(self):
        return self._full_name
    
    @full_name.setter
    def full_name(self, value):
        self._full_name = value
    
    def __str__(self):
        return f"{self.full_name}'s Resume ({self.get_template_display()})"
    
    def save(self, *args, **kwargs):
        is_new = not bool(self.id)
        
        if is_new:
            self.id = uuid.uuid4()
            # Generate new resume_id only for new instances
            self.resume_id = generate_resume_id()
            
        super().save(*args, **kwargs)

class Education(models.Model):
    GRADE_TYPE_CHOICES = [
        ('cgpa', 'CGPA (out of 10)'),
        ('percentage', 'Percentage (%)'),
        ('gpa', 'GPA (out of 4)'),
    ]
    
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='educations')
    school = models.CharField(max_length=200)
    degree = models.CharField(max_length=200)
    field_of_study = models.CharField(max_length=200, blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    currently_studying = models.BooleanField(default=False)
    grade_type = models.CharField(
        max_length=20,
        choices=GRADE_TYPE_CHOICES,
        blank=True,
        null=True,
        help_text='Type of grade (CGPA/Percentage/GPA)'
    )
    grade = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        help_text='Grade value (e.g., 3.8, 85.5, 8.5)',
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100)  # Will be validated based on grade_type in clean()
        ]
    )
    description = models.TextField(blank=True, null=True)
    
    def clean(self):
        if self.grade is not None:
            if self.grade_type == 'cgpa' and self.grade > 10:
                raise ValidationError({
                    'grade': 'CGPA cannot be greater than 10.0'
                })
            elif self.grade_type == 'gpa' and self.grade > 4:
                raise ValidationError({
                    'grade': 'GPA cannot be greater than 4.0'
                })
            elif self.grade_type == 'percentage' and self.grade > 100:
                raise ValidationError({
                    'grade': 'Percentage cannot be greater than 100%'
                })
    
    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.degree} at {self.school}"

class Experience(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='experiences')
    job_title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    location = models.CharField(max_length=200, blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    currently_working = models.BooleanField(default=False)
    description = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.job_title} at {self.company}"

class Skill(models.Model):
    SKILL_LEVELS = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]
    
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='skills')
    name = models.CharField(max_length=100)
    level = models.CharField(max_length=20, choices=SKILL_LEVELS, default='intermediate')
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_level_display()})"


def validate_future_date(value):
    if value and value < timezone.now().date():
        raise ValidationError("Expiration date must be in the future")


class Certification(models.Model):
    """
    Model to store professional certifications and licenses
    """
    resume = models.ForeignKey(
        Resume, 
        on_delete=models.CASCADE, 
        related_name='certifications',
        help_text="The resume this certification belongs to"
    )
    
    name = models.CharField(
        max_length=200,
        help_text="Name of the certification (e.g., AWS Certified Solutions Architect)"
    )
    
    issuing_organization = models.CharField(
        max_length=200,
        help_text="Organization that issued the certification"
    )
    
    issue_date = models.DateField(
        help_text="Date when the certification was issued"
    )
    
    expiration_date = models.DateField(
        blank=True, 
        null=True,
        validators=[validate_future_date],
        help_text="Expiration date (if any)"
    )
    
    credential_id = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="Credential ID or License number (if applicable)"
    )
    
    credential_url = models.URLField(
        max_length=500, 
        blank=True, 
        null=True,
        validators=[URLValidator()],
        help_text="URL to verify the credential (if available online)"
    )
    
    description = models.TextField(
        blank=True, 
        null=True,
        help_text="Additional details about the certification"
    )
    
    class Meta:
        ordering = ['-issue_date']
        verbose_name_plural = "Certifications"
    
    def __str__(self):
        return f"{self.name} from {self.issuing_organization}"
    
    @property
    def is_expired(self):
        """Check if the certification has expired"""
        if not self.expiration_date:
            return False
        return timezone.now().date() > self.expiration_date
    
    @property
    def is_expiring_soon(self):
        """Check if the certification is expiring within the next 30 days"""
        if not self.expiration_date or self.is_expired:
            return False
        days_until_expiry = (self.expiration_date - timezone.now().date()).days
        return 0 <= days_until_expiry <= 30
