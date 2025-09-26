from django import forms
from django.forms import inlineformset_factory
from .models import Resume, Education, Experience, Skill
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from django.urls import reverse_lazy
from datetime import date

class ResumeForm(forms.ModelForm):
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    
    class Meta:
        model = Resume
        fields = [
            'title', 'first_name', 'last_name', 'email', 'phone', 'address', 
            'about', 'profile_picture', 'template'
        ]
        widgets = {
            
            'about': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Add Bootstrap classes to form fields
        for field in self.fields:
            if field != 'profile_picture':
                self.fields[field].widget.attrs.update({'class': 'form-control'})
            
            if field in ['title', 'first_name', 'last_name', 'email', 'phone', 'address']:
                self.fields[field].widget.attrs.update({'placeholder': f'Enter {field.replace("_", " ").title()}'})
        
        # Add specific classes to specific fields
        self.fields['about'].widget.attrs.update({'rows': 4, 'class': 'form-control'})
        
        # Customize profile picture field
        self.fields['profile_picture'].widget.attrs.update({
            'class': 'form-control-file',
            'data-current-value': self.instance.profile_picture.name.split('/')[-1] if self.instance.profile_picture else ''
        })
        
        if self.instance and self.instance.pk:
            # If editing, populate first_name and last_name from full_name
            name_parts = self.instance.full_name.split(' ', 1)
            self.fields['first_name'].initial = name_parts[0]
            if len(name_parts) > 1:
                self.fields['last_name'].initial = name_parts[1]
    
    def save(self, commit=True):
        # Combine first_name and last_name into full_name before saving
        self.instance.full_name = f"{self.cleaned_data['first_name']} {self.cleaned_data['last_name']}"
        
        # Set the user if it's a new instance and we have a user
        if not self.instance.pk and hasattr(self, 'user') and self.user:
            self.instance.user = self.user
            
        return super().save(commit=commit)
    
    def clean_profile_picture(self):
        picture = self.cleaned_data.get('profile_picture')
        if picture:
            if picture.size > 2 * 1024 * 1024:  # 2MB limit
                raise ValidationError("Image file too large (maximum 2MB)")
        return picture

class EducationForm(forms.ModelForm):
    class Meta:
        model = Education
        fields = ['school', 'degree', 'field_of_study', 'start_date', 
                 'end_date', 'currently_studying', 'grade_type', 'grade', 'description']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'grade_type': forms.Select(attrs={'class': 'form-select'}),
            'grade': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'max': '100'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        currently_studying = cleaned_data.get('currently_studying', False)
        grade_type = cleaned_data.get('grade_type')
        grade = cleaned_data.get('grade')
        
        if start_date and end_date and start_date > end_date:
            raise ValidationError({
                'end_date': 'End date must be after start date.'
            })
            
        if currently_studying and end_date:
            raise ValidationError({
                'currently_studying': 'Cannot have an end date if currently studying.',
                'end_date': 'Leave end date empty if currently studying.'
            })
            
        if not currently_studying and not end_date:
            raise ValidationError({
                'end_date': 'Please provide an end date or check "Currently Studying".'
            })
        
        # Make grade_type and grade optional but validate if either is provided
        if grade is not None and not grade_type:
            raise ValidationError({
                'grade_type': 'Please select a grade type if providing a grade.'
            })
        
        if grade_type and grade is None:
            raise ValidationError({
                'grade': 'Please provide a grade value if selecting a grade type.'
            })
        
        # If both are provided, validate based on grade_type
        if grade is not None and grade_type:
            if grade_type == 'cgpa' and grade > 10:
                raise ValidationError({
                    'grade': 'CGPA cannot be greater than 10.0'
                })
            elif grade_type == 'gpa' and grade > 4:
                raise ValidationError({
                    'grade': 'GPA cannot be greater than 4.0'
                })
            elif grade_type == 'percentage' and grade > 100:
                raise ValidationError({
                    'grade': 'Percentage cannot be greater than 100%'
                })
        
        return cleaned_data

class ExperienceForm(forms.ModelForm):
    class Meta:
        model = Experience
        fields = ['job_title', 'company', 'location', 'start_date', 
                 'end_date', 'currently_working', 'description']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        currently_working = cleaned_data.get('currently_working')
        
        if start_date and end_date and start_date > end_date:
            raise ValidationError({
                'end_date': 'End date must be after start date.'
            })
            
        if currently_working and end_date:
            raise ValidationError({
                'currently_working': 'Cannot have an end date if currently working here.',
                'end_date': 'Leave end date empty if currently working here.'
            })
            
        if not currently_working and not end_date:
            raise ValidationError({
                'end_date': 'Please provide an end date or check "Currently Working".'
            })
            
        return cleaned_data

class SkillForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = ['name', 'level']

# Formset factories
EducationFormSet = inlineformset_factory(
    Resume, Education, form=EducationForm, 
    extra=1, can_delete=True, can_delete_extra=True
)

ExperienceFormSet = inlineformset_factory(
    Resume, Experience, form=ExperienceForm, 
    extra=1, can_delete=True, can_delete_extra=True
)

SkillFormSet = inlineformset_factory(
    Resume, Skill, form=SkillForm,
    extra=3, can_delete=True, can_delete_extra=True
)
