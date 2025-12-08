import os
import json
from django.shortcuts import render
from django.views import View
from jobs.models import JobPosting
from .services import MapboxIsochroneService

# Django REST Framework imports
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
import requests

# ==========================
# API: Isochrone
# ==========================
class IsochroneView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        lon = request.data.get("longitude")
        lat = request.data.get("latitude")
        minutes = request.data.get("minutes", 15)

        if lon is None or lat is None:
            return Response(
                {"error": "longitude and latitude are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        service = MapboxIsochroneService()
        try:
            result = service.get_isochrone(float(lon), float(lat), int(minutes))
            return Response(result)
        except Exception as e:
            return Response({"error": str(e)}, status=500)


# ==========================
# API: Distance
# ==========================
class DistanceView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        origin_lon = request.data.get("origin_longitude")
        origin_lat = request.data.get("origin_latitude")
        dest_lon = request.data.get("destination_longitude")
        dest_lat = request.data.get("destination_latitude")

        if None in [origin_lon, origin_lat, dest_lon, dest_lat]:
            return Response(
                {"error": "All coordinate fields are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        service = MapboxIsochroneService()
        try:
            # Also get route geometry for display
            route_data = service.calculate_distance(
                float(origin_lon),
                float(origin_lat),
                float(dest_lon),
                float(dest_lat),
            )

            # Request the route geometry from Mapbox Directions API
            directions_url = (
                f"https://api.mapbox.com/directions/v5/mapbox/driving/"
                f"{origin_lon},{origin_lat};{dest_lon},{dest_lat}"
            )
            params = {
                "access_token": service.token,
                "geometries": "geojson"
            }
            response = requests.get(directions_url, params=params)
            directions = response.json()
            geometry = directions.get("routes", [{}])[0].get("geometry", {})

            route_data["geometry"] = geometry
            return Response(route_data)
        except Exception as e:
            return Response({"error": str(e)}, status=500)


# ==========================
# Helper: Geocode a location string
# ==========================
def geocode_location(service, location_text: str):
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{location_text}.json"
    params = {"access_token": service.token, "limit": 1}
    response = requests.get(url, params=params)
    data = response.json()
    if "features" not in data or not data["features"]:
        return None
    coords = data["features"][0]["geometry"]["coordinates"]
    return {
        "longitude": coords[0],
        "latitude": coords[1],
        "place_name": data["features"][0]["place_name"],
    }


# ==========================
# Applicant Map Page
# ==========================
class ApplicantMapView(View):
    def get(self, request):
        service = MapboxIsochroneService()
        jobs = JobPosting.objects.filter(user=request.user)
        job_points = []

        for job in jobs:
            if job.location_text:
                geo = geocode_location(service, job.location_text)
                if geo:
                    job_points.append({
                        "title": job.title,
                        "location_text": job.location_text,
                        "longitude": geo["longitude"],
                        "latitude": geo["latitude"],
                    })

        # Default center
        if job_points:
            default_center = [job_points[0]["longitude"], job_points[0]["latitude"]]
        else:
            default_center = [-98.5795, 39.8283]  # USA center fallback

        # Ensure token is available
        mapbox_token = os.environ.get("MAPBOX_TOKEN")
        if not mapbox_token:
            raise ValueError("MAPBOX_TOKEN not set in environment variables")

        return render(request, "maps/applicant_map.html", {
            "job_points_json": json.dumps(job_points),
            "MAPBOX_TOKEN": mapbox_token,
            "default_center": json.dumps(default_center),
        })
