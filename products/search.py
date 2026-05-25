import logging
from django.conf import settings

logger = logging.getLogger(__name__)

_client = None

def get_meilisearch_client():
    global _client
    if _client is not None:
        return _client
    
    host = getattr(settings, 'MEILISEARCH_HOST', 'http://127.0.0.1:7700')
    api_key = getattr(settings, 'MEILISEARCH_API_KEY', '')
    
    try:
        import meilisearch
        client = meilisearch.Client(host, api_key)
        # Verify connection by pinging health endpoint
        client.health()
        _client = client
        return _client
    except ImportError:
        logger.debug("meilisearch library is not installed.")
        return None
    except Exception as e:
        logger.warning("Meilisearch connection failed, falling back to database. Error: %s", e)
        return None


def get_or_create_index():
    client = get_meilisearch_client()
    if not client:
        return None
    try:
        index = client.index('products')
        # Check if index exists by fetching its primary key info
        index.get_primary_key()
        return index
    except Exception:
        try:
            # Create the index if it doesn't exist
            client.create_index('products', {'primaryKey': 'id'})
            index = client.index('products')
            # Set filterable attributes
            index.update_filterable_attributes(['available', 'category_id'])
            return index
        except Exception as e:
            logger.warning("Failed to create index 'products': %s", e)
            return None


def index_product(product):
    index = get_or_create_index()
    if not index:
        return
    try:
        doc = {
            'id': str(product.id),
            'name': product.name,
            'slug': product.slug,
            'description': product.description,
            'price': float(product.price),
            'available': product.available,
            'discount_percent': product.discount_percent,
            'category_id': product.category_id,
        }
        index.add_documents([doc])
    except Exception as e:
        logger.warning("Failed to index product %s: %s", product.id, e)


def remove_product(product_id):
    index = get_or_create_index()
    if not index:
        return
    try:
        index.delete_document(str(product_id))
    except Exception as e:
        logger.warning("Failed to delete product %s from index: %s", product_id, e)


def search_products_meili(query, category_id=None, limit=20):
    index = get_or_create_index()
    if not index:
        return None  # Signal fallback to database search
        
    try:
        search_filter = ['available = true']
        if category_id:
            search_filter.append(f'category_id = {category_id}')
            
        results = index.search(query, {
            'limit': limit,
            'filter': search_filter
        })
        
        hits = results.get('hits', [])
        return [int(hit['id']) for hit in hits]
    except Exception as e:
        logger.warning("Meilisearch query failed: %s", e)
        return None
