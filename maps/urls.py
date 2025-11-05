"""
Maps app URLs
"""
from django.urls import path
from .views import IsochroneView, DistanceView

urlpatterns = [
    path('isochrone/', IsochroneView.as_view(), name='isochrone'),
    path('distance/', DistanceView.as_view(), name='distance'),
]
