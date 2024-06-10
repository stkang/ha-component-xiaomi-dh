from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.xiaomi_miio import KEY_DEVICE, KEY_COORDINATOR
from homeassistant.components.xiaomi_miio.binary_sensor import (
    XiaomiMiioBinarySensorDescription,
    XiaomiGenericBinarySensor,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import (
    DOMAIN,
    ATTR_TANK_FULL,
    ATTR_DEFROST_STATUS,
)

BINARY_SENSOR_TYPES = (
    XiaomiMiioBinarySensorDescription(
        key=ATTR_TANK_FULL,
        name="Water tank full",
        icon="mdi:water-alert",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    XiaomiMiioBinarySensorDescription(
        key=ATTR_DEFROST_STATUS,
        name="Defrost status",
        icon="mdi:snowflake-melt",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Xiaomi sensor from a config entry."""
    entities = []

    for description in BINARY_SENSOR_TYPES:
        entities.append(
            XiaomiGenericBinarySensor(
                hass.data[DOMAIN][config_entry.entry_id][KEY_DEVICE],
                config_entry,
                f"{description.key}_{config_entry.unique_id}",
                hass.data[DOMAIN][config_entry.entry_id][KEY_COORDINATOR],
                description,
            )
        )

    async_add_entities(entities)
