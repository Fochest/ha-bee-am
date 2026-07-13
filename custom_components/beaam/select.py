import logging

from homeassistant.components.select import SelectEntity

from .const import DOMAIN, CHARGING_MODE_SETTING, CHARGING_MODES

_LOGGER = logging.getLogger(__name__)

# label (shown in HA / neoom app) -> neoom enum value
LABEL_TO_VALUE = {label: value for value, label in CHARGING_MODES.items()}


async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    api = data["api"]

    entities = []
    settings = coordinator.data.get("charging_point_settings", {})
    for thing_id, payload in settings.items():
        keys = {s["key"] for s in payload.get("settings", [])}
        if CHARGING_MODE_SETTING in keys:
            entities.append(BeaamWallboxModeSelect(coordinator, api, thing_id))

    async_add_entities(entities)


class BeaamWallboxModeSelect(SelectEntity):
    """Charging mode (Solar / Schnell) for a Beaam charging point."""

    def __init__(self, coordinator, api, thing_id):
        self.coordinator = coordinator
        self._api = api
        self._thing_id = thing_id

    @property
    def name(self):
        return f"Beaam Wallbox {self._thing_id[:8]} Lademodus"

    @property
    def unique_id(self):
        return f"beaam_wallbox_{self._thing_id}_lademodus"

    def _raw_value(self):
        payload = self.coordinator.data.get("charging_point_settings", {}).get(self._thing_id, {})
        for setting in payload.get("settings", []):
            if setting["key"] == CHARGING_MODE_SETTING:
                return setting.get("value")
        return None

    @property
    def options(self):
        # Known modes, plus the current raw value if the device reports something unmapped,
        # so current_option always stays within options.
        opts = list(CHARGING_MODES.values())
        raw = self._raw_value()
        if raw is not None and raw not in CHARGING_MODES and str(raw) not in opts:
            opts.append(str(raw))
        return opts

    @property
    def current_option(self):
        raw = self._raw_value()
        if raw is None:
            return None
        return CHARGING_MODES.get(raw, str(raw))

    async def async_select_option(self, option: str):
        value = LABEL_TO_VALUE.get(option)
        if value is None:
            _LOGGER.warning("Unknown Beaam charging mode option: %s", option)
            return
        await self._api.async_set_thing_setting(self._thing_id, CHARGING_MODE_SETTING, value)
        await self.coordinator.async_request_refresh()

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, f"wallbox_{self._thing_id}")},
            "name": f"Beaam Wallbox {self._thing_id[:8]}",
            "manufacturer": "NEOOM",
            "model": "CHARGING_POINT_AC",
        }

    async def async_update(self):
        await self.coordinator.async_request_refresh()
