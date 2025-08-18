from .cart_views import get_or_create_cart

def cart(request):
    """
    Context processor that makes the cart available to all templates.
    """
    if request.path.startswith('/admin/'):
        return {}
        
    return {
        'cart': get_or_create_cart(request)
    }
