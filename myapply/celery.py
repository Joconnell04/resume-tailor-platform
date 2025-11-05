"""
Celery application configuration for the MyApply project.
"""
import os

from celery import Celery

# Set default Django settings module for Celery.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myapply.settings")

app = Celery("myapply")

# Load Celery config from Django settings, using the CELERY_ namespace.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks in installed apps.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    """
    Basic task for connectivity testing.
    """
    print(f"Debug task executed by Celery worker: {self.request!r}")
