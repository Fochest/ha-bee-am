from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import POWER_WATT
from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    entities = []

    for site_id, data in coordinator.data.items():
        site = data["site"]
        ef = data.get("energy_flow") or {}
        if ef:
            entities.append(NtuitySiteSensor(coordinator, site_id, "Total Power", ef.get("power", 0)))

    async_add_entities(entities)


class NtuitySiteSensor(CoordinatorEntity):
    def __init__(self, coordinator, site_id, name, initial_value):
        super().__init__(coordinator)
        self._site_id = site_id
        self._attr_name = f"Ntuity {site_id} {name}"
        self._attr_unique_id = f"ntuity_{site_id}_{name}"
        self._value = initial_value

    @property
    def state(self):
        try:
            return self.coordinator.data[self._site_id]["energy_flow"]["power"]
        except Exception:
            return None

    @property
    def unit_of_measurement(self):
        return POWER_WATT
