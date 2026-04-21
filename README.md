# Floor Heat Proxy

Home Assistant custom integration for floor-heating climate proxy entities.

This integration keeps your existing `climate.*` room entities and Lovelace cards, but moves actual heating control into Home Assistant helpers, templates, automations, and scripts.

## What It Does

- Exposes a thin `climate` entity for each room
- Reads `current_temperature`, `temperature`, `hvac_action`, `preset_mode`, and `hvac_mode` from helper-backed entities
- Writes target temperature, enable state, and preset changes back to helpers
- Lets existing climate cards keep working while you replace `generic_thermostat` with your own curve-based control logic

## Installation

### HACS

1. Add this repository as a custom integration repository in HACS.
2. Install `Floor Heat Proxy`.
3. Restart Home Assistant.

### Manual

Copy `custom_components/floor_heat_proxy` into your HA config directory and restart Home Assistant.

## YAML Configuration

Add entries to `climate.yaml`:

```yaml
- platform: floor_heat_proxy
  name: 主卧地暖
  unique_id: floor_heat_proxy_zhu_wo
  temperature_sensor: sensor.lumi_cn_lumi_158d00041f4592_v1_temperature_p_2_1
  target_temperature_entity: input_number.floor_heat_zhu_wo_target_temp
  enabled_entity: input_boolean.floor_heat_zhu_wo_enabled
  preset_entity: input_select.floor_heat_zhu_wo_preset
  predicted_temperature_entity: sensor.floor_heat_zhu_wo_predicted_temp
  heat_demand_entity: binary_sensor.floor_heat_zhu_wo_heat_demand
  hvac_action_entity: sensor.floor_heat_zhu_wo_hvac_action
  valve_switch_entity: switch.yeelink_cn_358374474_sw1_on_p_3_1
  sensor_valid_entity: binary_sensor.floor_heat_zhu_wo_sensor_valid
```

See:

- [examples/climate.yaml](examples/climate.yaml)
- [examples/packages/floor_heat_curve.yaml](examples/packages/floor_heat_curve.yaml)

## Expected Helper Model

For each room the integration expects:

- `input_number.floor_heat_<room>_target_temp`
- `input_boolean.floor_heat_<room>_enabled`
- `input_select.floor_heat_<room>_preset`
- `sensor.floor_heat_<room>_predicted_temp`
- `binary_sensor.floor_heat_<room>_heat_demand`
- `sensor.floor_heat_<room>_hvac_action`
- `binary_sensor.floor_heat_<room>_sensor_valid`

The package example includes the complete helper, template, automation, and script structure for all 8 rooms.

## Presets

Default preset temperature mapping:

- `away`: `18.0`
- `comfort`: `23.0`
- `home`: `22.0`
- `sleep`: `21.0`
- `none`: leave target temperature unchanged

You can override those values per entity in YAML with `preset_temperatures`.

