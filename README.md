# CO₂ Carbonator for Home Assistant

A Home Assistant custom integration for tracking a manual water carbonator with one shared NFC tag.

Scan the configured NFC tag after filling a bottle. Press **Replace Tank** when you install a new CO₂ tank. The integration exposes one Home Assistant device with sensors, buttons, and a configurable expected-bottles-per-tank number.

## Features

- One NFC tag = one `bottle filled` event.
- Duplicate-scan cooldown.
- Current tank bottle count.
- Lifetime bottle count.
- Completed tank count.
- Last completed tank bottle count.
- Average bottles per completed tank.
- Expected bottles per tank setting.
- Estimated bottles remaining.
- Tank usage percent.
- Tank age and bottles/day sensors.
- Manual **Replace Tank** and **Initialize Current Tank** buttons.
- Persistent state stored in Home Assistant `.storage`.
- Fires Home Assistant events for custom automations:
  - `co2_carbonator_bottle_filled`
  - `co2_carbonator_tank_replaced`

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
sensor.co2_carbonator_last_bottle_filled
number.co2_carbonator_expected_bottles_per_tank
button.co2_carbonator_replace_tank
button.co2_carbonator_initialize_current_tank
```

Exact entity IDs may vary based on your integration/device name.

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
| NFC tag UUID | The Home Assistant tag UUID to treat as “one bottle filled” |
| Duplicate scan cooldown seconds | Default `45`; prevents accidental double-counting |
| Expected bottles per tank | Default `60`; used for remaining/usage estimates |

### Finding your NFC tag UUID

In Home Assistant, go to **Settings → Tags** and select/create the tag you want to use.

If you only see the tag entity ID, convert underscores back to hyphens. For example:

```text
tag.bb0f4609_8d97_4125_818a_d144e919d659
```

becomes:

```text
bb0f4609-8d97-4125-818a-d144e919d659
```

## Usage

1. Add the integration.
2. Press **Initialize Current Tank** once if you want to start from a clean current tank.
3. After carbonating/filling a bottle, scan the configured NFC tag.
4. When replacing the CO₂ tank, press **Replace Tank**.

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
  - entity: sensor.co2_carbonator_last_bottle_filled
    name: Last bottle filled
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
  - entity: button.co2_carbonator_replace_tank
    name: Replace CO₂ tank
```

## Events

### `co2_carbonator_bottle_filled`

Fired after a matching NFC scan is accepted.

### `co2_carbonator_tank_replaced`

Fired when the replace-tank button is pressed.

## Development

Run a syntax check:

```bash
python3 -m py_compile custom_components/co2_carbonator/*.py
```

This repository intentionally has no runtime dependencies outside Home Assistant.

## Notes

This is a local/manual tracker. It does not measure CO₂ mass or pressure directly; it counts accepted bottle-fill events and records completed tank sessions.
