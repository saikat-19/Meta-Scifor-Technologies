from django.core.management.base import BaseCommand
from ecom.models import Category

class Command(BaseCommand):
    help = 'Create sample categories for the e-commerce site'

    def handle(self, *args, **options):
        categories = [
            'Electronics',
            'Clothing',
            'Home & Kitchen',
            'Beauty & Personal Care',
            'Books',
            'Sports & Outdoors',
            'Toys & Games',
            'Health & Household',
            'Automotive',
            'Tools & Home Improvement'
        ]

        created_count = 0
        for name in categories:
            category, created = Category.objects.get_or_create(
                name=name,
                defaults={
                    'slug': name.lower().replace(' ', '-').replace('&', 'and'),
                    'is_active': True
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created category: {name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Category already exists: {name}'))

        self.stdout.write(self.style.SUCCESS(f'Successfully created {created_count} categories'))
