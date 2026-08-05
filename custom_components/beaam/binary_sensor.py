from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    CHARGING_POINT_CONNECTIVITY_KEY,
    SITE_CONNECTIVITY_KEYS,
)


async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]

    entities = []

    energy_flow = coordinator.data.get("site_state", {}).get("energyFlow", {})
    for state in energy_flow.get("states", []):
        key = state["key"]
        if key in SITE_CONNECTIVITY_KEYS:
            entities.append(BeaamConnectivityBinarySensor(coordinator, key))

    charging_points = coordinator.data.get("charging_points", {})
    for thing_id, payload in charging_points.items():
        keys = {s["key"] for s in payload.get("states", [])}
        if CHARGING_POINT_CONNECTIVITY_KEY in keys:
            entities.append(
                BeaamChargingPointConnectivityBinarySensor(coordinator, thing_id)
            )

    async_add_entities(entities)


class BeaamConnectivityBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Per-category reachability flag from the site's energyFlow (`*_ONLINE`)."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator, key):
        super().__init__(coordinator)
        self._key = key

    @property
    def name(self):
        return f"Beaam {self._key}"

    @property
    def unique_id(self):
        return f"beaam_{self._key.lower()}"

    @property
    def is_on(self):
        # NEOOM reports None when the site has no thing of that category at all
        # (e.g. HEATING_ONLINE without a heating device) — that stays "unknown"
        # rather than being flattened to "disconnected".
        energy_flow = self.coordinator.data.get("site_state", {}).get("energyFlow", {})
        for state in energy_flow.get("states", []):
            if state["key"] == self._key:
                return state.get("value")
        return None


class BeaamChargingPointConnectivityBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Whether the Beaam currently reaches a charging point (`CONNECTION`)."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator, thing_id):
        super().__init__(coordinator)
        self._thing_id = thing_id

    @property
    def name(self):
        return f"Beaam Wallbox {self._thing_id[:8]} {CHARGING_POINT_CONNECTIVITY_KEY}"

    @property
    def unique_id(self):
        return (
            f"beaam_wallbox_{self._thing_id}_"
            f"{CHARGING_POINT_CONNECTIVITY_KEY.lower()}"
        )

    @property
    def is_on(self):
        cp = self.coordinator.data.get("charging_points", {}).get(self._thing_id, {})
        for state in cp.get("states", []):
            if state["key"] == CHARGING_POINT_CONNECTIVITY_KEY:
                return state.get("value")
        return None

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, f"wallbox_{self._thing_id}")},
            "name": f"Beaam Wallbox {self._thing_id[:8]}",
            "manufacturer": "NEOOM",
            "model": "CHARGING_POINT_AC",
        }
