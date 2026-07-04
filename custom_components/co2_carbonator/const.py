from homeassistant.const import Platform

DOMAIN = "co2_carbonator"

CONF_EXPECTED_BOTTLES_PER_TANK = "expected_bottles_per_tank"

DEFAULT_EXPECTED_BOTTLES_PER_TANK = 60

PLATFORMS = [Platform.SENSOR, Platform.BUTTON, Platform.NUMBER]

EVENT_BOTTLE_RECORDED = "co2_carbonator_bottle_recorded"
EVENT_BOTTLE_UNRECORDED = "co2_carbonator_bottle_unrecorded"
EVENT_TANK_REPLACED = "co2_carbonator_tank_replaced"

SERVICE_RECORD_BOTTLE = "record_bottle"
SERVICE_UNRECORD_BOTTLE = "unrecord_bottle"
SERVICE_REPLACE_TANK = "replace_tank"
SERVICE_INITIALIZE_TANK = "initialize_tank"

ATTR_CONFIG_ENTRY_ID = "config_entry_id"
ATTR_AMOUNT = "amount"
ATTR_TANK_ID = "tank_id"
ATTR_CURRENT_BOTTLES = "current_bottles"
