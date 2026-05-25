import os
from celery import Celery

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')

# Load settings from django settings file, with CELERY_ namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Discover tasks automatically in all registered Django apps
app.autodiscover_tasks()
