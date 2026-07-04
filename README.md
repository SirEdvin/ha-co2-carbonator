# CO₂ Carbonator for Home Assistant

A small Home Assistant custom integration that provides a clean device/entity model for tracking a manual water carbonator.

The integration deliberately does **not** know about NFC tags, scanners, cooldowns, or any other trigger source. It exposes services/actions and buttons. Your own Home Assistant automations decide when to call them — for example, after an NFC scan.

## Scope

This integration provides:

- One Home Assistant device representing your manual CO₂ carbonator.
- Entities for current tank tracking and summary metrics.
- Services/actions for recording bottles, correcting bottle records, and replacing/initializing tanks.
- Buttons for manual dashboard use.
- No NFC tag handling.
- No cooldown logic.
- No custom `.storage` database.

State is represented by Home Assistant entities. After restart, the integration restores its runtime values from the last HA entity state attributes when available.

## Entities

The integration creates one device with entities similar to:

```text
sensor.co2_carbonator_current_tank_bottles
sensor.co2_carbonator_lifetime_bottles
sensor.co2_carbonator_completed_tanks
sensor.co2_carbonator_last_completed_tank_bottles
sensor.co2_carbonator_average_bottles_per_completed_tank
sensor.co2_carbonator_estimated_bottles_remaining
sensor.co2_carbonator_tank_usage_percent
sensor.co2_carbonator_current_tank_age
sensor.co2_carbonator_bottles_per_day_current_tank
sensor.co2_carbonator_current_tank_id
sensor.co2_carbonator_tank_started
sensor.co2_carbonator_last_bottle_recorded
number.co2_carbonator_expected_bottles_per_tank
button.co2_carbonator_record_bottle
button.co2_carbonator_unrecord_bottle
button.co2_carbonator_replace_tank
button.co2_carbonator_initialize_current_tank
```

Exact entity IDs may vary based on your integration/device name.

## Services/actions

### `co2_carbonator.record_bottle`

Record one or more carbonated bottles for the current tank.

```yaml
action: co2_carbonator.record_bottle
data:
  amount: 1
```

If you have multiple CO₂ Carbonator devices, pass `config_entry_id`:

```yaml
action: co2_carbonator.record_bottle
data:
  config_entry_id: "01JABCDEF1234567890"
  amount: 1
```

### `co2_carbonator.unrecord_bottle`

Subtract one or more bottles from the current tank and lifetime counts. The integration removes only bottles that still exist on the current tank and clamps counts at `0`, so this action is safe to use when correcting mistakes.

This does not change `Last Bottle Recorded`; that timestamp remains the time of the last positive bottle record. The integration fires `co2_carbonator_bottle_unrecorded` for downstream correction automations.

```yaml
action: co2_carbonator.unrecord_bottle
data:
  amount: 1
```

### `co2_carbonator.replace_tank`

Close the current tank session and start a new tank. This increments completed-tank metrics and resets current tank bottles to `0`.

```yaml
action: co2_carbonator.replace_tank
```

Optional explicit new tank ID:

```yaml
action: co2_carbonator.replace_tank
data:
  tank_id: "CO2-2026-06-27"
```

### `co2_carbonator.initialize_tank`

Start or reset the current tank without recording the previous tank as completed. Useful after first setup or when correcting state.

```yaml
action: co2_carbonator.initialize_tank
data:
  tank_id: "CO2-2026-06-27"
  current_bottles: 0
```

## Example NFC automation

This integration does not handle NFC directly. Use a Home Assistant automation like this:

```yaml
alias: CO₂ - Bottle recorded from NFC
mode: single
trigger:
  - platform: tag
    tag_id: YOUR_NFC_TAG_UUID
action:
  - action: co2_carbonator.record_bottle
    data:
      amount: 1
```

If you want cooldown/debounce behavior, implement it in this automation, for example with a timer helper or automation conditions.

## Installation

### Option 1: HACS custom repository

1. In Home Assistant, open **HACS → Integrations**.
2. Open the three-dot menu and choose **Custom repositories**.
3. Add this repository URL:

   ```text
   https://github.com/SirEdvin/ha-co2-carbonator
   ```

4. Select category **Integration**.
5. Install **CO₂ Carbonator**.
6. Restart Home Assistant.
7. Go to **Settings → Devices & services → Add integration**.
8. Search for **CO₂ Carbonator**.

### Option 2: Manual install

Copy this directory from the repository:

```text
custom_components/co2_carbonator
```

to your Home Assistant config directory:

```text
/config/custom_components/co2_carbonator
```

Then restart Home Assistant and add the integration from **Settings → Devices & services → Add integration**.

## Configuration

The setup form asks for:

| Field | Description |
|---|---|
| Name | Device/integration name, e.g. `CO₂ Carbonator` |
| Expected bottles per tank | Default `60`; used for remaining/usage estimates |

## Usage

1. Add the integration.
2. Press **Initialize Current Tank** once if you want to start from a clean current tank.
3. Call `co2_carbonator.record_bottle` from your NFC automation or press **Record Bottle** manually.
4. Call `co2_carbonator.unrecord_bottle` or press **Unrecord Bottle** to correct accidental records.
5. Press **Replace Tank** or call `co2_carbonator.replace_tank` when installing a new CO₂ tank.

## Suggested dashboard card

```yaml
type: entities
title: CO₂ Carbonator
entities:
  - entity: sensor.co2_carbonator_current_tank_id
    name: Current tank
  - entity: sensor.co2_carbonator_tank_started
    name: Tank started
  - entity: sensor.co2_carbonator_current_tank_bottles
    name: Bottles on current tank
  - entity: sensor.co2_carbonator_last_bottle_recorded
    name: Last bottle recorded
  - entity: sensor.co2_carbonator_current_tank_age
    name: Tank age
  - entity: sensor.co2_carbonator_bottles_per_day_current_tank
    name: Bottles/day
  - entity: number.co2_carbonator_expected_bottles_per_tank
    name: Expected bottles per tank
  - entity: sensor.co2_carbonator_estimated_bottles_remaining
    name: Estimated bottles remaining
  - entity: sensor.co2_carbonator_tank_usage_percent
    name: Tank usage
  - entity: sensor.co2_carbonator_last_completed_tank_bottles
    name: Last completed tank bottles
  - entity: sensor.co2_carbonator_average_bottles_per_completed_tank
    name: Average bottles/tank
  - entity: button.co2_carbonator_record_bottle
    name: Record bottle
  - entity: button.co2_carbonator_unrecord_bottle
    name: Unrecord bottle
  - entity: button.co2_carbonator_replace_tank
    name: Replace CO₂ tank
```

## Events

The integration fires events for optional downstream automations:

- `co2_carbonator_bottle_recorded`
- `co2_carbonator_bottle_unrecorded`
- `co2_carbonator_tank_replaced`

## Development

Run a syntax check:

```bash
python3 -m py_compile custom_components/co2_carbonator/*.py
```

This repository intentionally has no runtime dependencies outside Home Assistant.
