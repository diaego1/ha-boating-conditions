"""Constants for the Boating Conditions integration."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.const import Platform

DOMAIN = "boating_conditions"
PLATFORMS: list[Platform] = [Platform.SENSOR]

DEFAULT_NAME = "Boating Conditions"
DEFAULT_LOCATION_NAME = "Brighton Marina"
DEFAULT_LATITUDE = 50.8121
DEFAULT_LONGITUDE = -0.0985
DEFAULT_TIMEZONE = "Europe/London"
DEFAULT_YACHT_LENGTH_FT = 55
DEFAULT_UPDATE_INTERVAL_HOURS = 3
DEFAULT_FORECAST_DAYS = 8

CONF_LOCATION_NAME = "location_name"
CONF_YACHT_LENGTH_FT = "yacht_length_ft"
CONF_UPDATE_INTERVAL_HOURS = "update_interval_hours"

WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"
MARINE_API_URL = "https://marine-api.open-meteo.com/v1/marine"
STATIC_BASE_URL = f"/api/{DOMAIN}/static"
CARD_FILENAME = "boating-conditions-card.js"
CARD_RESOURCE_URL = f"{STATIC_BASE_URL}/{CARD_FILENAME}"

SERVICE_REFRESH_FORECAST = "refresh_forecast"

RAG_GREEN = "green"
RAG_YELLOW = "yellow"
RAG_RED = "red"
RAG_UNKNOWN = "unknown"
RAG_OPTIONS = [RAG_GREEN, RAG_YELLOW, RAG_RED, RAG_UNKNOWN]

DAY_KEYS = ("friday", "saturday", "sunday")
DAY_INDEX_TO_KEY = {
    4: "friday",
    5: "saturday",
    6: "sunday",
}

UPDATE_TIMEOUT_SECONDS = 20

ONSHORE_MIN_DEGREES = 120
ONSHORE_MAX_DEGREES = 240

ATTRIBUTION = "Forecast data from Open-Meteo weather and marine APIs."
DISCLAIMER = (
    "Guidance only for a 55 ft motor yacht. Always check local forecasts, tides, "
    "Notices to Mariners, traffic, and real conditions before departure."
)

SCAN_INTERVAL_FALLBACK = timedelta(hours=DEFAULT_UPDATE_INTERVAL_HOURS)
