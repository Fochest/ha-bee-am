from homeassistant.components.sensor import SensorEntity
from homeassistant.const import (
    UnitOfPower,
    UnitOfEnergy,
    PERCENTAGE,
)
from .const import DOMAIN

# Mapping von Beaam-Keys auf Einheit & Device Class
SENSOR_DEFINITIONS = {
    "POWER_PRODUCTION": (UnitOfPower.WATT, "power"),
    "POWER_CONSUMPTION_CALC": (UnitOfPower.WATT, "power"),
    "POWER_GRID": (UnitOfPower.WATT, "power"),
    "POWER_STORAGE": (UnitOfPower.WATT, "power"),
    "ENERGY_PRODUCED": (UnitOfEnergy.WATT_HOUR, "energy"),
    "ENERGY_CONSUMED": (UnitOfEnergy.WATT_HOUR, "energy"),
    "ENERGY_IMPORTED": (UnitOfEnergy.WATT_HOUR, "energy"),
    "ENERGY_EXPORTED": (UnitOfEnergy.WATT_HOUR, "energy"),
    "ENERGY_CHARGED": (UnitOfEnergy.WATT_HOUR, "energy"),
    "ENERGY_DISCHARGED": (UnitOfEnergy.WATT_HOUR, "energy"),
    "ENERGY_CONSUMED_CALC": (UnitOfEnergy.WATT_HOUR, "energy"),
    "STATE_OF_CHARGE": (PERCENTAGE, "battery"),
    "SELF_SUFFICIENCY": (PERCENTAGE, None),
    # Fraktionen → werden zusätzlich dynamisch behandelt
}

async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]

    sensors = []
    energy_flow = coordinator.data.get("site_state", {}).get("energyFlow", {})
    for state in energy_flow.get("states", []):
        key = state["key"]
        sensors.append(BeaamSensor(coordinator, key))

    async_add_entities(sensors)


class BeaamSensor(SensorEntity):
    def __init__(self, coordinator, key):
        self.coordinator = coordinator
        self._key = key
        definition = SENSOR_DEFINITIONS.get(key, (None, None))
        self._unit, self._device_class = definition

        # Fraktionswerte → immer in Prozent
        if key.startswith("FRACTION_"):
            self._unit = PERCENTAGE
            self._device_class = None

    @property
    def name(self):
        return f"Beaam {self._key}"

    @property
    def unique_id(self):
        return f"beaam_{self._key.lower()}"

    @property
    def native_value(self):
        energy_flow = self.coordinator.data.get("site_state", {}).get("energyFlow", {})
        for state in energy_flow.get("states", []):
            if state["key"] == self._key:
                value = state["value"]
                if value is None:
                    return None
                if self._key.startswith("FRACTION_"):
                    return round(value * 100, 2)  # in %
                return value
        return None

    @property
    def native_unit_of_measurement(self):
        return self._unit

    @property
    def device_class(self):
        return self._device_class

    async def async_update(self):
        await self.coordinator.async_request_refresh()