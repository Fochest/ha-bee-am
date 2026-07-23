from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import (
    UnitOfPower,
    UnitOfEnergy,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfTime,
    PERCENTAGE,
)
from .const import DOMAIN

# Mapping von Beaam-Keys auf Einheit & Device Class
SENSOR_DEFINITIONS = {
    "POWER_PRODUCTION": (UnitOfPower.WATT, "power", SensorStateClass.MEASUREMENT),
    # POWER_CONSUMPTION = measured total (meter-equipped sites);
    # POWER_CONSUMPTION_CALC = calculated fallback when no dedicated meter exists
    "POWER_CONSUMPTION": (UnitOfPower.WATT, "power", SensorStateClass.MEASUREMENT),
    "POWER_CONSUMPTION_CALC": (UnitOfPower.WATT, "power", SensorStateClass.MEASUREMENT),
    # sub-consumers; APPLIANCES = total consumption minus all other sub-consumers
    "POWER_APPLIANCES": (UnitOfPower.WATT, "power", SensorStateClass.MEASUREMENT),
    "POWER_CHARGING_STATIONS": (UnitOfPower.WATT, "power", SensorStateClass.MEASUREMENT),
    "POWER_HEATING": (UnitOfPower.WATT, "power", SensorStateClass.MEASUREMENT),
    "POWER_GRID": (UnitOfPower.WATT, "power", SensorStateClass.MEASUREMENT),
    "POWER_STORAGE": (UnitOfPower.WATT, "power", SensorStateClass.MEASUREMENT),
    "MAX_NETWORK_UTILIZATION": (UnitOfPower.WATT, "power", SensorStateClass.MEASUREMENT),
    "ENERGY_PRODUCED": (UnitOfEnergy.WATT_HOUR, "energy", SensorStateClass.TOTAL_INCREASING),
    "ENERGY_CONSUMED": (UnitOfEnergy.WATT_HOUR, "energy", SensorStateClass.TOTAL_INCREASING),
    "ENERGY_CONSUMED_CALC": (UnitOfEnergy.WATT_HOUR, "energy", SensorStateClass.TOTAL_INCREASING),
    "ENERGY_APPLIANCES": (UnitOfEnergy.WATT_HOUR, "energy", SensorStateClass.TOTAL_INCREASING),
    "ENERGY_CHARGING_STATIONS": (UnitOfEnergy.WATT_HOUR, "energy", SensorStateClass.TOTAL_INCREASING),
    "ENERGY_HEATING": (UnitOfEnergy.WATT_HOUR, "energy", SensorStateClass.TOTAL_INCREASING),
    "ENERGY_IMPORTED": (UnitOfEnergy.WATT_HOUR, "energy", SensorStateClass.TOTAL_INCREASING),
    "ENERGY_EXPORTED": (UnitOfEnergy.WATT_HOUR, "energy", SensorStateClass.TOTAL_INCREASING),
    "ENERGY_CHARGED": (UnitOfEnergy.WATT_HOUR, "energy", SensorStateClass.TOTAL_INCREASING),
    "ENERGY_DISCHARGED": (UnitOfEnergy.WATT_HOUR, "energy", SensorStateClass.TOTAL_INCREASING),
    "STATE_OF_CHARGE": (PERCENTAGE, "battery", SensorStateClass.MEASUREMENT),
    "SELF_SUFFICIENCY": (PERCENTAGE, None, SensorStateClass.MEASUREMENT)
    # Fraktionen → werden zusätzlich dynamisch behandelt
}

# Keys a CHARGING_POINT_AC thing exposes via /things/{id}/states
CHARGING_POINT_SENSOR_DEFINITIONS = {
    "ACTIVE_POWER": (UnitOfPower.WATT, "power", SensorStateClass.MEASUREMENT),
    "MAX_POWER_CHARGE": (UnitOfPower.WATT, "power", SensorStateClass.MEASUREMENT),
    "MAX_POWER_CHARGE_FALLBACK": (UnitOfPower.WATT, "power", SensorStateClass.MEASUREMENT),
    "CURRENT_P1": (UnitOfElectricCurrent.AMPERE, "current", SensorStateClass.MEASUREMENT),
    "CURRENT_P2": (UnitOfElectricCurrent.AMPERE, "current", SensorStateClass.MEASUREMENT),
    "CURRENT_P3": (UnitOfElectricCurrent.AMPERE, "current", SensorStateClass.MEASUREMENT),
    "VOLTAGE_P1": (UnitOfElectricPotential.VOLT, "voltage", SensorStateClass.MEASUREMENT),
    "VOLTAGE_P2": (UnitOfElectricPotential.VOLT, "voltage", SensorStateClass.MEASUREMENT),
    "VOLTAGE_P3": (UnitOfElectricPotential.VOLT, "voltage", SensorStateClass.MEASUREMENT),
    "CONSUMED_ENERGY_TOTAL": (UnitOfEnergy.WATT_HOUR, "energy", SensorStateClass.TOTAL_INCREASING),
    # session energy: resets per charging process, so TOTAL (not TOTAL_INCREASING)
    "CONSUMED_ENERGY_ACTUAL": (UnitOfEnergy.WATT_HOUR, "energy", SensorStateClass.TOTAL),
    "CHARGING_PROCESS_ENERGY": (UnitOfEnergy.WATT_HOUR, "energy", SensorStateClass.TOTAL),
    "CHARGING_TIME": (UnitOfTime.SECONDS, "duration", SensorStateClass.MEASUREMENT),
    "EV_STATE_CODE": (None, None, None),
    "CP_STATE_CODE": (None, None, None),
    "PHASE_SWITCHING_MODE": (None, None, None),
    "LAST_RFID_CARD": (None, None, None),
    "SERIAL_NUMBER": (None, None, None),
    "FIRMWARE_VERSION": (None, None, None),
}


async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]

    sensors = []
    energy_flow = coordinator.data.get("site_state", {}).get("energyFlow", {})
    for state in energy_flow.get("states", []):
        key = state["key"]
        sensors.append(BeaamSensor(coordinator, key))

    charging_points = coordinator.data.get("charging_points", {})
    for thing_id, payload in charging_points.items():
        for state in payload.get("states", []):
            key = state["key"]
            if key in CHARGING_POINT_SENSOR_DEFINITIONS:
                sensors.append(BeaamChargingPointSensor(coordinator, thing_id, key))

    async_add_entities(sensors)


class BeaamSensor(SensorEntity):
    def __init__(self, coordinator, key):
        self.coordinator = coordinator
        self._key = key
        definition = SENSOR_DEFINITIONS.get(key, (None, None, None))
        self._unit, self._device_class, self._state_class = definition

        if key.startswith("FRACTION_"):
            self._unit = PERCENTAGE
            self._device_class = None
            self._state_class = SensorStateClass.MEASUREMENT
        elif self._unit is None:
            # Key not explicitly mapped: infer sensible metadata from the
            # POWER_/ENERGY_ prefix so newly added NEOOM keys still get a unit
            # (and are thus auto-excluded from the logbook) without a code change.
            if key.startswith("POWER_"):
                self._unit = UnitOfPower.WATT
                self._device_class = "power"
                self._state_class = SensorStateClass.MEASUREMENT
            elif key.startswith("ENERGY_"):
                self._unit = UnitOfEnergy.WATT_HOUR
                self._device_class = "energy"
                self._state_class = SensorStateClass.TOTAL_INCREASING

        # The energyFlow loop creates a sensor for every key the NEOOM API
        # returns. Keys we can give a unit to (explicit map, FRACTION_, or an
        # inferred POWER_/ENERGY_ prefix) are continuous and stay out of the
        # logbook, so enable them. Anything still without a unit (unknown string
        # keys) is created disabled so it never clutters the activity stream
        # until we map it properly.
        self._attr_entity_registry_enabled_default = self._unit is not None

    @property
    def name(self):
        return f"Beaam {self._key}"

    @property
    def unique_id(self):
        return f"beaam_{self._key.lower()}"

    @property
    def state_class(self):
        return self._state_class

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


class BeaamChargingPointSensor(SensorEntity):
    def __init__(self, coordinator, thing_id, key):
        self.coordinator = coordinator
        self._thing_id = thing_id
        self._key = key
        definition = CHARGING_POINT_SENSOR_DEFINITIONS.get(key, (None, None, None))
        self._unit, self._device_class, self._state_class = definition

    @property
    def name(self):
        return f"Beaam Wallbox {self._thing_id[:8]} {self._key}"

    @property
    def unique_id(self):
        return f"beaam_wallbox_{self._thing_id}_{self._key.lower()}"

    @property
    def state_class(self):
        return self._state_class

    @property
    def native_value(self):
        cp = self.coordinator.data.get("charging_points", {}).get(self._thing_id, {})
        for state in cp.get("states", []):
            if state["key"] == self._key:
                return state.get("value")
        return None

    @property
    def native_unit_of_measurement(self):
        return self._unit

    @property
    def device_class(self):
        return self._device_class

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
