from django.db import models
from django.utils import timezone
from django.utils.timezone import now
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from django.db.models.manager import Manager

class Task(models.Model):
    # Django ORM objects manager - using Any to avoid type checking issues
    objects: Any
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    details = models.TextField(blank=True, null=True)
    due_date = models.DateField(
        'Due Date',
        blank=True,
        null=True,
        validators=[MinValueValidator(limit_value=now().date())]
    )
    completed: models.BooleanField = models.BooleanField(default=False)  # type: ignore
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return str(self.title)
        
    class Meta:
        ordering = ['-created']
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'
