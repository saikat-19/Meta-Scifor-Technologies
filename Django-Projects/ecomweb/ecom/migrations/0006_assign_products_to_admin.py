from django.db import migrations
from django.contrib.auth import get_user_model

def assign_products_to_admin(apps, schema_editor):
    Product = apps.get_model('ecom', 'Product')
    User = get_user_model()
    
    # Get the first superuser (admin)
    admin = User.objects.filter(is_superuser=True).first()
    
    if admin:
        # Assign all products without a seller to the admin
        Product.objects.filter(seller__isnull=True).update(seller=admin)

def reverse_assign_products(apps, schema_editor):
    # This is a data migration, so we don't need to reverse it
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('ecom', '0005_product_seller'),
    ]

    operations = [
        migrations.RunPython(assign_products_to_admin, reverse_assign_products),
    ]
