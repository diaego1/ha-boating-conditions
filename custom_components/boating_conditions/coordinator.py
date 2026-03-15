"""Coordinator for the Boating Conditions integration."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .analysis import ForecastAnalysisError, analyse_forecasts
from .api import OpenMeteoApiError, OpenMeteoClient
from .const import (
    CONF_LOCATION_NAME,
    CONF_UPDATE_INTERVAL_HOURS,
    CONF_YACHT_LENGTH_FT,
    DOMAIN,
    SCAN_INTERVAL_FALLBACK,
)

LOGGER = logging.getLogger(__name__)


class BoatingConditionsCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetch and analyse the Brighton Marina weekend outlook."""

    def __init__(self, hass, *, client: OpenMeteoClient, entry) -> None:
        update_interval = timedelta(
            hours=entry.data.get(
                CONF_UPDATE_INTERVAL_HOURS,
                entry.options.get(
                    CONF_UPDATE_INTERVAL_HOURS,
                    SCAN_INTERVAL_FALLBACK.seconds // 3600,
                ),
            )
        )

        super().__init__(
            hass,
            logger=LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=update_interval,
        )
        self.client = client
        self.entry = entry

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch the latest forecast and convert it into weekend RAG data."""

        try:
            payloads = await self.client.async_fetch_forecasts(
                latitude=float(self.entry.data["latitude"]),
                longitude=float(self.entry.data["longitude"]),
                timezone_name=self.entry.data["timezone"],
            )
            analysis = analyse_forecasts(
                weather_payload=payloads["weather"],
                marine_payload=payloads["marine"],
                timezone_name=self.entry.data["timezone"],
                yacht_length_ft=int(self.entry.data[CONF_YACHT_LENGTH_FT]),
                location_name=self.entry.data[CONF_LOCATION_NAME],
            )
        except (ForecastAnalysisError, OpenMeteoApiError, KeyError, ValueError) as err:
            raise UpdateFailed(f"Unable to update boating conditions data: {err}") from err

        return analysis
