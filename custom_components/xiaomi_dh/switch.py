from __future__ import annotations

from homeassistant.components.xiaomi_miio import KEY_DEVICE, KEY_COORDINATOR
from homeassistant.components.xiaomi_miio.const import (
    FEATURE_SET_BUZZER,
    FEATURE_SET_CHILD_LOCK,
    FEATURE_SET_LED,
)
from homeassistant.components.xiaomi_miio.switch import (
    DATA_KEY,
    SWITCH_TYPES,
    XiaomiGenericCoordinatedSwitch,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import (
    DOMAIN,
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the switch from a config entry."""
    unique_id = config_entry.unique_id
    device = hass.data[DOMAIN][config_entry.entry_id][KEY_DEVICE]
    coordinator = hass.data[DOMAIN][config_entry.entry_id][KEY_COORDINATOR]

    if DATA_KEY not in hass.data:
        hass.data[DATA_KEY] = {}

    device_features = FEATURE_SET_BUZZER | FEATURE_SET_CHILD_LOCK | FEATURE_SET_LED

    async_add_entities(
        XiaomiGenericCoordinatedSwitch(
            device,
            config_entry,
            f"{description.key}_{unique_id}",
            coordinator,
            description,
        )
        for description in SWITCH_TYPES
        if description.feature & device_features
    )
