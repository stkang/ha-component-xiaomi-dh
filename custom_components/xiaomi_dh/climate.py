"""Support for Xiaomi Mi Air Dehumidifier."""

import logging
import math
from typing import Any

from miio.airdehumidifier import OperationMode, FanSpeed

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
    ATTR_HUMIDITY,
    HVACAction,
)
from homeassistant.components.xiaomi_miio import (
    KEY_DEVICE,
    CONF_FLOW_TYPE,
    KEY_COORDINATOR,
)
from homeassistant.components.xiaomi_miio.device import XiaomiCoordinatedMiioEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_DEVICE,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util.percentage import percentage_to_ranged_value
from .const import (
    DOMAIN,
    AVAILABLE_ATTRIBUTES_AIRDEHUMIDIFIER,
    ATTR_TARGET_HUMIDITY,
    ATTR_MODE,
    ATTR_COMPRESSOR_STATUS,
    ATTR_FAN_ST,
    ATTR_TEMPERATURE,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Humidifier from a config entry."""
    if config_entry.data[CONF_FLOW_TYPE] != CONF_DEVICE:
        return

    unique_id = config_entry.unique_id
    coordinator = hass.data[DOMAIN][config_entry.entry_id][KEY_COORDINATOR]
    air_humidifier = hass.data[DOMAIN][config_entry.entry_id][KEY_DEVICE]
    entity: ClimateEntity = XiaomiAirDehumidifier(
        air_humidifier,
        config_entry,
        unique_id,
        coordinator,
    )

    async_add_entities([entity])


class XiaomiAirDehumidifier(XiaomiCoordinatedMiioEntity, ClimateEntity):
    """Representation of a Xiaomi Air Dehumidifier."""

    _enable_turn_on_off_backwards_compatibility = False

    _attr_name = None
    _attr_precision = 1
    _attr_max_humidity: float = 60
    _attr_min_humidity: float = 40
    _attr_humidity_steps: int = 10
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.DRY]
    _attr_preset_modes = [mode.name for mode in OperationMode]
    _attr_fan_modes = [
        mode.name for mode in FanSpeed if mode not in [FanSpeed.Sleep, FanSpeed.Strong]
    ]
    _attr_temperature_unit = UnitOfTemperature.CELSIUS

    def __init__(self, device, entry, unique_id, coordinator):
        super().__init__(device, entry, unique_id, coordinator=coordinator)

        self._attributes = {}
        self._state = self.coordinator.data.is_on
        self._attributes.update(
            {
                key: self._extract_value_from_attribute(self.coordinator.data, value)
                for key, value in AVAILABLE_ATTRIBUTES_AIRDEHUMIDIFIER.items()
            }
        )
        self._attr_target_humidity = self._attributes[ATTR_TARGET_HUMIDITY]
        self._attr_current_humidity = self._attributes[ATTR_HUMIDITY]
        self._attr_current_temperature = self._attributes[ATTR_TEMPERATURE]
        self._attr_hvac_mode = HVACMode.DRY if self.is_on else HVACMode.OFF
        self._attr_preset_mode = OperationMode(self._attributes[ATTR_MODE]).name
        self._attr_fan_mode = (
            FanSpeed(self._attributes[ATTR_FAN_ST]).name
            if self.preset_mode != OperationMode.DryCloth.name
            else None
        )

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._state

    @callback
    def _handle_coordinator_update(self):
        """Fetch state from the device."""
        self._state = self.coordinator.data.is_on
        self._attributes.update(
            {
                key: self._extract_value_from_attribute(self.coordinator.data, value)
                for key, value in AVAILABLE_ATTRIBUTES_AIRDEHUMIDIFIER.items()
            }
        )
        self._attr_target_humidity = self._attributes[ATTR_TARGET_HUMIDITY]
        self._attr_current_humidity = self._attributes[ATTR_HUMIDITY]
        self._attr_current_temperature = self._attributes[ATTR_TEMPERATURE]

        self._attr_hvac_action = (
            HVACAction.DRYING
            if self._attributes[ATTR_COMPRESSOR_STATUS]
            else HVACAction.OFF
        )
        self._attr_hvac_mode = HVACMode.DRY if self.is_on else HVACMode.OFF
        self._attr_preset_mode = OperationMode(self._attributes[ATTR_MODE]).name

        self._attr_fan_mode = (
            FanSpeed(self._attributes[ATTR_FAN_ST]).name
            if self.preset_mode != OperationMode.DryCloth.name
            else None
        )

        self.async_write_ha_state()

    @property
    def supported_features(self):
        """Flag supported features."""
        features = ClimateEntityFeature(0)
        if self.is_on:
            features |= ClimateEntityFeature.PRESET_MODE
            if self.preset_mode == OperationMode.Auto.name:
                features |= ClimateEntityFeature.TARGET_HUMIDITY
            if self.preset_mode != OperationMode.DryCloth.name:
                features |= ClimateEntityFeature.FAN_MODE
        return features

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the device on."""
        if await self._try_command(
            "Turning the miio device on failed.", self._device.on
        ):
            self._state = True
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the device off."""
        if await self._try_command(
            "Turning the miio device off failed.", self._device.off
        ):
            self._state = False
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode):
        """Set new target hvac mode."""
        if hvac_mode == HVACMode.DRY:
            await self.async_turn_on()
        elif hvac_mode == HVACMode.OFF:
            await self.async_turn_off()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""

        if await self._try_command(
            "Setting the fan mode of the miio device failed.",
            self._device.set_mode,
            OperationMode[preset_mode],
        ):
            self._attr_preset_mode = preset_mode
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()

    async def async_set_humidity(self, humidity: int) -> None:
        """Set new target humidity."""

        if self.preset_mode != OperationMode.Auto.name:
            await self.async_set_preset_mode(OperationMode.Auto.name)

        target_humidity = self.translate_humidity(humidity)
        if not target_humidity:
            return
        if await self._try_command(
            "Setting the humidity of the miio device failed.",
            self._device.set_target_humidity,
            target_humidity,
        ):
            self._attr_target_humidity = humidity
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()

    async def async_set_fan_mode(self, fan_mode: str):
        """Set new target fan mode."""
        if self.preset_mode == OperationMode.DryCloth.name:
            return
        if await self._try_command(
            "Setting the fan mode of the miio device failed.",
            self._device.set_fan_speed,
            FanSpeed[fan_mode],
        ):
            self._attr_fan_mode = fan_mode
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()

    def translate_humidity(self, humidity: float) -> float | None:
        """Translate the target humidity to the first valid step."""
        return int(
            math.ceil(
                percentage_to_ranged_value((1, self._attr_humidity_steps), humidity)
            )
            * 100
            / self._attr_humidity_steps
            if 0 < humidity <= 100
            else None
        )
