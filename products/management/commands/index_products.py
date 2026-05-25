from django.core.management.base import BaseCommand
from products.models import Product
from products.search import index_product, get_meilisearch_client

class Command(BaseCommand):
    help = 'Indexes all existing products into Meilisearch'

    def handle(self, *args, **options):
        client = get_meilisearch_client()
        if not client:
            self.stdout.write(self.style.ERROR(
                "Meilisearch is unreachable or not configured. "
                "Ensure Meilisearch is running and configured correctly in settings."
            ))
            return
            
        products = Product.objects.all()
        count = 0
        for p in products:
            index_product(p)
            count += 1
            
        self.stdout.write(self.style.SUCCESS(f"Successfully indexed {count} products in Meilisearch."))
