from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import transaction
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse

from .models import Product, Cart, CartItem, UserProfile


def get_or_create_cart(request):
    """Helper function to get or create a cart for the current user/session."""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        if not request.session.session_key:
            request.session.create()
        cart, created = Cart.objects.get_or_create(
            session_key=request.session.session_key,
            user=None
        )
    return cart


def cart_detail(request):
    """View to display the cart contents."""
    cart = get_or_create_cart(request)
    return render(request, 'pages/cart/detail.html', {'cart': cart})


@require_POST
def cart_add(request, product_id):
    """View to add a product to the cart or update its quantity."""
    try:
        product = Product.objects.get(id=product_id)
        
        # Get or create cart
        cart = get_or_create_cart(request)
        
        # Get quantity from form (default to 1 if not provided)
        quantity = int(request.POST.get('quantity', 1))
        
        # Check available stock
        available_stock = product.stock
        
        # Check if product is already in cart
        cart_item = None
        try:
            cart_item = CartItem.objects.get(cart=cart, product=product)
            # If item already in cart, calculate total requested quantity
            total_quantity = cart_item.quantity + quantity
            if total_quantity > available_stock:
                message = f"Only {available_stock} items available in stock. You already have {cart_item.quantity} in your cart."
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': message,
                        'stock_available': available_stock,
                        'in_cart': cart_item.quantity
                    }, status=400)
                messages.error(request, message)
                return redirect('ecom:product_detail', slug=product.slug)
                
            # Update quantity if item already exists in cart
            cart_item.quantity = total_quantity
            cart_item.save()
            
        except CartItem.DoesNotExist:
            # Check if requested quantity exceeds available stock
            if quantity > available_stock:
                message = f"Only {available_stock} items available in stock."
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': message,
                        'stock_available': available_stock,
                        'in_cart': 0
                    }, status=400)
                messages.error(request, message)
                return redirect('ecom:product_detail', slug=product.slug)
                
            # Create new cart item
            cart_item = CartItem.objects.create(
                cart=cart,
                product=product,
                quantity=quantity
            )
        
        # Update cart timestamp
        cart.updated_at = timezone.now()
        cart.save()
        
        # Prepare success message
        message = f"{product.name} added to your cart."
        
        # If this is an AJAX request, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': message,
                'cart_total_items': cart.total_items,
                'cart_total': str(cart.total)
            })
            
        # For non-AJAX requests, use messages and redirect
        messages.success(request, message)
        return redirect('ecom:cart_detail')
        
    except Product.DoesNotExist:
        error_msg = "Product not found."
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': error_msg}, status=404)
        messages.error(request, error_msg)
        return redirect('ecom:product_list')
    except Exception as e:
        error_msg = f"An error occurred: {str(e)}"
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': error_msg}, status=500)
        messages.error(request, error_msg)
        return redirect('ecom:product_list')


@require_POST
def cart_update(request, item_id):
    """View to update the quantity of a cart item."""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user if request.user.is_authenticated else None)
    quantity = int(request.POST.get('quantity', 1))
    
    if quantity < 1:
        cart_item.delete()
        messages.success(request, 'Item removed from cart')
    else:
        cart_item.quantity = quantity
        cart_item.save()
        messages.success(request, 'Cart updated successfully')
    
    return redirect('ecom:cart_detail')


@require_POST
def cart_remove(request, item_id):
    """View to remove an item from the cart."""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user if request.user.is_authenticated else None)
    product_name = cart_item.product.name
    cart_item.delete()
    messages.success(request, f'Removed {product_name} from your cart')
    return redirect('ecom:cart_detail')


def cart_count(request):
    """API endpoint to get the current cart item count."""
    cart = get_or_create_cart(request)
    return JsonResponse({
        'count': cart.total_items
    })


@login_required
def checkout(request):
    """View to handle the checkout process."""
    cart = get_or_create_cart(request)
    
    if not cart.items.exists():
        messages.warning(request, "Your cart is empty.")
        return redirect('ecom:cart_detail')
    
    # Get or create user profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Process the checkout form
        phone_number = request.POST.get('phone_number')
        address = request.POST.get('address')
        
        # Update profile if data was provided
        if phone_number or address:
            if phone_number:
                profile.phone_number = phone_number
            if address:
                profile.address = address
            profile.save()
        
        # In a real implementation, this would process the payment
        # For now, we'll just redirect to the order confirmation page
        return HttpResponseRedirect(reverse('ecom:checkout_payment_notice'))
    
    context = {
        'cart': cart,
        'profile': profile,
    }
    return render(request, 'pages/checkout/checkout.html', context)


@login_required
def checkout_payment_notice(request):
    """View to show payment notice after checkout attempt."""
    return render(request, 'pages/checkout/payment_notice.html')
