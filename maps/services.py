"""
Maps app services

Mapbox Isochrone service for calculating travel time/distance.
"""
import os
import requests


class MapboxIsochroneService:
    """
    Service for Mapbox Isochrone API.
    
    Calculates reachable areas within a given travel time from a location.
    Useful for determining if a job is within commuting distance.
    
    TODO: Implement actual Mapbox API integration
    - Set up Mapbox client with API token
    - Implement coordinate geocoding if needed
    - Make actual API calls to Mapbox Isochrone endpoint
    - Parse and return isochrone geometry
    - Calculate distance between two points
    """
    
    BASE_URL = "https://api.mapbox.com/isochrone/v1/mapbox/driving"
    
    def __init__(self):
        """Initialize service with API configuration."""
        self.token = os.environ.get('MAPBOX_TOKEN', '')
        if not self.token:
            print("Warning: MAPBOX_TOKEN not set. Map features will not work.")
    
    def get_isochrone(self, lon: float, lat: float, minutes: int = 15) -> dict:
        """
        Get isochrone data for a location.
        
        An isochrone represents the area reachable within a given time.
        
        Args:
            lon: Longitude of the starting point
            lat: Latitude of the starting point
            minutes: Travel time in minutes (default: 15)
        
        Returns:
            dict with isochrone data:
                - center: [lon, lat]
                - minutes: travel time
                - geometry: GeoJSON geometry (to be implemented)
        
        TODO: Implement actual API call
        Example API call:
        GET https://api.mapbox.com/isochrone/v1/mapbox/driving/{lon},{lat}
            ?contours_minutes={minutes}
            &access_token={token}
        """
        # Placeholder return
        return {
            "center": [lon, lat],
            "minutes": minutes,
            "geometry": {},
            "note": "Mapbox integration not yet implemented"
        }
    
    def calculate_distance(
        self,
        origin_lon: float,
        origin_lat: float,
        dest_lon: float,
        dest_lat: float
    ) -> dict:
        """
        Calculate distance/travel time between two points.
        
        Args:
            origin_lon: Origin longitude
            origin_lat: Origin latitude
            dest_lon: Destination longitude
            dest_lat: Destination latitude
        
        Returns:
            dict with:
                - distance_km: Distance in kilometers
                - duration_minutes: Estimated travel time
        
        TODO: Implement using Mapbox Directions API
        """
        # Placeholder return
        return {
            "distance_km": 0,
            "duration_minutes": 0,
            "note": "Distance calculation not yet implemented"
        }
