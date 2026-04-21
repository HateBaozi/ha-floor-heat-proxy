"""Constants for Floor Heat Proxy."""

from __future__ import annotations

DOMAIN = "floor_heat_proxy"

CONF_ENABLED_ENTITY = "enabled_entity"
CONF_HEAT_DEMAND_ENTITY = "heat_demand_entity"
CONF_HVAC_ACTION_ENTITY = "hvac_action_entity"
CONF_PREDICTED_TEMPERATURE_ENTITY = "predicted_temperature_entity"
CONF_PRESET_ENTITY = "preset_entity"
CONF_PRESET_TEMPERATURES = "preset_temperatures"
CONF_SENSOR_VALID_ENTITY = "sensor_valid_entity"
CONF_TARGET_TEMPERATURE_ENTITY = "target_temperature_entity"
CONF_TEMPERATURE_SENSOR = "temperature_sensor"
CONF_VALVE_SWITCH_ENTITY = "valve_switch_entity"

DEFAULT_MAX_TEMP = 30.0
DEFAULT_MIN_TEMP = 15.0
DEFAULT_TARGET_TEMP_STEP = 0.5

DEFAULT_PRESET_TEMPERATURES = {
    "away": 18.0,
    "comfort": 23.0,
    "home": 22.0,
    "sleep": 21.0,
}

PRESET_MODES = ["none", "away", "comfort", "home", "sleep"]

