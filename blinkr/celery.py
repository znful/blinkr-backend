import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "blinkr.settings")

app = Celery("blinkr")

# Read CELERY_* keys from Django's settings module (see blinkr/settings/base.py).
app.config_from_object("django.conf:settings", namespace="CELERY")

# Look for a tasks.py in every app listed in INSTALLED_APPS.
app.autodiscover_tasks()
