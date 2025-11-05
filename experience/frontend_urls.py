"""
Frontend URLs for experience app.
"""
from django.urls import path
from . import frontend_views

urlpatterns = [
    path('', frontend_views.experience_list, name='experience_list'),
    path('create/', frontend_views.experience_create, name='experience_create'),
    path('edit/', frontend_views.experience_edit, name='experience_edit'),
]
