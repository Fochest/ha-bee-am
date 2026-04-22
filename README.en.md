# Home Assistant Custom Integration – BEAAM API

***English** • [Deutsch](README.md)*

This Home Assistant custom integration connects to the **internal Beaam API**. (https://developer.neoom.com/reference/concepts-terms-1)

It exposes measurements such as power production, consumption, grid import/export, battery state of charge, and **fraction values (e.g. PV → storage, PV → grid)** as Home Assistant sensors.

All sensors now also provide the `state_class` attribute so that they are evaluated correctly in Home Assistant dashboards.

---

## Installation

1. Download `beaam.zip` from the latest [release](https://github.com/Fochest/ha-bee-am/releases/latest) and extract it into:

   ```
   config/custom_components/beaam/
   ```

   so that the following structure exists:

   ```
   config/custom_components/beaam/__init__.py
   config/custom_components/beaam/manifest.json
   config/custom_components/beaam/sensor.py
   ...
   ```

2. Restart Home Assistant.

3. Go to **Settings → Devices & Services → Add integration** and search for `Beaam`.

---

## Configuration

How to create the **Bearer Token**:
- Log in at https://connect.neoom.com/users/sign_in with your Neoom credentials.
- Select the local site.
- In the menu under **Access management**, click **API keys**.
- Create a **key for the BEAAM API** and store it safely. This is the Bearer Token required in the next step.

During setup in the UI you need to provide:

- **Beaam IP/address** → e.g. `192.168.1.50`
- **Bearer Token** → API token for authentication

Sensors for all available data points are then created automatically.

---

## Supported endpoints

The integration uses the following REST endpoints of the Beaam API:

- `GET http://{beaamIp}/api/v1/site/state`  
  → returns current energy flows and KPIs
- `GET http://{beaamIp}/api/v1/site/configuration`  
  → returns site configuration data (used, among other things, for automatic discovery of wallboxes)
- `GET http://{beaamIp}/api/v1/things/{thingId}/states`  
  → returns the state of individual things (currently used for `CHARGING_POINT_AC`)

---

## Sensors & units

The main sensors automatically receive **units**, **device classes**, and **state_class** so they are visualised correctly in Home Assistant:

| Key                             | Unit | Device Class | state_class |
|---------------------------------|------|--------------|-------------|
| POWER_PRODUCTION                | W    | power        | measurement |
| POWER_CONSUMPTION_CALC          | W    | power        | measurement |
| POWER_GRID                      | W    | power        | measurement |
| POWER_STORAGE                   | W    | power        | measurement |
| ENERGY_PRODUCED                 | Wh   | energy       | total_increasing |
| ENERGY_CONSUMED_CALC            | Wh   | energy       | total_increasing |
| ENERGY_IMPORTED                 | Wh   | energy       | total_increasing |
| ENERGY_EXPORTED                 | Wh   | energy       | total_increasing |
| ENERGY_CHARGED                  | Wh   | energy       | total_increasing |
| ENERGY_DISCHARGED               | Wh   | energy       | total_increasing |
| STATE_OF_CHARGE                 | %    | battery      | measurement |
| SELF_SUFFICIENCY                | %    | –            | measurement |
| FRACTION_PV_TO_STORAGE          | %    | –            | measurement |
| FRACTION_PV_TO_GRID             | %    | –            | measurement |
| FRACTION_PV_TO_CONSUMPTION      | %    | –            | measurement |
| FRACTION_GRID_TO_STORAGE        | %    | –            | measurement |
| FRACTION_GRID_TO_CONSUMPTION    | %    | –            | measurement |
| FRACTION_STORAGE_TO_CONSUMPTION | %    | –            | measurement |
| FRACTION_STORAGE_TO_GRID        | %    | –            | measurement |

All **fraction values** are automatically converted from decimals (e.g. `0.1188`) into percent (e.g. `11.88 %`).

---

## Wallbox (CHARGING_POINT_AC)

Every wallbox of type `CHARGING_POINT_AC` configured on the site is detected automatically (discovery via `/site/configuration` based on the thing type — the actual thing ID is not hard-coded) and added as its own device in Home Assistant. For each wallbox, the following sensors are created:

| Key                       | Unit | Device Class | state_class      |
|---------------------------|------|--------------|------------------|
| ACTIVE_POWER              | W    | power        | measurement      |
| MAX_POWER_CHARGE          | W    | power        | measurement      |
| MAX_POWER_CHARGE_FALLBACK | W    | power        | measurement      |
| CURRENT_P1 / P2 / P3      | A    | current      | measurement      |
| VOLTAGE_P1 / P2 / P3      | V    | voltage      | measurement      |
| CONSUMED_ENERGY_TOTAL     | Wh   | energy       | total_increasing |
| CONSUMED_ENERGY_ACTUAL    | Wh   | energy       | total            |
| CHARGING_PROCESS_ENERGY   | Wh   | energy       | total            |
| CHARGING_TIME             | s    | duration     | measurement      |
| EV_STATE_CODE             | –    | –            | –                |
| CP_STATE_CODE             | –    | –            | –                |
| PHASE_SWITCHING_MODE      | –    | –            | –                |
| LAST_RFID_CARD            | –    | –            | –                |
| SERIAL_NUMBER             | –    | –            | –                |
| FIRMWARE_VERSION          | –    | –            | –                |

Notes:

- `CONSUMED_ENERGY_TOTAL` is the cumulative lifetime counter of the wallbox and is suitable for the Home Assistant Energy Dashboard.
- `CONSUMED_ENERGY_ACTUAL` and `CHARGING_PROCESS_ENERGY` refer to the **current charging session** and are therefore classified as `total` (not `total_increasing`), as they reset with every new session.
- Multiple wallboxes are queried in parallel; the failure of a single wallbox does not prevent the remaining sensors from updating.

---

## Notes

- The integration works **locally** against the Beaam's internal API — no cloud connection required.
- Polling interval: **30 seconds** by default (configured in the `DataUpdateCoordinator`).
- For debugging in the Home Assistant log, you can enable the logger:

  ```yaml
  logger:
    default: info
    logs:
      custom_components.beaam: debug
  ```

---

## ToDo / future extensions

- Write access via POST to `things/{thingId}/commands`
- Support for additional thing types (BATTERY, PV, INVERTER, ELECTRICITY_METER_AC) analogous to the wallbox integration
- Configurable polling interval

---

## License

MIT

## Disclaimer

I am in no way affiliated with NEOOM; this is a purely private development project without commercial intent.
