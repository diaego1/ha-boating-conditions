"""Config flow for Boating Conditions."""

from __future__ import annotations

from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import OpenMeteoApiError, OpenMeteoClient
from .const import (
    CONF_LOCATION_NAME,
    CONF_UPDATE_INTERVAL_HOURS,
    CONF_YACHT_LENGTH_FT,
    DEFAULT_LATITUDE,
    DEFAULT_LOCATION_NAME,
    DEFAULT_LONGITUDE,
    DEFAULT_NAME,
    DEFAULT_TIMEZONE,
    DEFAULT_UPDATE_INTERVAL_HOURS,
    DEFAULT_YACHT_LENGTH_FT,
    DOMAIN,
)


class BoatingConditionsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Boating Conditions."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            unique_id = self._build_unique_id(
                latitude=float(user_input[CONF_LATITUDE]),
                longitude=float(user_input[CONF_LONGITUDE]),
            )

            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            try:
                _validate_timezone(user_input["timezone"])
                client = OpenMeteoClient(async_get_clientsession(self.hass))
                await client.async_fetch_forecasts(
                    latitude=float(user_input[CONF_LATITUDE]),
                    longitude=float(user_input[CONF_LONGITUDE]),
                    timezone_name=user_input["timezone"],
                )
            except ZoneInfoNotFoundError:
                errors["timezone"] = "invalid_timezone"
            except OpenMeteoApiError:
                errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_build_schema(user_input),
            errors=errors,
        )

    @staticmethod
    def _build_unique_id(*, latitude: float, longitude: float) -> str:
        return f"{latitude:.4f},{longitude:.4f}"


def _build_schema(user_input: dict[str, Any] | None) -> vol.Schema:
    user_input = user_input or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_NAME,
                default=user_input.get(CONF_NAME, DEFAULT_NAME),
            ): str,
            vol.Required(
                CONF_LOCATION_NAME,
                default=user_input.get(CONF_LOCATION_NAME, DEFAULT_LOCATION_NAME),
            ): str,
            vol.Required(
                CONF_LATITUDE,
                default=user_input.get(CONF_LATITUDE, DEFAULT_LATITUDE),
            ): vol.All(vol.Coerce(float), vol.Range(min=-90, max=90)),
            vol.Required(
                CONF_LONGITUDE,
                default=user_input.get(CONF_LONGITUDE, DEFAULT_LONGITUDE),
            ): vol.All(vol.Coerce(float), vol.Range(min=-180, max=180)),
            vol.Required(
                "timezone",
                default=user_input.get("timezone", DEFAULT_TIMEZONE),
            ): str,
            vol.Required(
                CONF_YACHT_LENGTH_FT,
                default=user_input.get(CONF_YACHT_LENGTH_FT, DEFAULT_YACHT_LENGTH_FT),
            ): vol.All(vol.Coerce(int), vol.Range(min=30, max=120)),
            vol.Required(
                CONF_UPDATE_INTERVAL_HOURS,
                default=user_input.get(
                    CONF_UPDATE_INTERVAL_HOURS, DEFAULT_UPDATE_INTERVAL_HOURS
                ),
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=12)),
        }
    )


def _validate_timezone(value: str) -> None:
    ZoneInfo(value)
