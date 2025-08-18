from django.urls import path
from . import cart_views

app_name = 'cart'

urlpatterns = [
    path('', cart_views.cart_detail, name='cart_detail'),
    path('add/<int:product_id>/', cart_views.cart_add, name='cart_add'),
    path('update/<int:item_id>/', cart_views.cart_update, name='cart_update'),
    path('remove/<int:item_id>/', cart_views.cart_remove, name='cart_remove'),
    path('api/count/', cart_views.cart_count, name='cart_count'),
]
