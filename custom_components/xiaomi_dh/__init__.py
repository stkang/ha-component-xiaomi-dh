import asyncio
import logging
from datetime import timedelta

from miio import (
    DeviceException,
    AirDehumidifier,
)

from homeassistant.components.xiaomi_miio import (
    POLLING_TIMEOUT_SEC,
    KEY_DEVICE,
    KEY_COORDINATOR,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_MODEL, CONF_HOST, CONF_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import DOMAIN
from .const import PLATFORMS

_LOGGER = logging.getLogger(__name__)


def _async_update_data_default(hass, device):
    """
    alarm = {str} 'ok'
    # buzzer = {bool} True
    # child_lock = {bool} False
    @ compressor_status = {bool} True
    ## data = {defaultdict: 14} defaultdict(<function AirDehumidifier.status.<locals>.<lambda> at 0x308f4ba60>, {'on_off': 'on', 'mode': 'auto', 'fan_st': 2, ...'temp': 28, 'compressor_status': 'on', 'fan_speed': 2, 'tank_full': 'off', 'defrost_status': 'off', 'alarm': 'ok', 'auto': 40})
    # defrost_status = {bool} False
    @@ device_info = {DeviceInfo} nwt.derh.wdh318efw1 v2.2.7 (40:31:3C:37:4D:27) @ 192.168.100.47 - token: 38448b7d0c8e8b3fff3014df344bd11f
    @ fan_speed = {FanSpeed} <FanSpeed.Medium: 2>
    @ fan_st = {int} 2
    @ humidity = {int} 37
    @ is_on = {bool} True
    # led = {bool} True
    @ mode = {OperationMode} <OperationMode.Auto: 'auto'>
    power = {str} 'on'
    # tank_full = {bool} False
    @ target_humidity = {int} 40
    @ temperature = {int} 28"""

    async def update():
        """Fetch data from the device using async_add_executor_job."""

        async def _async_fetch_data():
            """Fetch data from the device."""
            async with asyncio.timeout(POLLING_TIMEOUT_SEC):
                state = await hass.async_add_executor_job(device.status)
                _LOGGER.debug("Got new state: %s", state)
                return state

        try:
            return await _async_fetch_data()
        except DeviceException as ex:
            if getattr(ex, "code", None) != -9999:
                raise UpdateFailed(ex) from ex
            _LOGGER.info("Got exception while fetching the state, trying again: %s", ex)
        # Try to fetch the data a second time after error code -9999
        try:
            return await _async_fetch_data()
        except DeviceException as ex:
            raise UpdateFailed(ex) from ex

    return update


async def async_create_miio_device_and_coordinator(
    hass: HomeAssistant, entry: ConfigEntry
) -> None:
    """Set up a data coordinator and one miio device to service multiple entities."""
    device = AirDehumidifier(
        entry.data[CONF_HOST], entry.data[CONF_TOKEN], model=entry.data[CONF_MODEL]
    )

    # Removing fan platform entity for humidifiers and migrate the name
    # to the config entry for migration
    entity_registry = er.async_get(hass)
    assert entry.unique_id
    entity_id = entity_registry.async_get_entity_id("fan", DOMAIN, entry.unique_id)
    if entity_id:
        # This check is entities that have a platform migration only
        # and should be removed in the future
        if (entity := entity_registry.async_get(entity_id)) and (
            migrate_entity_name := entity.name
        ):
            hass.config_entries.async_update_entry(entry, title=migrate_entity_name)
        entity_registry.async_remove(entity_id)

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=entry.title,
        update_method=_async_update_data_default(hass, device),
        # Polling interval. Will only be polled if there are subscribers.
        update_interval=timedelta(seconds=60),
    )

    hass.data[DOMAIN][entry.entry_id] = {
        KEY_DEVICE: device,
        KEY_COORDINATOR: coordinator,
    }

    # Trigger first data fetch
    await coordinator.async_config_entry_first_refresh()


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the Xiaomi Miio components from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    await async_create_miio_device_and_coordinator(hass, entry)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    )
    if unload_ok:
        hass.data[DOMAIN].pop(config_entry.entry_id)
    return unload_ok


async def update_listener(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)
