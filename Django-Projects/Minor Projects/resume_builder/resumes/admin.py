from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    Resume, 
    Education, 
    Experience, 
    Skill, 
    Certification
)

class EducationInline(admin.TabularInline):
    model = Education
    extra = 1
    fields = ('degree', 'institution', 'start_date', 'end_date', 'grade', 'grade_type')

class ExperienceInline(admin.TabularInline):
    model = Experience
    extra = 1
    fields = ('job_title', 'company', 'start_date', 'end_date', 'description')

class SkillInline(admin.TabularInline):
    model = Skill
    extra = 1
    fields = ('name', 'proficiency')

class CertificationInline(admin.TabularInline):
    model = Certification
    extra = 1
    fields = ('name', 'issuing_organization', 'issue_date', 'expiration_date', 'credential_id', 'credential_url')

class ResumeAdmin(admin.ModelAdmin):
    list_display = ('title', 'full_name', 'email', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('title', 'full_name', 'email')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [EducationInline, ExperienceInline, SkillInline, CertificationInline]

# Register models
admin.site.register(Resume, ResumeAdmin)
admin.site.register(Education)
admin.site.register(Experience)
admin.site.register(Skill)
admin.site.register(Certification)
