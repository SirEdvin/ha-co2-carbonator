from homeassistant.const import Platform

DOMAIN = "co2_carbonator"

CONF_TAG_ID = "tag_id"
CONF_SCAN_COOLDOWN_SECONDS = "scan_cooldown_seconds"
CONF_EXPECTED_BOTTLES_PER_TANK = "expected_bottles_per_tank"

DEFAULT_SCAN_COOLDOWN_SECONDS = 45
DEFAULT_EXPECTED_BOTTLES_PER_TANK = 60

PLATFORMS = [Platform.SENSOR, Platform.BUTTON, Platform.NUMBER]

EVENT_BOTTLE_FILLED = "co2_carbonator_bottle_filled"
EVENT_TANK_REPLACED = "co2_carbonator_tank_replaced"
