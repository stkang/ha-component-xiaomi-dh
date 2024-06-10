"""Constants for the Imazu Wall Pad integration."""

from homeassistant.components.climate import ATTR_HUMIDITY
from homeassistant.const import Platform

DOMAIN = "xiaomi_dh"

PLATFORMS = [
    Platform.CLIMATE,
    Platform.SWITCH,
    Platform.BINARY_SENSOR,
]

# Air Dehumidifier
ATTR_TEMPERATURE = "temperature"
ATTR_MODE = "mode"
ATTR_BUZZER = "buzzer"
ATTR_CHILD_LOCK = "child_lock"
ATTR_LED = "led"
ATTR_FAN_SPEED = "fan_speed"
ATTR_TARGET_HUMIDITY = "target_humidity"
ATTR_TANK_FULL = "tank_full"
ATTR_COMPRESSOR_STATUS = "compressor_status"
ATTR_DEFROST_STATUS = "defrost_status"
ATTR_FAN_ST = "fan_st"
ATTR_ALARM = "alarm"

AVAILABLE_ATTRIBUTES_AIRDEHUMIDIFIER = {
    ATTR_TEMPERATURE: "temperature",
    ATTR_HUMIDITY: "humidity",
    ATTR_MODE: "mode",
    ATTR_BUZZER: "buzzer",
    ATTR_CHILD_LOCK: "child_lock",
    ATTR_TARGET_HUMIDITY: "target_humidity",
    ATTR_LED: "led",
    ATTR_FAN_SPEED: "fan_speed",
    ATTR_TANK_FULL: "tank_full",
    ATTR_COMPRESSOR_STATUS: "compressor_status",
    ATTR_DEFROST_STATUS: "defrost_status",
    ATTR_FAN_ST: "fan_st",
    ATTR_ALARM: "alarm",
}
