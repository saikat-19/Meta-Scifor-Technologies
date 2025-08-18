from django.db import migrations


def add_category_methods(apps, schema_editor):
    """Add methods to the Category model."""
    Category = apps.get_model('ecom', 'Category')
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('ecom:product_list') + f'?category={self.slug}'
    
    def products_count(self):
        if hasattr(self, '_products_count'):
            return self._products_count
        return self.products.count()
    
    # Add the methods to the Category model
    Category.get_absolute_url = get_absolute_url
    Category.products_count = property(products_count)


class Migration(migrations.Migration):
    dependencies = [
        ('ecom', '0008_category_icon_category_is_featured_alter_product_sku'),
    ]

    operations = [
        migrations.RunPython(add_category_methods, reverse_code=migrations.RunPython.noop),
    ]
