"""Open-Meteo client for the Boating Conditions integration."""

from __future__ import annotations

import asyncio
from typing import Any

from aiohttp import ClientError, ClientSession

from .const import (
    DEFAULT_FORECAST_DAYS,
    MARINE_API_URL,
    UPDATE_TIMEOUT_SECONDS,
    WEATHER_API_URL,
)


class OpenMeteoApiError(Exception):
    """Raised when Open-Meteo data cannot be fetched or validated."""


class OpenMeteoClient:
    """Small client for Open-Meteo weather and marine forecast data."""

    def __init__(self, session: ClientSession) -> None:
        self._session = session

    async def async_fetch_forecasts(
        self,
        *,
        latitude: float,
        longitude: float,
        timezone_name: str,
    ) -> dict[str, Any]:
        """Fetch weather and marine forecast payloads."""

        common_params = {
            "latitude": latitude,
            "longitude": longitude,
            "forecast_days": DEFAULT_FORECAST_DAYS,
            "timezone": timezone_name,
            "cell_selection": "sea",
        }

        weather_params = {
            **common_params,
            "hourly": ",".join(
                [
                    "wind_speed_10m",
                    "wind_gusts_10m",
                    "wind_direction_10m",
                ]
            ),
            "daily": ",".join(["sunrise", "sunset"]),
            "wind_speed_unit": "kmh",
        }

        marine_params = {
            **common_params,
            "hourly": ",".join(
                [
                    "wave_height",
                    "wave_period",
                    "wave_direction",
                    "wind_wave_height",
                    "wind_wave_period",
                    "wind_wave_direction",
                    "swell_wave_height",
                    "swell_wave_period",
                    "swell_wave_direction",
                    "secondary_swell_wave_height",
                    "secondary_swell_wave_period",
                    "secondary_swell_wave_direction",
                ]
            ),
        }

        weather, marine = await asyncio.gather(
            self._async_get_json(WEATHER_API_URL, weather_params),
            self._async_get_json(MARINE_API_URL, marine_params),
        )

        self._validate_payload(weather, "weather")
        self._validate_payload(marine, "marine")

        return {
            "weather": weather,
            "marine": marine,
        }

    async def _async_get_json(
        self,
        url: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Run an HTTP GET and decode JSON."""

        try:
            async with asyncio.timeout(UPDATE_TIMEOUT_SECONDS):
                response = await self._session.get(url, params=params)
                response.raise_for_status()
                return await response.json()
        except (TimeoutError, ClientError, ValueError) as err:
            raise OpenMeteoApiError(f"Unable to fetch Open-Meteo data from {url}") from err

    @staticmethod
    def _validate_payload(payload: dict[str, Any], label: str) -> None:
        """Ensure the payload contains the sections this integration expects."""

        if "hourly" not in payload:
            raise OpenMeteoApiError(f"Open-Meteo {label} payload is missing hourly data")
        if label == "weather" and "daily" not in payload:
            raise OpenMeteoApiError("Open-Meteo weather payload is missing daily data")
