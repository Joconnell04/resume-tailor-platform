"""
Maps app URLs
"""
from django.urls import path
from .views import IsochroneView, DistanceView, ApplicantMapView

urlpatterns = [
    path('isochrone/', IsochroneView.as_view(), name='isochrone'),
    path('distance/', DistanceView.as_view(), name='distance'),
    path('applicant-map/', ApplicantMapView.as_view(), name='applicant_map'),
]