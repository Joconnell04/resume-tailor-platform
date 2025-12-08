"""
Maps app services

Mapbox Isochrone service for calculating travel time/distance.
"""
import os
import requests


class MapboxIsochroneService:
    BASE_ISOCHRONE_URL = "https://api.mapbox.com/isochrone/v1/mapbox/driving"
    BASE_DIRECTIONS_URL = "https://api.mapbox.com/directions/v5/mapbox/driving"

    def __init__(self):
        self.token = os.environ.get("MAPBOX_TOKEN", "")
        if not self.token:
            raise ValueError("MAPBOX_TOKEN not set in environment variables")

    # -----------------------------
    # ISOCHRONE REQUEST
    # -----------------------------
    def get_isochrone(self, lon: float, lat: float, minutes: int = 15) -> dict:
        url = f"{self.BASE_ISOCHRONE_URL}/{lon},{lat}"
        params = {
            "contours_minutes": minutes,
            "polygons": "true",
            "access_token": self.token
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            geometry = data.get("features", [{}])[0]
        except Exception as e:
            geometry = {}
        
        return {
            "center": [lon, lat],
            "minutes": minutes,
            "geometry": geometry
        }

    # -----------------------------
    # DISTANCE CALCULATION
    # -----------------------------
    def calculate_distance(
        self,
        origin_lon: float,
        origin_lat: float,
        dest_lon: float,
        dest_lat: float
    ) -> dict:
        coordinates = f"{origin_lon},{origin_lat};{dest_lon},{dest_lat}"
        url = f"{self.BASE_DIRECTIONS_URL}/{coordinates}"
        params = {
            "access_token": self.token,
            "geometries": "geojson"
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            route = data.get("routes", [{}])[0]
            distance_km = route.get("distance", 0) / 1000
            duration_minutes = route.get("duration", 0) / 60
        except Exception as e:
            distance_km = 0
            duration_minutes = 0

        return {
            "distance_km": round(distance_km, 2),
            "duration_minutes": round(duration_minutes, 2)
        }

    # -----------------------------
    # GEOCODING
    # -----------------------------
    def geocode_location(self, location_text: str) -> dict | None:
        url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{location_text}.json"
        params = {
            "access_token": self.token,
            "limit": 1
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            features = data.get("features", [])
            if not features:
                return None
            coords = features[0]["geometry"]["coordinates"]
            return {
                "longitude": coords[0],
                "latitude": coords[1],
                "place_name": features[0]["place_name"]
            }
        except Exception:
            return None
