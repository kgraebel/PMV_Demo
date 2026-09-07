"""Fetches current outdoor temperature from Open-Meteo -- a free weather API
that needs no API key or account -- for use as the outside_temp_f input to
RoomMRTEstimator (mrt.py).
"""

from dataclasses import dataclass
from typing import Optional

import requests

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


class WeatherAPIError(RuntimeError):
    """Raised when the weather API can't be reached or returns unexpected data."""


@dataclass
class OutdoorConditions:
    temperature_f: float
    location_name: str
    latitude: float
    longitude: float


class OutdoorWeather:
    def __init__(
        self,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        location_name: Optional[str] = None,
    ):
        """Give either latitude/longitude directly, or a location_name to
        geocode (e.g. "Chicago, IL" or a ZIP code) -- geocoding also needs
        no API key.
        """
        if latitude is not None and longitude is not None:
            self.latitude = latitude
            self.longitude = longitude
            self.location_name = location_name or f"{latitude:.3f}, {longitude:.3f}"
            return

        if not location_name:
            raise ValueError("Provide either latitude/longitude or a location_name")

        self.latitude, self.longitude, resolved_name = self._geocode(location_name)
        self.location_name = resolved_name

    @staticmethod
    def _geocode(location_name: str):
        resp = requests.get(
            GEOCODING_URL,
            params={"name": location_name, "count": 1},
            timeout=10,
        )
        if resp.status_code != 200:
            raise WeatherAPIError(f"Geocoding request failed ({resp.status_code}): {resp.text}")

        results = resp.json().get("results")
        if not results:
            raise WeatherAPIError(f"No location found for {location_name!r}")

        match = results[0]
        parts = [match.get("name"), match.get("admin1"), match.get("country")]
        display_name = ", ".join(p for p in parts if p)
        return match["latitude"], match["longitude"], display_name

    def get_current_conditions(self) -> OutdoorConditions:
        resp = requests.get(
            FORECAST_URL,
            params={
                "latitude": self.latitude,
                "longitude": self.longitude,
                "current_weather": "true",
                "temperature_unit": "fahrenheit",
            },
            timeout=10,
        )
        if resp.status_code != 200:
            raise WeatherAPIError(f"Forecast request failed ({resp.status_code}): {resp.text}")

        payload = resp.json()
        current = payload.get("current_weather")
        if not current or "temperature" not in current:
            raise WeatherAPIError(f"Unexpected response from weather API: {payload}")

        return OutdoorConditions(
            temperature_f=current["temperature"],
            location_name=self.location_name,
            latitude=self.latitude,
            longitude=self.longitude,
        )
