from django.db import models
from django.utils import timezone
from django.utils.timezone import now
from django.core.validators import MinValueValidator

class Task(models.Model):
    title = models.CharField(max_length=200)
    details = models.TextField(blank=True, null=True)
    due_date = models.DateField(
        'Due Date',
        blank=True,
        null=True,
        validators=[MinValueValidator(limit_value=now().date())]
    )
    completed = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
        
    class Meta:
        ordering = ['-created']
