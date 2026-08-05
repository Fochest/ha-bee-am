DOMAIN = "beaam"
PLATFORMS = ["sensor", "binary_sensor", "select"]

API_SITE_STATE = "/api/v1/site/state"
API_SITE_CONFIGURATION = "/api/v1/site/configuration"
API_THING_STATES = "/api/v1/things/{thing_id}/states"
API_THING_SETTINGS = "/api/v1/things/{thing_id}/settings"

# energyFlow keys NEOOM declares as BOOLEAN in /site/configuration: one
# reachability flag per device category ("does the Beaam see the things of that
# class"). Handled by binary_sensor, so the sensor platform skips them.
SITE_CONNECTIVITY_KEYS = {
    "CHARGING_POINTS_ONLINE",
    "GRID_METERS_ONLINE",
    "HEATING_ONLINE",
    "PRODUCERS_ONLINE",
    "STORAGES_ONLINE",
}

# CHARGING_POINT_AC state telling whether the Beaam reaches the station.
CHARGING_POINT_CONNECTIVITY_KEY = "CONNECTION"

# Charging-point EMS operating mode (setting key OPERATING_MODE_EMS).
# Maps the neoom enum values to the labels shown in the neoom app.
CHARGING_MODE_SETTING = "OPERATING_MODE_EMS"
CHARGING_MODES = {
    "EXCESS_CONSUMPTION": "Solar",
    "FAST_CHARGING": "Schnell",
}
