import os

import requests


class MapboxRoutingProvider:
    def __init__(self):
        self.access_token = os.getenv("MAPBOX_ACCESS_TOKEN")

        if not self.access_token:
            raise RuntimeError(
                "MAPBOX_ACCESS_TOKEN is not configured"
            )

    def get_walking_route(
        self,
        origin_latitude: float,
        origin_longitude: float,
        destination_latitude: float,
        destination_longitude: float,
    ):
        coordinates = (
            f"{origin_longitude},{origin_latitude};"
            f"{destination_longitude},{destination_latitude}"
        )

        url = (
            "https://api.mapbox.com/directions/v5/"
            f"mapbox/walking/{coordinates}"
        )

        params = {
            "access_token": self.access_token,
            "geometries": "geojson",
        }

        response = requests.get(
            url,
            params=params,
            timeout=15,
        )

        if not response.ok:
            raise RuntimeError(
                f"Mapbox HTTP {response.status_code}: "
                f"{response.text}"
            )

        data = response.json()

        if data.get("code") != "Ok":
            raise RuntimeError(
                f"Mapbox routing error: {data}"
            )

        route = data["routes"][0]

        return {
            "distance": route["distance"],
            "duration": route["duration"],
            "geometry": route["geometry"],
        }

    def get_optimized_walking_route(
        self,
        points: list[tuple[float, float]],
    ):
        if len(points) < 2:
            raise ValueError(
                "At least 2 points are required"
            )

        coordinates = ";".join(
            f"{longitude},{latitude}"
            for latitude, longitude in points
        )

        url = (
            "https://api.mapbox.com/optimized-trips/v1/"
            f"mapbox/walking/{coordinates}"
        )

        params = {
            "access_token": self.access_token,
            "geometries": "geojson",
            "roundtrip": "true",
            "source": "first",
            "destination": "any",
        }

        response = requests.get(
            url,
            params=params,
            timeout=15,
        )

        if not response.ok:
            raise RuntimeError(
                f"Mapbox HTTP {response.status_code}: "
                f"{response.text}"
            )

        data = response.json()

        if data.get("code") != "Ok":
            raise RuntimeError(
                f"Mapbox routing error: {data}"
            )

        trip = data["trips"][0]

        return {
            "distance": trip["distance"],
            "duration": trip["duration"],
            "order": [
                waypoint["waypoint_index"]
                for waypoint in data["waypoints"]
            ],
            "geometry": trip["geometry"],
        }


mapbox_routing_provider = MapboxRoutingProvider()