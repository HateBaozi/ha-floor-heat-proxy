"""Climate platform for Floor Heat Proxy."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant.components.climate import PLATFORM_SCHEMA, ClimateEntity
from homeassistant.components.climate.const import (
    ATTR_TEMPERATURE,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.const import ATTR_ENTITY_ID, CONF_NAME, CONF_UNIQUE_ID, STATE_ON, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util import slugify

from .const import (
    CONF_ENABLED_ENTITY,
    CONF_HEAT_DEMAND_ENTITY,
    CONF_HVAC_ACTION_ENTITY,
    CONF_PREDICTED_TEMPERATURE_ENTITY,
    CONF_PRESET_ENTITY,
    CONF_PRESET_TEMPERATURES,
    CONF_SENSOR_VALID_ENTITY,
    CONF_TARGET_TEMPERATURE_ENTITY,
    CONF_TEMPERATURE_SENSOR,
    CONF_VALVE_SWITCH_ENTITY,
    DEFAULT_MAX_TEMP,
    DEFAULT_MIN_TEMP,
    DEFAULT_PRESET_TEMPERATURES,
    DEFAULT_TARGET_TEMP_STEP,
    PRESET_MODES,
)

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_UNIQUE_ID): cv.string,
        vol.Required(CONF_TEMPERATURE_SENSOR): cv.entity_id,
        vol.Required(CONF_TARGET_TEMPERATURE_ENTITY): cv.entity_id,
        vol.Required(CONF_ENABLED_ENTITY): cv.entity_id,
        vol.Required(CONF_PRESET_ENTITY): cv.entity_id,
        vol.Required(CONF_PREDICTED_TEMPERATURE_ENTITY): cv.entity_id,
        vol.Required(CONF_HEAT_DEMAND_ENTITY): cv.entity_id,
        vol.Required(CONF_HVAC_ACTION_ENTITY): cv.entity_id,
        vol.Required(CONF_VALVE_SWITCH_ENTITY): cv.entity_id,
        vol.Required(CONF_SENSOR_VALID_ENTITY): cv.entity_id,
        vol.Optional(
            CONF_PRESET_TEMPERATURES,
            default=DEFAULT_PRESET_TEMPERATURES,
        ): vol.Schema({cv.string: vol.Coerce(float)}),
    }
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up Floor Heat Proxy climate entities from YAML."""
    async_add_entities([FloorHeatProxyClimate(hass, config)])


class FloorHeatProxyClimate(ClimateEntity):
    """Proxy climate entity backed by helpers and template entities."""

    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
    _attr_preset_modes = PRESET_MODES
    _attr_min_temp = DEFAULT_MIN_TEMP
    _attr_max_temp = DEFAULT_MAX_TEMP
    _attr_target_temperature_step = DEFAULT_TARGET_TEMP_STEP
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.PRESET_MODE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )
    _attr_should_poll = False

    def __init__(self, hass: HomeAssistant, config: ConfigType) -> None:
        """Initialize the proxy climate entity."""
        self.hass = hass
        self._attr_name = config[CONF_NAME]
        self._attr_unique_id = config[CONF_UNIQUE_ID]
        self._temperature_sensor = config[CONF_TEMPERATURE_SENSOR]
        self._target_temperature_entity = config[CONF_TARGET_TEMPERATURE_ENTITY]
        self._enabled_entity = config[CONF_ENABLED_ENTITY]
        self._preset_entity = config[CONF_PRESET_ENTITY]
        self._predicted_temperature_entity = config[CONF_PREDICTED_TEMPERATURE_ENTITY]
        self._heat_demand_entity = config[CONF_HEAT_DEMAND_ENTITY]
        self._hvac_action_entity = config[CONF_HVAC_ACTION_ENTITY]
        self._valve_switch_entity = config[CONF_VALVE_SWITCH_ENTITY]
        self._sensor_valid_entity = config[CONF_SENSOR_VALID_ENTITY]
        self._preset_temperatures: Mapping[str, float] = config[CONF_PRESET_TEMPERATURES]
        self._attr_icon = "mdi:radiator"
        self._enable_turn_on_off_backwards_compatibility = False

    @property
    def current_temperature(self) -> float | None:
        """Return current room temperature."""
        return self._float_state(self._temperature_sensor)

    @property
    def temperature_unit(self) -> str:
        """Return the configured HA temperature unit."""
        return self.hass.config.units.temperature_unit

    @property
    def target_temperature(self) -> float | None:
        """Return target room temperature."""
        return self._float_state(self._target_temperature_entity)

    @property
    def hvac_mode(self) -> HVACMode:
        """Return active hvac mode."""
        return HVACMode.HEAT if self._is_on(self._enabled_entity) else HVACMode.OFF

    @property
    def hvac_action(self) -> HVACAction:
        """Return current hvac action."""
        if self.hvac_mode == HVACMode.OFF:
            return HVACAction.OFF

        raw_state = self._state(self._hvac_action_entity).lower()
        mapping = {
            "heating": HVACAction.HEATING,
            "heat": HVACAction.HEATING,
            "on": HVACAction.HEATING,
            "preheating": HVACAction.PREHEATING,
            "idle": HVACAction.IDLE,
            "off": HVACAction.OFF,
        }
        return mapping.get(raw_state, HVACAction.IDLE)

    @property
    def preset_mode(self) -> str:
        """Return current preset mode."""
        state = self._state(self._preset_entity)
        return state if state in PRESET_MODES else "none"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes for observability."""
        return {
            "predicted_temperature": self._float_state(self._predicted_temperature_entity),
            "heat_demand": self._state(self._heat_demand_entity),
            "sensor_valid": self._state(self._sensor_valid_entity),
            "valve_state": self._state(self._valve_switch_entity),
            "temperature_sensor_entity": self._temperature_sensor,
            "target_temperature_entity": self._target_temperature_entity,
            "enabled_entity": self._enabled_entity,
            "preset_entity": self._preset_entity,
            "predicted_temperature_entity": self._predicted_temperature_entity,
            "heat_demand_entity": self._heat_demand_entity,
            "hvac_action_entity": self._hvac_action_entity,
            "valve_switch_entity": self._valve_switch_entity,
            "sensor_valid_entity": self._sensor_valid_entity,
        }

    async def async_added_to_hass(self) -> None:
        """Register listeners after entity is added."""
        entity_ids = [
            self._temperature_sensor,
            self._target_temperature_entity,
            self._enabled_entity,
            self._preset_entity,
            self._predicted_temperature_entity,
            self._heat_demand_entity,
            self._hvac_action_entity,
            self._valve_switch_entity,
            self._sensor_valid_entity,
        ]
        self.async_on_remove(
            async_track_state_change_event(
                self.hass,
                entity_ids,
                self._handle_dependency_change,
            )
        )

    @callback
    def _handle_dependency_change(self, event) -> None:
        """Write HA state when any dependency changes."""
        self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set a new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        await self._async_set_number_entity(self._target_temperature_entity, float(temperature))
        self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set a new hvac mode."""
        if hvac_mode == HVACMode.HEAT:
            await self._async_turn_entity_on(self._enabled_entity)
        elif hvac_mode == HVACMode.OFF:
            await self._async_turn_entity_off(self._enabled_entity)
        else:
            raise ValueError(f"Unsupported hvac mode: {hvac_mode}")

        self.async_write_ha_state()

    async def async_turn_on(self) -> None:
        """Turn on heating participation."""
        await self.async_set_hvac_mode(HVACMode.HEAT)

    async def async_turn_off(self) -> None:
        """Turn off heating participation."""
        await self.async_set_hvac_mode(HVACMode.OFF)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set preset mode and optionally write mapped target temperature."""
        if preset_mode not in PRESET_MODES:
            raise ValueError(f"Unsupported preset mode: {preset_mode}")

        await self._async_select_option(self._preset_entity, preset_mode)

        if preset_mode != "none" and preset_mode in self._preset_temperatures:
            await self._async_set_number_entity(
                self._target_temperature_entity,
                self._preset_temperatures[preset_mode],
            )

        self.async_write_ha_state()

    def _state(self, entity_id: str) -> str:
        """Return entity state as a string."""
        state = self.hass.states.get(entity_id)
        if state is None:
            return STATE_UNKNOWN
        return str(state.state)

    def _float_state(self, entity_id: str) -> float | None:
        """Return entity state as float."""
        state = self._state(entity_id)
        if state in {STATE_UNKNOWN, STATE_UNAVAILABLE, ""}:
            return None
        try:
            return float(state)
        except (TypeError, ValueError):
            return None

    def _is_on(self, entity_id: str) -> bool:
        """Return whether an entity is considered on."""
        state = self._state(entity_id).lower()
        return state in {STATE_ON, "heat", "heating", "true"}

    async def _async_turn_entity_on(self, entity_id: str) -> None:
        """Turn on an entity."""
        domain = entity_id.split(".", 1)[0]
        await self.hass.services.async_call(
            domain,
            "turn_on",
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )

    async def _async_turn_entity_off(self, entity_id: str) -> None:
        """Turn off an entity."""
        domain = entity_id.split(".", 1)[0]
        await self.hass.services.async_call(
            domain,
            "turn_off",
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )

    async def _async_set_number_entity(self, entity_id: str, value: float) -> None:
        """Write a numeric helper entity."""
        domain = entity_id.split(".", 1)[0]
        service = "set_value"
        key = "value"
        if domain not in {"input_number", "number"}:
            raise ValueError(f"{entity_id} is not a writable number entity")

        await self.hass.services.async_call(
            domain,
            service,
            {ATTR_ENTITY_ID: entity_id, key: value},
            blocking=True,
        )

    async def _async_select_option(self, entity_id: str, option: str) -> None:
        """Write an input_select or select helper."""
        domain = entity_id.split(".", 1)[0]
        if domain not in {"input_select", "select"}:
            raise ValueError(f"{entity_id} is not a writable select entity")

        service = "select_option" if domain == "input_select" else "select_option"
        await self.hass.services.async_call(
            domain,
            service,
            {ATTR_ENTITY_ID: entity_id, "option": option},
            blocking=True,
        )
