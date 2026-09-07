"""Client for Google's Smart Device Management (SDM) API — reads room
temperature and humidity from a Nest thermostat.

Credentials are never hardcoded here. Provide them via environment
variables (see .env.example) or constructor arguments:

    NEST_PROJECT_ID      SDM "Device Access" project ID
    NEST_CLIENT_ID       OAuth client ID
    NEST_CLIENT_SECRET   OAuth client secret
    NEST_REFRESH_TOKEN   OAuth refresh token (from the one-time consent flow)
    NEST_DEVICE_ID       Thermostat device ID (see list_devices() to find it)
"""

import os
import time
from dataclasses import dataclass
from typing import Optional

import requests

TOKEN_URL = "https://oauth2.googleapis.com/token"
SDM_BASE_URL = "https://smartdevicemanagement.googleapis.com/v1"

TEMPERATURE_TRAIT = "sdm.devices.traits.Temperature"
HUMIDITY_TRAIT = "sdm.devices.traits.Humidity"
INFO_TRAIT = "sdm.devices.traits.Info"


class NestAPIError(RuntimeError):
    """Raised when the SDM API rejects a request or returns unexpected data."""


@dataclass
class RoomConditions:
    air_temperature_c: float
    relative_humidity_pct: float
    device_id: str
    room_name: Optional[str] = None


@dataclass
class NestDevice:
    device_id: str
    display_name: Optional[str]
    room_name: Optional[str]


class NestThermostat:
    def __init__(
        self,
        project_id: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        refresh_token: Optional[str] = None,
        device_id: Optional[str] = None,
    ):
        self.project_id = project_id or os.environ.get("NEST_PROJECT_ID")
        self.client_id = client_id or os.environ.get("NEST_CLIENT_ID")
        self.client_secret = client_secret or os.environ.get("NEST_CLIENT_SECRET")
        self.refresh_token = refresh_token or os.environ.get("NEST_REFRESH_TOKEN")
        self.device_id = device_id or os.environ.get("NEST_DEVICE_ID")

        missing = [
            name
            for name, val in [
                ("NEST_PROJECT_ID", self.project_id),
                ("NEST_CLIENT_ID", self.client_id),
                ("NEST_CLIENT_SECRET", self.client_secret),
                ("NEST_REFRESH_TOKEN", self.refresh_token),
            ]
            if not val
        ]
        if missing:
            raise NestAPIError(f"Missing Nest credentials: {', '.join(missing)}")

        self._access_token = None
        self._token_expires_at = 0.0

    def _access_token_valid(self) -> str:
        if self._access_token and time.time() < self._token_expires_at - 30:
            return self._access_token

        resp = requests.post(
            TOKEN_URL,
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": self.refresh_token,
                "grant_type": "refresh_token",
            },
            timeout=10,
        )
        if resp.status_code != 200:
            raise NestAPIError(f"Token refresh failed ({resp.status_code}): {resp.text}")

        payload = resp.json()
        self._access_token = payload["access_token"]
        self._token_expires_at = time.time() + payload.get("expires_in", 3600)
        return self._access_token

    def _get(self, path: str) -> dict:
        token = self._access_token_valid()
        resp = requests.get(
            f"{SDM_BASE_URL}/{path}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if resp.status_code != 200:
            raise NestAPIError(f"SDM API request failed ({resp.status_code}): {resp.text}")
        return resp.json()

    def list_devices(self) -> list:
        """List every device on this Device Access project, for finding a device_id."""
        payload = self._get(f"enterprises/{self.project_id}/devices")
        devices = []
        for d in payload.get("devices", []):
            traits = d.get("traits", {})
            room_name = None
            for relation in d.get("parentRelations", []):
                room_name = relation.get("displayName")
                break
            devices.append(
                NestDevice(
                    device_id=d["name"].rsplit("/", 1)[-1],
                    display_name=traits.get(INFO_TRAIT, {}).get("customName"),
                    room_name=room_name,
                )
            )
        return devices

    def get_room_conditions(self, device_id: Optional[str] = None) -> RoomConditions:
        """Fetch current air temperature and relative humidity for one thermostat."""
        target_id = device_id or self.device_id
        if not target_id:
            raise NestAPIError(
                "No device_id given and NEST_DEVICE_ID is not set. "
                "Call list_devices() to find one."
            )

        payload = self._get(f"enterprises/{self.project_id}/devices/{target_id}")
        traits = payload.get("traits", {})

        if TEMPERATURE_TRAIT not in traits or HUMIDITY_TRAIT not in traits:
            raise NestAPIError(
                f"Device {target_id} does not report temperature/humidity traits "
                "(is it a Nest thermostat with a sensor, not just a display?)."
            )

        room_name = None
        for relation in payload.get("parentRelations", []):
            room_name = relation.get("displayName")
            break

        return RoomConditions(
            air_temperature_c=float(traits[TEMPERATURE_TRAIT]["ambientTemperatureCelsius"]),
            relative_humidity_pct=float(traits[HUMIDITY_TRAIT]["ambientHumidityPercent"]),
            device_id=target_id,
            room_name=room_name,
        )
