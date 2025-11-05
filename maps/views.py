"""
Maps app views

API views for map-related functionality.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .services import MapboxIsochroneService


class IsochroneView(APIView):
    """
    Get isochrone data for a location.
    
    POST /api/maps/isochrone/
    
    Body:
    {
        "longitude": -84.388,
        "latitude": 33.749,
        "minutes": 30
    }
    """
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Get isochrone for given coordinates."""
        lon = request.data.get('longitude')
        lat = request.data.get('latitude')
        minutes = request.data.get('minutes', 15)
        
        if lon is None or lat is None:
            return Response(
                {'error': 'longitude and latitude are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            service = MapboxIsochroneService()
            result = service.get_isochrone(
                lon=float(lon),
                lat=float(lat),
                minutes=int(minutes)
            )
            return Response(result)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DistanceView(APIView):
    """
    Calculate distance between user location and job location.
    
    POST /api/maps/distance/
    
    Body:
    {
        "origin_longitude": -84.388,
        "origin_latitude": 33.749,
        "destination_longitude": -84.450,
        "destination_latitude": 33.780
    }
    """
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Calculate distance between two points."""
        origin_lon = request.data.get('origin_longitude')
        origin_lat = request.data.get('origin_latitude')
        dest_lon = request.data.get('destination_longitude')
        dest_lat = request.data.get('destination_latitude')
        
        if None in [origin_lon, origin_lat, dest_lon, dest_lat]:
            return Response(
                {'error': 'All coordinate fields are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            service = MapboxIsochroneService()
            result = service.calculate_distance(
                origin_lon=float(origin_lon),
                origin_lat=float(origin_lat),
                dest_lon=float(dest_lon),
                dest_lat=float(dest_lat)
            )
            return Response(result)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
