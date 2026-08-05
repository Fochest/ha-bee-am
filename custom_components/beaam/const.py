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
# Maps the neoom enum values to the labels shown in the neoom app and the
# CONNECT portal. NEOOM does not document the permitted values anywhere in the
# API (SettingDto.value is just string|number|boolean); these are the five the
# CONNECT portal translates under "OPERATING_MODE_EMS/values".
CHARGING_MODE_SETTING = "OPERATING_MODE_EMS"
CHARGING_MODES = {
    "DEVICE_CONTROLLED": "Ausgenommen",
    "EXCESS_CONSUMPTION": "Solar",
    "FAST_CHARGING": "Schnell",
    "FLEXIBILITY_MARKETING": "Flexibilitätsvermarktung",
    "GRIID_CONTROLLED": "Intelligent",
}

# Of those, the ones offered as a choice. The rest are labelled only, and stay
# selectable while the device itself reports them:
#
# - GRIID_CONTROLLED ("Intelligent") needs a neoom CONNECT Mega/Giga
#   subscription. The local API has no way to tell whether one exists - there is
#   no entitlement field anywhere in it, and a Beaam without the subscription
#   accepts and keeps the value regardless (measured). What such a station then
#   does is unknown; the plausible failure is that no charging plan ever arrives
#   and the car silently does not charge. So it is not offered: a subscriber sets
#   it once in the neoom app, after which the device reports it and it becomes
#   selectable here - and switching away from it is a one-way door, which is the
#   right behaviour if the subscription has lapsed.
# - DEVICE_CONTROLLED ("Ausgenommen") would take the wallbox out of CONNECT's
#   control entirely, and FLEXIBILITY_MARKETING is not a charging mode.
SELECTABLE_CHARGING_MODES = (
    "EXCESS_CONSUMPTION",
    "FAST_CHARGING",
)
