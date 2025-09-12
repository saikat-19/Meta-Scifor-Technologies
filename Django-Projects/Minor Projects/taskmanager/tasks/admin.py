from django.contrib import admin
from .models import Task

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'completed', 'due_date', 'created', 'updated')
    list_filter = ('completed', 'due_date', 'created', 'user')
    search_fields = ('title', 'details', 'user__username')
    list_editable = ('completed',)
    date_hierarchy = 'created'
    ordering = ('-created',)
    
    fieldsets = (
        ('Task Information', {
            'fields': ('user', 'title', 'details')
        }),
        ('Scheduling', {
            'fields': ('due_date', 'completed')
        }),
        ('Timestamps', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('created', 'updated')
