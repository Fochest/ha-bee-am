# Home Assistant Custom Integration – BEAAM API

***English** • [Deutsch](README.md)*

This Home Assistant custom integration connects to the **internal Beaam API**. (https://developer.neoom.com/reference/concepts-terms-1)

It exposes measurements such as power production, consumption, grid import/export, battery state of charge, and **fraction values (e.g. PV → storage, PV → grid)** as Home Assistant sensors.

All sensors now also provide the `state_class` attribute so that they are evaluated correctly in Home Assistant dashboards.

> **Compatibility** (as of 2026-08-05): successfully tested against local **BEAAM API `2.13.0`** — the `info.version` of the OpenAPI document at `http://<beaam>/api-json`; the device reported NTUITY OS `v1.17.0-build3919` and firmware `1.36.0`.
>
> There is **no known minimum software version.** The integration only creates entities for keys the API actually returns — a missing key means a missing entity, not an error. Only **writing** (the charging-mode select) needs software that supports `PUT /things/{thingId}/settings`; NEOOM introduced that in **BEAAM software 1.77** according to the changelog. Without it you simply lose the select, the sensors keep working.
>
> Careful with version numbers: the "BEAAM Software" series in NEOOM's changelog (1.7x) is **not** the same numbering as the locally reported NTUITY OS or API version.

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
- `GET http://{beaamIp}/api/v1/things/{thingId}/settings`  
  → returns a thing's settings (including the charging mode `OPERATING_MODE_EMS`)
- `PUT http://{beaamIp}/api/v1/things/{thingId}/settings`  
  → writes settings (used to switch the wallbox charging mode)

---

## Sensors & units

The main sensors automatically receive **units**, **device classes**, and **state_class** so they are visualised correctly in Home Assistant:

| Key                             | Unit | Device Class | state_class |
|---------------------------------|------|--------------|-------------|
| POWER_PRODUCTION                | W    | power        | measurement |
| POWER_CONSUMPTION                | W    | power        | measurement |
| POWER_CONSUMPTION_CALC          | W    | power        | measurement |
| POWER_APPLIANCES                | W    | power        | measurement |
| POWER_CHARGING_STATIONS         | W    | power        | measurement |
| POWER_HEATING                   | W    | power        | measurement |
| POWER_GRID                      | W    | power        | measurement |
| POWER_GRID_REMAINING            | W    | power        | measurement |
| POWER_STORAGE                   | W    | power        | measurement |
| MAX_NETWORK_UTILIZATION         | W    | power        | measurement |
| ENERGY_PRODUCED                 | Wh   | energy       | total_increasing |
| ENERGY_CONSUMED                 | Wh   | energy       | total_increasing |
| ENERGY_CONSUMED_CALC            | Wh   | energy       | total_increasing |
| ENERGY_APPLIANCES               | Wh   | energy       | total_increasing |
| ENERGY_CHARGING_STATIONS        | Wh   | energy       | total_increasing |
| ENERGY_HEATING                  | Wh   | energy       | total_increasing |
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

Notes on consumption:

- `POWER_CONSUMPTION_CALC` / `ENERGY_CONSUMED_CALC` are the **calculated total consumption** for sites without a dedicated consumption meter. With a meter installed NEOOM sends `POWER_CONSUMPTION` / `ENERGY_CONSUMED` (measured) instead. Use these for whole-home consumption.
- `POWER_APPLIANCES` is, per NEOOM, a **residual**: total consumption minus all other sub-consumers (`POWER_CHARGING_STATIONS`, `POWER_HEATING`, …). Do *not* use it as total consumption.
- Keys not explicitly mapped are given W/Wh automatically based on their `POWER_*`/`ENERGY_*` prefix. Keys without a known prefix (e.g. plain status strings) are created **disabled by default** so they don't clutter the activity stream — enable them manually in Home Assistant if needed.
- `POWER_GRID_REMAINING` is the power headroom left at the grid connection. The corresponding limits come from `/site/configuration` under `siteInfo.gridConnections` (`maxPowerSupply` / `maxPowerFeedIn`). Sites for which NEOOM does not compute the value report `null`, leaving the sensor "unknown".

---

## Reachability (binary sensors)

For each device category NEOOM publishes a **BOOLEAN flag** in `energyFlow` indicating whether the Beaam currently reaches the things of that class. These keys are created as `binary_sensor` entities with `device_class: connectivity` (and therefore *no longer* as plain sensors):

| Key                     | Meaning                        |
|-------------------------|--------------------------------|
| PRODUCERS_ONLINE        | producers (PV) reachable        |
| STORAGES_ONLINE         | storage/battery reachable       |
| GRID_METERS_ONLINE      | grid meters reachable           |
| CHARGING_POINTS_ONLINE  | charging points reachable       |
| HEATING_ONLINE          | heating reachable               |

In addition, every wallbox gets a `binary_sensor` from its **`CONNECTION`** state — whether the Beaam reaches the station itself.

Notes:

- If a category does not exist in the site (e.g. no heating), NEOOM reports `null`. The binary sensor deliberately stays **"unknown"** instead of being flattened to "disconnected", which would make an absent category look like a fault.
- `CHARGING_POINTS_ONLINE` and `CONNECTION` are independent of `CP_STATE_CODE`: a station can be reachable (`true`) while reporting itself as `UNAVAILABLE`. Use the connectivity flag for outage alerts and `CP_STATE_CODE` for charging state.
- **Upgrading from ≤ 0.5.0:** the `*_ONLINE` keys used to be created as (disabled-by-default) plain sensors. After the update they appear as binary sensors; the old disabled `sensor.*` entries remain as registry leftovers and can be deleted.

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
| ERROR_CODES               | –    | –            | – (diagnostic)   |

Notes:

- `CONSUMED_ENERGY_TOTAL` is the cumulative lifetime counter of the wallbox and is suitable for the Home Assistant Energy Dashboard.
- `ERROR_CODES` is delivered as a string array. Because a Home Assistant state must be scalar, multiple codes are joined with commas and an empty list is reported as **`OK`**. The entity is categorised as **diagnostic**.
- `SERIAL_NUMBER` and `FIRMWARE_VERSION` may stay empty if the Beaam never received them from the station — even when `CONNECTION` reports `true`.
- `CONSUMED_ENERGY_ACTUAL` and `CHARGING_PROCESS_ENERGY` refer to the **current charging session** and are therefore classified as `total` (not `total_increasing`), as they reset with every new session.
- Multiple wallboxes are queried in parallel; the failure of a single wallbox does not prevent the remaining sensors from updating.

### Switch charging mode (select)

For every wallbox that exposes the `OPERATING_MODE_EMS` setting, a **`select` entity "Lademodus" (charging mode)** is created as well. It lets you switch the charging mode straight from Home Assistant (writes via `PUT /things/{thingId}/settings`):

| Option    | `OPERATING_MODE_EMS` |
|-----------|----------------------|
| Solar     | `EXCESS_CONSUMPTION` |
| Schnell   | `FAST_CHARGING`      |

- **Solar** charges from PV surplus, **Schnell** (fast) charges at full power.
- If the wallbox reports an unknown mode value, it is shown as an additional (raw) option so the current state is always represented correctly.
- After switching, the coordinator refreshes immediately so the new mode appears without waiting for the polling interval.

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

## Pinning the API surface and checking updates (`tools/api_snapshot.py`)

Because the integration discovers everything at runtime, a firmware update never crashes it — it just silently stops creating an entity whose key disappeared. `tools/api_snapshot.py` makes that visible before users notice:

```bash
# record the surface of the software running right now
BEAAM_TOKEN=sk_beaam_… python tools/api_snapshot.py capture \
    --ip 192.168.1.50 -o tools/baselines/api-2.13.0.json

# after an update: capture again and check against every kept baseline
BEAAM_TOKEN=sk_beaam_… python tools/api_snapshot.py capture --ip 192.168.1.50 -o /tmp/new.json
python tools/api_snapshot.py compare tools/baselines /tmp/new.json
```

`capture` writes two files: the snapshot (endpoint status, datapoint keys with `dataType`/`unitOfMeasure`/`controllable`, JSON type of each value) and, next to it, the full OpenAPI document as `*.openapi.json`, which pins the complete datapoint vocabulary of that version. Measurements, thing IDs, the site ID and geo coordinates are deliberately **not** stored, so baselines can be committed.

`compare` classifies every difference:

- **BREAKING** — something the integration actually uses vanished or changed type (including a used OpenAPI operation going missing). Exit code 1.
- **WARN** — a key or thing type disappeared that no entity was built from.
- **INFO** — new keys, version bumps, changed `controllable` flags. For new keys it also says whether the prefix fallback covers them or whether they would be created disabled and should be mapped.

The set of "actually used" keys is read out of `custom_components/beaam/` via AST rather than duplicated, so the check follows the code automatically. Several baselines in the directory are all checked against the candidate, which is how you test against multiple older versions.

---

## ToDo / future extensions

- Further write actions via `POST /things/{thingId}/commands` (e.g. charging power, start/stop). Note: per NEOOM, commands only apply to datapoints marked `"controllable": true` in `/site/configuration`. On a `CHARGING_POINT_AC` that may be limited to `MAX_POWER_CHARGE`, `MAX_POWER_CHARGE_FALLBACK` and `PHASE_SWITCHING_MODE` — commands such as `STATION_AVAILABILITY` or `ENABLE_CHARGING` exist in the API enum but are not necessarily available on your own thing.
- Support for additional thing types (BATTERY, PV, INVERTER, ELECTRICITY_METER_AC) analogous to the wallbox integration
- Configurable polling interval

---

## License

MIT

## Disclaimer

I am in no way affiliated with NEOOM; this is a purely private development project without commercial intent.
