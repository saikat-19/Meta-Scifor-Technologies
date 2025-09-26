from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout, get_backends
from django.contrib.auth.views import LoginView as BaseLoginView
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.views.generic import (
    CreateView, UpdateView, DeleteView, DetailView, ListView, 
    TemplateView, FormView, View
)
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse, Http404
from django.db.models import Sum, F, Q
from django.views.generic.edit import FormMixin
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction
from django.contrib.auth.forms import AuthenticationForm
from django.utils import timezone
from datetime import timedelta
from typing import Any, Dict, List

from .models import Invoice, InvoiceItem, UserProfile, Client, User
from .forms import InvoiceForm, InvoiceItemForm, InvoiceItemFormSet, CustomUserCreationForm, UserProfileForm, ClientForm
from .auth_views import LoginView, VerifyEmailView, resend_verification_email

def home(request: Any) -> Any:
    context = {
        'title': 'BillMate - Easy Invoicing Solution',
        'welcome_message': 'Welcome to BillMate',
        'description': 'Create professional invoices in minutes with our easy-to-use invoicing platform.'
    }
    return render(request, 'home.html', context)

# Using the custom LoginView from auth_views.py

def logout_view(request: Any) -> Any:
    # Clear any pending messages before logout
    storage = messages.get_messages(request)
    for _ in storage:
        pass  # This clears the messages
    
    logout(request)
    # Don't add a success message to prevent it from persisting
    return redirect('login')

@login_required(login_url='/accounts/login/')
def dashboard_view(request: Any) -> Any:
    # Check if user needs to verify their email
    if hasattr(request.user, 'email_verified') and not request.user.email_verified:
        messages.warning(
            request,
            'Please verify your email address to access all features. '
            'Check your email for the verification link or '
            '<a href=\"{}\" class=\"font-medium text-blue-600 hover:text-blue-500\">click here to resend</a>.'.format(
                reverse('invoice_app:resend_verification')
            ),
            extra_tags='safe'
        )
    
    try:
        # Get recent invoices for the logged-in user
        recent_invoices: List[Invoice] = list(Invoice.objects.filter(created_by=request.user).order_by('-created_at')[:5])  # type: ignore[attr-defined]
        
        # Calculate statistics
        total_invoices: int = Invoice.objects.filter(created_by=request.user).count()  # type: ignore[attr-defined]
        total_paid: float = sum(invoice.total for invoice in Invoice.objects.filter(created_by=request.user, status='paid'))  # type: ignore[attr-defined]
        total_pending: float = sum(invoice.total for invoice in Invoice.objects.filter(created_by=request.user, status='sent'))  # type: ignore[attr-defined]
        total_overdue: float = sum(invoice.total for invoice in Invoice.objects.filter(created_by=request.user, status='overdue'))  # type: ignore[attr-defined]
        
        context = {
            'title': 'Dashboard',
            'active_page': 'dashboard',
            'recent_invoices': recent_invoices,
            'use_humanize': True,  # Add this flag to indicate we want to use humanize
            'email_verified': getattr(request.user, 'email_verified', True),
            'stats': {
                'total_invoices': total_invoices or 0,
                'total_paid': total_paid or 0,
                'total_pending': total_pending or 0,
                'total_overdue': total_overdue or 0,
            },
        }
        return render(request, 'dashboard/home.html', context)
    except Exception as e:
        print(f"Error in dashboard_view: {str(e)}")
        # Return a simple response if there's an error
        context = {
            'title': 'Dashboard',
            'active_page': 'dashboard',
            'recent_invoices': [],
            'use_humanize': True,
            'email_verified': getattr(request.user, 'email_verified', True) if hasattr(request, 'user') else True,
            'stats': {
                'total_invoices': 0,
                'total_paid': 0,
                'total_pending': 0,
                'total_overdue': 0,
            },
        }
        return render(request, 'dashboard/home.html', context)

@login_required
def invoice_list(request: Any) -> Any:
    """List all invoices for the logged-in user"""
    invoices = Invoice.objects.filter(created_by=request.user).order_by('-issue_date')  # type: ignore[attr-defined]
    return render(request, 'dashboard/invoice_list.html', {'invoices': invoices})

@login_required
def invoice_detail(request: Any, pk: int) -> Any:
    """View details of a specific invoice"""
    invoice = get_object_or_404(Invoice, pk=pk, created_by=request.user)
    
    # Get or create user profile for invoice company information
    try:
        profile = UserProfile.objects.get(user=request.user)  # type: ignore[attr-defined]
    except UserProfile.DoesNotExist:  # type: ignore[attr-defined]
        profile = UserProfile.objects.create(user=request.user)  # type: ignore[attr-defined]
    
    return render(request, 'dashboard/invoice_detail.html', {
        'invoice': invoice,
        'profile': profile
    })

@login_required
def invoice_create(request: Any) -> Any:
    """Create a new invoice"""
    if request.method == 'POST':
        form = InvoiceForm(request.POST, user=request.user)
        formset = InvoiceItemFormSet(request.POST, instance=Invoice())
        
        # Check if we have at least one valid item
        has_valid_items = False
        if formset.is_valid():
            for item_form in formset:
                if item_form.cleaned_data and not item_form.cleaned_data.get('DELETE', False):
                    has_valid_items = True
                    break
        
        if form.is_valid() and formset.is_valid() and has_valid_items:
            with transaction.atomic():  # type: ignore[attr-defined]
                invoice = form.save(commit=False)
                invoice.created_by = request.user
                invoice.save()
                formset.instance = invoice
                formset.save()
                
                # Update invoice totals
                invoice.update_totals()
                
            messages.success(request, 'Invoice created successfully!')
            return redirect('invoice_app:invoice_detail', pk=invoice.pk)
        else:
            # Log validation errors for debugging
            if not form.is_valid():
                print("Form errors:", form.errors)
            if not formset.is_valid():
                print("Formset errors:", formset.errors)
                print("Formset non_form_errors:", formset.non_form_errors())
            if not has_valid_items:
                messages.error(request, 'Please add at least one invoice item.')
                print("No valid items found")
    else:
        form = InvoiceForm(user=request.user)
        formset = InvoiceItemFormSet(instance=Invoice())
    
    return render(request, 'dashboard/invoice_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Create New Invoice',
        'submit_btn': 'Create Invoice'
    })

@login_required
def invoice_update(request: Any, pk: int) -> Any:
    """Update an existing invoice"""
    invoice = get_object_or_404(Invoice, pk=pk, created_by=request.user)
    
    if request.method == 'POST':
        form = InvoiceForm(request.POST, instance=invoice, user=request.user)
        formset = InvoiceItemFormSet(request.POST, instance=invoice)
        
        # Enhanced validation for updates
        has_valid_items = False
        formset_should_be_saved = False
        
        # For updates, we need to be more careful about validation
        existing_items_count = invoice.items.count()
        
        # First, let's manually validate the formset by checking each form
        valid_forms = []
        forms_with_data = []
        delete_count = 0
        
        for item_form in formset.forms:
            # Check if this form has any data
            form_prefix = item_form.prefix
            description = formset.data.get(f'{form_prefix}-description', '').strip()
            quantity = formset.data.get(f'{form_prefix}-quantity', '').strip()
            unit_price = formset.data.get(f'{form_prefix}-unit_price', '').strip()
            delete_flag = formset.data.get(f'{form_prefix}-DELETE', False)
            
            # If form is marked for deletion
            if delete_flag:
                delete_count += 1
                continue
                
            # If form has any data, it needs to be complete
            if description or quantity or unit_price:
                forms_with_data.append(item_form)
                # Validate this specific form
                if description and quantity and unit_price:
                    try:
                        # Try to convert to ensure valid data
                        float(quantity)
                        float(unit_price)
                        valid_forms.append(item_form)
                    except (ValueError, TypeError):
                        pass  # Invalid data, don't add to valid forms
        
        # Calculate total valid items after update
        total_items_after_update = existing_items_count - delete_count + len(valid_forms)
        
        # For updates, we allow saving if:
        # 1. No new data was added (status-only update)
        # 2. New valid data was added
        if len(forms_with_data) == 0:
            # No new data added - status-only update
            has_valid_items = existing_items_count > delete_count
            formset_should_be_saved = delete_count > 0  # Only save if there are deletions
        elif len(valid_forms) == len(forms_with_data):
            # All forms with data are valid
            has_valid_items = total_items_after_update > 0
            formset_should_be_saved = True
        else:
            # Some forms with data are invalid
            has_valid_items = False
            formset_should_be_saved = False
        
        if form.is_valid() and has_valid_items:
            with transaction.atomic():  # type: ignore[attr-defined]
                form.save()
                
                # Handle formset saving based on our validation
                if formset_should_be_saved:
                    if len(forms_with_data) == 0 and delete_count > 0:
                        # Only deletions - process deletions manually
                        for item_form in formset.forms:
                            form_prefix = item_form.prefix
                            delete_flag = formset.data.get(f'{form_prefix}-DELETE', False)
                            if delete_flag and item_form.instance.pk:
                                item_form.instance.delete()
                    else:
                        # We have valid new data - use the normal formset save
                        # But first, create a custom formset with only valid forms
                        for item_form in formset.forms:
                            form_prefix = item_form.prefix
                            description = formset.data.get(f'{form_prefix}-description', '').strip()
                            quantity = formset.data.get(f'{form_prefix}-quantity', '').strip()
                            unit_price = formset.data.get(f'{form_prefix}-unit_price', '').strip()
                            delete_flag = formset.data.get(f'{form_prefix}-DELETE', False)
                            
                            # Skip empty forms and deleted forms
                            if not (description or quantity or unit_price) and not delete_flag:
                                continue
                                
                            # Process deletion
                            if delete_flag and item_form.instance.pk:
                                item_form.instance.delete()
                                continue
                                
                            # Process new/updated items
                            if description and quantity and unit_price:
                                if item_form.instance.pk:
                                    # Update existing item
                                    item_form.instance.description = description
                                    item_form.instance.quantity = int(quantity)
                                    item_form.instance.unit_price = float(unit_price)
                                    item_form.instance.save()
                                else:
                                    # Create new item
                                    InvoiceItem.objects.create(  # type: ignore[attr-defined]
                                        invoice=invoice,
                                        description=description,
                                        quantity=int(quantity),
                                        unit_price=float(unit_price)
                                    )
                
                invoice.update_totals()
                
            messages.success(request, 'Invoice updated successfully!')
            return redirect('invoice_app:invoice_detail', pk=invoice.pk)
        else:
            # Log validation errors for debugging
            if not form.is_valid():
                print("Form errors:", form.errors)
            if not has_valid_items:
                if len(forms_with_data) > len(valid_forms):
                    messages.error(request, 'Please complete all item fields (description, quantity, and price).')
                    print(f"Invalid forms found: {len(forms_with_data) - len(valid_forms)} forms have incomplete data")
                else:
                    messages.error(request, 'Please add at least one invoice item.')
                    print("No valid items found")
    else:
        form = InvoiceForm(instance=invoice, user=request.user)
        formset = InvoiceItemFormSet(instance=invoice)
    
    return render(request, 'dashboard/invoice_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Update Invoice',
        'submit_btn': 'Update Invoice',
        'invoice': invoice
    })

@login_required
def invoice_detail(request: Any, pk: int):
    """View details of a specific invoice"""
    invoice = get_object_or_404(Invoice, pk=pk, created_by=request.user)
    items = invoice.items.all()
    
    context = {
        'invoice': invoice,
        'items': items,
        'title': f'Invoice #{invoice.invoice_number}'
    }
    return render(request, 'dashboard/invoice_detail.html', context)


def public_invoice_view(request, token):
    """View for public access to invoices using a secure token"""
    try:
        invoice = Invoice.objects.get(view_token=token)
    except Invoice.DoesNotExist:
        raise Http404("Invoice not found or access denied")

    # Get all items for the invoice
    items = invoice.items.all()
    
    # Get company information
    company = invoice.created_by.profile if hasattr(invoice.created_by, 'profile') else None
    company_name = getattr(company, 'company_name', 'BillMate')
    
    context = {
        'invoice': invoice,
        'items': items,
        'company': company,
        'company_name': company_name,
        'title': f'Invoice #{invoice.invoice_number}',
        'is_public': True  # Add flag to indicate public view
    }
    return render(request, 'dashboard/public_invoice.html', context)


def static_page_view(request, template_name):
    """
    View for rendering static pages.
    Valid templates are: 'about', 'privacy', 'terms'
    """
    valid_templates = ['about', 'privacy', 'terms']
    if template_name not in valid_templates:
        raise Http404("Page not found")
    
    return render(request, f'pages/{template_name}.html')

def register_view(request: Any) -> Any:
    if request.user.is_authenticated:
        return redirect('invoice_app:dashboard')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = form.save(commit=False)
                user.is_active = True
                user.save()
                
                # Create user profile
                UserProfile.objects.get_or_create(user=user)
                
                # Send verification email
                try:
                    user.send_verification_email()
                    if settings.DEBUG:
                        print("\n" + "="*80)
                        print("  VERIFICATION EMAIL SENT (check console for details)")
                        print(f"  User: {user.email}")
                        print(f"  Token: {user.verification_token}")
                        print("  In production, this would be sent via email")
                        print("="*80 + "\n")
                    
                    messages.success(
                        request,
                        'Registration successful! Please check your email to verify your account. '
                        'You must verify your email before you can log in.'
                    )
                    # Redirect to login page instead of dashboard
                    return redirect('login')
                    
                except Exception as e:
                    # Log the error but don't fail the registration
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Failed to send verification email: {e}")
                    
                    # Generate a new token for manual verification
                    user.generate_verification_token()
                    
                    if settings.DEBUG:
                        print("\n" + "!"*80)
                        print(f"  ERROR SENDING VERIFICATION EMAIL: {e}")
                        print(f"  User: {user.email}")
                        print(f"  Manual verification URL: /verify-email/{user.id}/{user.verification_token}/")
                        print("!"*80 + "\n")
                    
                    messages.warning(
                        request,
                        'Registration successful, but we were unable to send a verification email. '
                        'Please try logging in to request a new verification email.'
                    )
                    return redirect('login')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'registration/register.html', {
        'form': form,
        'title': 'Create an Account',
    })

def get_invoice_items(request: Any, invoice_id: int) -> JsonResponse:
    """API endpoint to get items for a specific invoice"""
    try:
        invoice = Invoice.objects.get(pk=invoice_id, created_by=request.user)  # type: ignore[attr-defined]
        items = invoice.items.values('id', 'description', 'quantity', 'unit_price', 'amount')
        return JsonResponse(list(items), safe=False)
    except Invoice.DoesNotExist:  # type: ignore[attr-defined]
        return JsonResponse({'error': 'Invoice not found'}, status=404)


@login_required
def user_profile(request: Any) -> Any:
    """View and update user profile/company information"""
    try:
        # Get or create user profile
        profile = UserProfile.objects.get(user=request.user)  # type: ignore[attr-defined]
    except UserProfile.DoesNotExist:  # type: ignore[attr-defined]
        profile = UserProfile.objects.create(user=request.user)  # type: ignore[attr-defined]
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Company information updated successfully!')
            return redirect('invoice_app:user_profile')
    else:
        form = UserProfileForm(instance=profile)
    
    return render(request, 'dashboard/user_profile.html', {
        'form': form,
        'profile': profile,
        'title': 'My Information'
    })


# Client Management Views
@login_required
def client_list(request: Any) -> Any:
    """List all clients for the logged-in user"""
    clients = Client.objects.filter(created_by=request.user).order_by('name')  # type: ignore[attr-defined]
    return render(request, 'dashboard/client_list.html', {
        'clients': clients,
        'title': 'Clients'
    })


@login_required
def client_create(request: Any) -> Any:
    """Create a new client"""
    if request.method == 'POST':
        form = ClientForm(request.POST, user=request.user)
        if form.is_valid():
            client = form.save()
            messages.success(request, 'Client created successfully!')
            return redirect('invoice_app:client_detail', pk=client.pk)
    else:
        form = ClientForm(user=request.user)
    
    return render(request, 'dashboard/client_form.html', {
        'form': form,
        'title': 'Add New Client',
        'submit_btn': 'Create Client'
    })


@login_required
def client_detail(request: Any, pk: int) -> Any:
    """View details of a specific client"""
    client = get_object_or_404(Client, pk=pk, created_by=request.user)
    
    # Get recent invoices for this client
    recent_invoices = Invoice.objects.filter(  # type: ignore[attr-defined]
        created_by=request.user,
        client=client
    ).order_by('-created_at')[:5]
    
    return render(request, 'dashboard/client_detail.html', {
        'client': client,
        'recent_invoices': recent_invoices,
        'title': f'Client: {client.name}'
    })


@login_required
def client_update(request: Any, pk: int) -> Any:
    """Update an existing client"""
    client = get_object_or_404(Client, pk=pk, created_by=request.user)
    
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Client updated successfully!')
            return redirect('invoice_app:client_detail', pk=client.pk)
    else:
        form = ClientForm(instance=client, user=request.user)
    
    return render(request, 'dashboard/client_form.html', {
        'form': form,
        'title': f'Edit Client: {client.name}',
        'submit_btn': 'Update Client',
        'client': client
    })


@login_required
def client_delete(request: Any, pk: int) -> Any:
    """Delete a client"""
    client = get_object_or_404(Client, pk=pk, created_by=request.user)
    
    if request.method == 'POST':
        client.delete()
        messages.success(request, 'Client deleted successfully!')
        return redirect('invoice_app:client_list')
    
    return render(request, 'dashboard/client_confirm_delete.html', {
        'client': client,
        'title': f'Delete Client: {client.name}'
    })


@login_required
def get_client_data(request: Any, pk: int) -> JsonResponse:
    """API endpoint to get client data for auto-population"""
    try:
        client = Client.objects.get(pk=pk, created_by=request.user)  # type: ignore[attr-defined]
        data = {
            'id': client.pk,
            'name': client.name,
            'email': client.email,
            'phone': client.phone,
            'address': client.address,
            'city': client.city,
            'state': client.state,
            'postal_code': client.postal_code,
            'country': client.country,
            'website': client.website
        }
        return JsonResponse(data)
    except Client.DoesNotExist:  # type: ignore[attr-defined]
        return JsonResponse({'error': 'Client not found'}, status=404)


@login_required
def send_invoice_email(request: Any, pk: int) -> Any:
    """Send invoice via email to the client"""
    invoice = get_object_or_404(Invoice, pk=pk, created_by=request.user)
    
    if request.method == 'POST':
        success, error = invoice.send_email(request)
        if success:
            messages.success(request, f'Invoice #{invoice.invoice_number} has been sent to {invoice.client_email}')
        else:
            messages.error(request, f'Failed to send invoice: {error}')
    
    return redirect('invoice_app:invoice_detail', pk=invoice.pk)


@login_required
def invoice_delete(request: Any, pk: int) -> Any:
    """Delete an invoice"""
    invoice = get_object_or_404(Invoice, pk=pk, created_by=request.user)
    
    if request.method == 'POST':
        invoice_number = invoice.invoice_number
        invoice.delete()
        messages.success(request, f'Invoice #{invoice_number} has been deleted successfully.')
        return redirect('invoice_app:invoice_list')
    
    # GET request - show confirmation page
    context = {
        'invoice': invoice,
        'title': f'Delete Invoice #{invoice.invoice_number}'
    }
    return render(request, 'dashboard/confirm_delete.html', context)
