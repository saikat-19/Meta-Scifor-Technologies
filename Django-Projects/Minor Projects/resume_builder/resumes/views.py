import os
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import Resume, Education, Experience, Skill
from .forms import ResumeForm, EducationForm, ExperienceForm, SkillForm, \
    EducationFormSet, ExperienceFormSet, SkillFormSet

class HomeView(TemplateView):
    """Home page view"""
    template_name = 'resumes/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Home - Resume Builder'
        return context

class ResumeCreateView(LoginRequiredMixin, CreateView):
    model = Resume
    form_class = ResumeForm
    template_name = 'resumes/create_resume.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if hasattr(self, 'request') and hasattr(self.request, 'user'):
            kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get the instance (for updates) or None (for creates)
        instance = self.object if hasattr(self, 'object') else None
        
        # Initialize formsets with proper data and files
        if self.request.method == 'POST':
            context['education_formset'] = EducationFormSet(
                self.request.POST,
                self.request.FILES,
                prefix='education',
                instance=instance
            )
            context['experience_formset'] = ExperienceFormSet(
                self.request.POST,
                self.request.FILES,
                prefix='experience',
                instance=instance
            )
            context['skill_formset'] = SkillFormSet(
                self.request.POST,
                self.request.FILES,
                prefix='skill',
                instance=instance
            )
        else:
            # For GET requests, initialize empty formsets
            context['education_formset'] = EducationFormSet(
                prefix='education',
                instance=instance
            )
            context['experience_formset'] = ExperienceFormSet(
                prefix='experience',
                instance=instance
            )
            context['skill_formset'] = SkillFormSet(
                prefix='skill',
                instance=instance
            )
            
        # Add form media to context
        context['form_media'] = context['form'].media
        
        return context
    
    def form_valid(self, form):
        print("Form is valid, processing...")  # Debug log
        context = self.get_context_data()
        
        try:
            # Save the resume first
            self.object = form.save(commit=False)
            self.object.user = self.request.user
            self.object.save()
            print("Resume saved with ID:", self.object.id)  # Debug log
            
            # Initialize formsets with the saved instance
            education_formset = EducationFormSet(
                self.request.POST,
                instance=self.object,
                prefix='education'
            )
            
            experience_formset = ExperienceFormSet(
                self.request.POST,
                instance=self.object,
                prefix='experience'
            )
            
            skill_formset = SkillFormSet(
                self.request.POST,
                instance=self.object,
                prefix='skill'
            )
            
            # Process education formset
            education_errors = None
            if education_formset.is_valid():
                education_instances = education_formset.save(commit=False)
                print(f"Processing {len(education_instances)} education instances")  # Debug log
                for instance in education_instances:
                    if instance.school:  # Only save if school is provided
                        instance.resume = self.object
                        instance.save()
                        print(f"Saved education: {instance}")  # Debug log
                
                # Handle deleted education instances
                for obj in education_formset.deleted_objects:
                    print(f"Deleting education: {obj}")  # Debug log
                    obj.delete()
            else:
                education_errors = education_formset.errors
                print("Education formset errors:", education_errors)  # Debug log
            
            # Process experience formset
            experience_errors = None
            if experience_formset.is_valid():
                experience_instances = experience_formset.save(commit=False)
                print(f"Processing {len(experience_instances)} experience instances")  # Debug log
                for instance in experience_instances:
                    if instance.job_title:  # Only save if job_title is provided
                        instance.resume = self.object
                        instance.save()
                        print(f"Saved experience: {instance}")  # Debug log
                
                # Handle deleted experience instances
                for obj in experience_formset.deleted_objects:
                    print(f"Deleting experience: {obj}")  # Debug log
                    obj.delete()
            else:
                experience_errors = experience_formset.errors
                print("Experience formset errors:", experience_errors)  # Debug log
            
            # Process skill formset
            skill_errors = None
            if skill_formset.is_valid():
                skill_instances = skill_formset.save(commit=False)
                print(f"Processing {len(skill_instances)} skill instances")  # Debug log
                for instance in skill_instances:
                    if instance.name:  # Only save if name is provided
                        instance.resume = self.object
                        instance.save()
                        print(f"Saved skill: {instance}")  # Debug log
                
                # Handle deleted skill instances
                for obj in skill_formset.deleted_objects:
                    print(f"Deleting skill: {obj}")  # Debug log
                    obj.delete()
            else:
                skill_errors = skill_formset.errors
                print("Skill formset errors:", skill_errors)  # Debug log
            
            # Check if it's an AJAX request
            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                from django.http import JsonResponse
                
                # If there are any formset errors, return them
                if any([education_errors, experience_errors, skill_errors]):
                    print("Returning formset errors")  # Debug log
                    return JsonResponse({
                        'success': False,
                        'errors': {
                            'education': education_errors,
                            'experience': experience_errors,
                            'skill': skill_errors
                        },
                        'message': 'Please correct the errors below.'
                    }, status=400)
                    
                # If everything is successful, return success response
                print("Form submission successful, redirecting...")  # Debug log
                return JsonResponse({
                    'success': True,
                    'redirect': reverse('resumes:resume_detail', kwargs={'pk': self.object.pk})
                })
            
            # For non-AJAX requests
            messages.success(self.request, 'Resume created successfully!')
            return redirect('resumes:resume_detail', pk=self.object.pk)
            
        except Exception as e:
            print(f"Error in form_valid: {str(e)}")  # Debug log
            import traceback
            traceback.print_exc()  # Print full traceback
            
            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                from django.http import JsonResponse
                return JsonResponse({
                    'success': False,
                    'message': f'An error occurred: {str(e)}',
                    'error': str(e)
                }, status=500)
                
            messages.error(self.request, f'An error occurred: {str(e)}')
            return self.render_to_response(self.get_context_data(form=form))
        
    def form_invalid(self, form):
        # Log form errors for debugging
        print("Form errors:", form.errors)
        print("Form data:", self.request.POST)
        
        # Check if it's an AJAX request
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            from django.http import JsonResponse
            return JsonResponse({
                'success': False,
                'errors': {
                    'form': form.errors,
                    'non_field_errors': form.non_field_errors()
                }
            }, status=400)
            
        # For non-AJAX requests, re-render the form with errors
        return self.render_to_response(self.get_context_data(form=form))
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.method in ('POST', 'PUT'):
            kwargs.update({
                'data': self.request.POST,
                'files': self.request.FILES,
            })
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.method == 'POST':
            context['education_formset'] = EducationFormSet(
                self.request.POST,
                instance=self.object,
                prefix='education'
            )
            context['experience_formset'] = ExperienceFormSet(
                self.request.POST,
                instance=self.object,
                prefix='experience'
            )
            context['skill_formset'] = SkillFormSet(
                self.request.POST,
                instance=self.object,
                prefix='skill'
            )
        else:
            context['education_formset'] = EducationFormSet(
                instance=self.object,
                prefix='education'
            )
            context['experience_formset'] = ExperienceFormSet(
                instance=self.object,
                prefix='experience'
            )
            context['skill_formset'] = SkillFormSet(
                instance=self.object,
                prefix='skill'
            )
            
            # Add education data to context for JavaScript
            # Only try to access educations if self.object exists (not None for new resumes)
            if self.object:
                educations = self.object.educations.all().order_by('-start_date')
                print(f"Found {educations.count()} education records")
                
                educations_list = []
                for edu in educations:
                    edu_data = {
                        'id': str(edu.id) if edu.id else '',
                        'school': edu.school or '',
                        'degree': edu.degree or '',
                        'field': edu.field_of_study or '',
                        'start_date': edu.start_date.strftime('%Y-%m') if edu.start_date else '',
                        'end_date': edu.end_date.strftime('%Y-%m') if edu.end_date else '',
                        'currently_studying': bool(edu.currently_studying),
                        'grade': str(edu.grade) if edu.grade is not None else '',
                        'grade_type': edu.grade_type or '',
                        'description': edu.description or ''
                    }
                    # print(f"Education data: {edu_data}")
                    educations_list.append(edu_data)
            else:
                educations_list = []
                print("New resume, no existing educations")
            
            # Add work experience data to context for JavaScript
            # Only try to access experiences if self.object exists
            if self.object:
                experiences = self.object.experiences.all().order_by('-start_date')
                print(f"Found {experiences.count()} experience records")
                
                experiences_list = []
                for exp in experiences:
                    exp_data = {
                        'id': str(exp.id) if exp.id else '',
                        'job_title': exp.job_title or '',
                        'company': exp.company or '',
                        'location': exp.location or '',
                        'start_date': exp.start_date.strftime('%Y-%m') if exp.start_date else '',
                        'end_date': exp.end_date.strftime('%Y-%m') if exp.end_date else '',
                        'currently_working': bool(exp.currently_working),
                        'description': exp.description or ''
                    }
                    # print(f"Experience data: {exp_data}")
                    experiences_list.append(exp_data)
            else:
                experiences_list = []
                print("New resume, no existing experiences")
            
            # Add skills data to context for JavaScript
            # Only try to access skills if self.object exists
            if self.object:
                skills = self.object.skills.all()
                print(f"Found {skills.count()} skill records")
                
                skills_list = []
                for skill in skills:
                    skill_data = {
                        'id': str(skill.id) if skill.id else '',
                        'name': skill.name or ''
                        # ,'level': skill.level or 'intermediate',
                    }
                    # print(f"Skill data: {skill_data}")
                    skills_list.append(skill_data)
            else:
                skills_list = []
                print("New resume, no existing skills")
            
            import json
            context['educations_json'] = json.dumps(educations_list)
            context['experiences_json'] = json.dumps(experiences_list)
            context['skills_json'] = json.dumps(skills_list)
            
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        is_ajax = self.request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        # Save the main form first
        self.object = form.save(commit=False)
        
        # Initialize formsets with the POST data and files
        education_formset = EducationFormSet(
            self.request.POST,
            instance=self.object,
            prefix='education'
        )
        
        experience_formset = ExperienceFormSet(
            self.request.POST,
            instance=self.object,
            prefix='experience'
        )
        
        skill_formset = SkillFormSet(
            self.request.POST,
            instance=self.object,
            prefix='skill'
        )
        
        # Check if all forms are valid
        form_valid = form.is_valid()
        education_valid = education_formset.is_valid()
        experience_valid = experience_formset.is_valid()
        skill_valid = skill_formset.is_valid()
        
        if not all([form_valid, education_valid, experience_valid, skill_valid]):
            # If any form is invalid, return the form with errors
            if is_ajax:
                from django.http import JsonResponse
                return JsonResponse({
                    'success': False,
                    'errors': {
                        'form': form.errors,
                        'education_formset': education_formset.errors if not education_valid else [],
                        'experience_formset': experience_formset.errors if not experience_valid else [],
                        'skill_formset': skill_formset.errors if not skill_valid else [],
                        'non_field_errors': form.non_field_errors()
                    }
                }, status=400)
            else:
                return self.render_to_response(
                    self.get_context_data(
                        form=form,
                        education_formset=education_formset,
                        experience_formset=experience_formset,
                        skill_formset=skill_formset
                    )
                )
        
        try:
            # Save the main form
            self.object.save()
            
            # Process education formset
            education_instances = education_formset.save(commit=False)
            for instance in education_instances:
                if instance.school:  # Only save if school is provided
                    instance.resume = self.object
                    instance.save()
            
            # Handle deleted education instances
            for obj in education_formset.deleted_objects:
                obj.delete()
            
            # Process experience formset
            experience_instances = experience_formset.save(commit=False)
            for instance in experience_instances:
                if instance.job_title:  # Only save if job_title is provided
                    instance.resume = self.object
                    instance.save()
            
            # Handle deleted experience instances
            for obj in experience_formset.deleted_objects:
                obj.delete()
            
            # Process skill formset
            skill_instances = skill_formset.save(commit=False)
            for instance in skill_instances:
                if instance.name:  # Only save if name is provided
                    instance.resume = self.object
                    instance.save()
            
            # Handle deleted skill instances
            for obj in skill_formset.deleted_objects:
                obj.delete()
            
            # Save many-to-many data if needed
            form.save_m2m()
            
            if is_ajax:
                from django.http import JsonResponse
                from django.urls import reverse
                return JsonResponse({
                    'success': True,
                    'message': 'Resume updated successfully!',
                    'redirect_url': reverse('resumes:resume_detail', kwargs={'pk': self.object.pk})
                })
            
            messages.success(self.request, 'Resume updated successfully!')
            return redirect('resumes:resume_detail', pk=self.object.pk)
            
        except Exception as e:
            if is_ajax:
                from django.http import JsonResponse
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=500)
            messages.error(self.request, f'An error occurred: {str(e)}')
            return self.form_invalid(form)

class ResumePrintView(DetailView):
    model = Resume
    template_name = 'resumes/resume_print.html'
    context_object_name = 'resume'
    slug_field = 'pk'
    
    def get_queryset(self):
        # Get base queryset based on authentication
        if self.request.user.is_authenticated:
            queryset = Resume.objects.filter(user=self.request.user)
        else:
            # If not authenticated, allow access to any resume (useful for sharing)
            queryset = Resume.objects.all()
            
        # Prefetch all related data to avoid N+1 queries
        return queryset.prefetch_related(
            'educations',
            'experiences',
            'skills',
            'certifications',
            'languages'
        )
        
    slug_url_kwarg = 'pk'

    def get_object(self, queryset=None):
        # Get the resume by UUID from the URL
        resume_id = self.kwargs.get('pk')
        try:
            return get_object_or_404(Resume, id=resume_id)
        except (ValueError, Resume.DoesNotExist):
            raise Http404("Resume not found")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Resume - {self.object.full_name} - Print'
        return context

class ResumeDetailView(LoginRequiredMixin, DetailView):
    model = Resume
    template_name = 'resumes/resume_detail.html'
    context_object_name = 'resume'

    def get_queryset(self):
        # Only allow users to view their own resumes with prefetched related data
        return Resume.objects.filter(user=self.request.user).prefetch_related(
            'educations',
            'experiences',
            'skills',
            'certifications',
            'languages'
        )

    def get(self, request, *args, **kwargs):
        # Redirect to print view for preview
        if not request.GET.get('edit'):
            return redirect('resumes:resume_print', pk=kwargs['pk'])
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Edit: {self.object.full_name}"
        return context

class ResumeListView(ListView):
    model = Resume
    template_name = 'resumes/resume_list.html'
    context_object_name = 'resumes'
    paginate_by = 10

    def get_queryset(self):
        return Resume.objects.all().order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'My Resumes'
        return context

class ResumeDeleteView(DeleteView):
    model = Resume
    template_name = 'resumes/resume_confirm_delete.html'
    success_url = reverse_lazy('resumes:resume_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Resume deleted successfully!')
        return super().delete(request, *args, **kwargs)

@require_http_methods(["POST"])
@csrf_exempt
def delete_profile_picture(request, pk):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    
    if resume.profile_picture:
        # Delete the file from storage
        if os.path.isfile(resume.profile_picture.path):
            os.remove(resume.profile_picture.path)
        # Clear the field
        resume.profile_picture.delete(save=True)
    
    return JsonResponse({'success': True})

def create_resume(request):
    """Legacy view for creating a new resume"""
    return redirect('resumes:resume_create')
