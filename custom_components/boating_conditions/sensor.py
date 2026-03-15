"""Sensor entities for the Boating Conditions integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTRIBUTION,
    CARD_RESOURCE_URL,
    CONF_LOCATION_NAME,
    DEFAULT_NAME,
    DOMAIN,
    RAG_OPTIONS,
)
from .coordinator import BoatingConditionsCoordinator


async def async_setup_entry(hass, entry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up Boating Conditions sensors."""

    coordinator: BoatingConditionsCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            WeekendOutlookSensor(coordinator, entry),
            WeekendDaySensor(coordinator, entry, "friday"),
            WeekendDaySensor(coordinator, entry, "saturday"),
            WeekendDaySensor(coordinator, entry, "sunday"),
        ]
    )


class BoatingConditionsBaseSensor(
    CoordinatorEntity[BoatingConditionsCoordinator], SensorEntity
):
    """Base sensor with shared device information."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = RAG_OPTIONS

    def __init__(self, coordinator: BoatingConditionsCoordinator, entry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="Open-Meteo",
            model="Weekend daylight boating outlook",
            name=entry.data.get(CONF_LOCATION_NAME, entry.title or DEFAULT_NAME),
        )

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.data is not None


class WeekendOutlookSensor(BoatingConditionsBaseSensor):
    """Main weekend outlook sensor."""

    _attr_name = "Weekend RAG"
    _attr_translation_key = "weekend_rag"

    def __init__(self, coordinator: BoatingConditionsCoordinator, entry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_weekend_rag"

    @property
    def native_value(self) -> str:
        data = self.coordinator.data or {}
        return data.get("state", "unknown")

    @property
    def icon(self) -> str:
        return _icon_for_rag(self.native_value)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        return {
            "summary": data.get("summary"),
            "state_label": data.get("state_label"),
            "weekend_label": data.get("weekend_label"),
            "weekend_start": data.get("weekend_start"),
            "weekend_end": data.get("weekend_end"),
            "location_name": data.get("location_name"),
            "boat_profile": data.get("boat_profile"),
            "best_day": data.get("best_day"),
            "worst_day": data.get("worst_day"),
            "days": data.get("days", []),
            "generated_at": data.get("generated_at"),
            "attribution": ATTRIBUTION,
            "disclaimer": data.get("disclaimer"),
            "card_resource_url": CARD_RESOURCE_URL,
        }


class WeekendDaySensor(BoatingConditionsBaseSensor):
    """Per-day Friday/Saturday/Sunday sensor."""

    def __init__(
        self,
        coordinator: BoatingConditionsCoordinator,
        entry,
        day_key: str,
    ) -> None:
        super().__init__(coordinator, entry)
        self._day_key = day_key
        self._attr_name = f"{day_key.capitalize()} RAG"
        self._attr_unique_id = f"{entry.entry_id}_{day_key}_rag"
        self._attr_translation_key = f"{day_key}_rag"

    @property
    def native_value(self) -> str:
        data = self.coordinator.data or {}
        day = data.get("by_key", {}).get(self._day_key, {})
        return day.get("rag", "unknown")

    @property
    def icon(self) -> str:
        return _icon_for_rag(self.native_value)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        day = dict(data.get("by_key", {}).get(self._day_key, {}))
        day["attribution"] = ATTRIBUTION
        day["location_name"] = data.get("location_name")
        day["boat_profile"] = data.get("boat_profile")
        day["weekend_label"] = data.get("weekend_label")
        day["disclaimer"] = data.get("disclaimer")
        day["card_resource_url"] = CARD_RESOURCE_URL
        return day


def _icon_for_rag(rag: str) -> str:
    if rag == "green":
        return "mdi:check-circle"
    if rag == "yellow":
        return "mdi:alert-circle"
    if rag == "red":
        return "mdi:close-circle"
    return "mdi:help-circle"
