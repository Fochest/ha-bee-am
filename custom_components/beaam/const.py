DOMAIN = "beaam"
PLATFORMS = ["sensor", "select"]

API_SITE_STATE = "/api/v1/site/state"
API_SITE_CONFIGURATION = "/api/v1/site/configuration"
API_THING_STATES = "/api/v1/things/{thing_id}/states"
API_THING_SETTINGS = "/api/v1/things/{thing_id}/settings"

# Charging-point EMS operating mode (setting key OPERATING_MODE_EMS).
# Maps the neoom enum values to the labels shown in the neoom app.
CHARGING_MODE_SETTING = "OPERATING_MODE_EMS"
CHARGING_MODES = {
    "EXCESS_CONSUMPTION": "Solar",
    "FAST_CHARGING": "Schnell",
}
