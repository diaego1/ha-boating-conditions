"""Boating Conditions integration."""

from __future__ import annotations

import asyncio
from pathlib import Path

from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant, ServiceCall

from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import OpenMeteoClient
from .const import (
    CARD_RESOURCE_URL,
    DOMAIN,
    PLATFORMS,
    SERVICE_REFRESH_FORECAST,
    STATIC_BASE_URL,
)
from .coordinator import BoatingConditionsCoordinator

STATIC_DIRECTORY = Path(__file__).parent / "static"


async def async_setup(hass: HomeAssistant, config) -> bool:
    """Set up the domain and register services."""

    hass.data.setdefault(DOMAIN, {})
    if not hass.data[DOMAIN].get("static_registered"):
        await hass.http.async_register_static_paths(
            [
                StaticPathConfig(
                    STATIC_BASE_URL,
                    str(STATIC_DIRECTORY),
                    cache_headers=False,
                )
            ]
        )
        hass.data[DOMAIN]["static_registered"] = True
        hass.data[DOMAIN]["card_resource_url"] = CARD_RESOURCE_URL

    if not hass.services.has_service(DOMAIN, SERVICE_REFRESH_FORECAST):

        async def async_handle_refresh(call: ServiceCall) -> None:
            coordinators = hass.data.get(DOMAIN, {}).values()
            await asyncio.gather(
                *(coordinator.async_request_refresh() for coordinator in coordinators)
            )

        hass.services.async_register(
            DOMAIN,
            SERVICE_REFRESH_FORECAST,
            async_handle_refresh,
        )

    return True


async def async_setup_entry(hass: HomeAssistant, entry) -> bool:
    """Set up Boating Conditions from a config entry."""

    session = async_get_clientsession(hass)
    coordinator = BoatingConditionsCoordinator(
        hass,
        client=OpenMeteoClient(session),
        entry=entry,
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry) -> bool:
    """Unload a config entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
