# Changelog

All notable changes to this integration. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), the versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Releases are cut by pushing a tag; note that the tag names carry a dot after the
`v` (`v.0.5.1`), which is this repository's convention.

## [Unreleased]

### Added

- Labels for the three `OPERATING_MODE_EMS` values the integration did not know:
  `GRIID_CONTROLLED` ("Intelligent"), `DEVICE_CONTROLLED` ("Ausgenommen") and
  `FLEXIBILITY_MARKETING` ("Flexibilitätsvermarktung"), so Home Assistant shows
  a proper label instead of the raw enum string when a wallbox is in one of them.

  None of the three is offered as a choice. "Intelligent" is NEOOM's CONNECT Ai
  mode and needs a CONNECT Mega or Giga subscription; the local API has no
  entitlement field, and a Beaam without the subscription accepts and keeps the
  value anyway (measured: `200`, held for five minutes, no server-side rollback),
  so there is nothing to react to and no way to know what such a station would
  do. A subscriber sets the mode once in the neoom app, after which the device
  reports it and it becomes selectable here. "Ausgenommen" would take the wallbox
  out of CONNECT's control entirely and "Flexibilitätsvermarktung" is not a
  charging mode.

  NEOOM documents none of these values in the API — `SettingDto` carries only
  `key` and `value`, and `value` is just `string|number|boolean`. The labels come
  from the CONNECT portal's translations under the key
  `OPERATING_MODE_EMS/values`.

  Note for when this ships: the select's state changes from the raw
  `GRIID_CONTROLLED` to `Intelligent` for anyone whose wallbox is in that mode,
  which affects templates or automations comparing against the raw string.

- `tools/api_snapshot.py`: record the shape of the Beaam local API for a given
  software version and diff later versions against it. `capture` stores endpoint
  status codes, datapoint keys with the `dataType`/`unitOfMeasure`/`controllable`
  NEOOM declares and the JSON type of each value, reads the API contract version
  from the OpenAPI document at `/api-json` and archives that document alongside
  the snapshot. `compare` grades every difference as BREAKING, WARN or INFO and
  exits non-zero on anything breaking. See [`tools/README.md`](tools/README.md).
- `tools/baselines/`: the first baseline, taken against BEAAM API `2.13.0`.

### Changed

- The compatibility note in the READMEs now states what actually matters to
  users: there is no known minimum Beaam software version, because a datapoint
  the API does not report simply yields no entity rather than an error. Only
  switching the charging mode needs software that can write settings (NEOOM
  introduced that in 1.77). The version details moved to `tools/README.md`.

### Fixed

- Selecting the mode the wallbox is already in was rejected with a log warning
  when that mode was one the integration did not know. The select now resolves
  any option it offers, mapped or raw.

## [0.5.1] - 2026-08-05

Verified against BEAAM API `2.13.0`; no endpoint or key the integration relies
on had changed. This release picks up the datapoints that were previously
unmapped or filtered out.

### Added

- `binary_sensor` platform with `device_class: connectivity` for the five
  BOOLEAN reachability flags NEOOM publishes in `energyFlow`
  (`PRODUCERS_ONLINE`, `STORAGES_ONLINE`, `GRID_METERS_ONLINE`,
  `CHARGING_POINTS_ONLINE`, `HEATING_ONLINE`), plus each charging point's own
  `CONNECTION` state.
- `ERROR_CODES` as a diagnostic sensor for each charging point. The API returns
  a string array, so the codes are joined and an empty list reads as `OK`.

### Changed

- `POWER_GRID_REMAINING` is mapped explicitly to W, confirmed against
  `/site/configuration`, instead of relying on the `POWER_` prefix fallback.
- Where a category does not exist in a site, NEOOM reports `null`; the
  connectivity sensors stay "unknown" rather than being flattened to
  "disconnected", so an absent category does not look like a fault.

### Upgrade note

The `*_ONLINE` keys used to be created as plain sensors, disabled by default.
They are now binary sensors, so the old `sensor.*_online` entries stay behind in
the entity registry as leftovers and can be deleted. Automations that had
manually enabled one of those sensors need to point at the binary sensor.

## [0.5.0] - 2026-07-23

### Added

- Mapped the remaining documented `energyFlow` keys: `POWER_CONSUMPTION`,
  `POWER_CHARGING_STATIONS`, `POWER_HEATING`, `MAX_NETWORK_UTILIZATION`,
  `ENERGY_CONSUMED`, `ENERGY_CHARGING_STATIONS`, `ENERGY_HEATING`.
- Prefix fallback in `BeaamSensor`: unmapped `POWER_*` keys get W with
  `device_class: power`, unmapped `ENERGY_*` keys get Wh with
  `state_class: total_increasing`. New NEOOM keys therefore arrive with a unit —
  and thus stay out of the logbook — without a code change.

## [0.4.5] - 2026-07-23

### Added

- Mapped `POWER_APPLIANCES` and `ENERGY_APPLIANCES`, which NEOOM had started
  emitting.

### Fixed

- Keys with no mapping were created as unitless sensors, which Home Assistant
  does not treat as continuous, so they cluttered the logbook and the activity
  stream. Unmapped keys are now created disabled by default.

## [0.4.4] - 2026-07-13

### Changed

- The charging-mode select is a `CoordinatorEntity` and updates optimistically,
  so the UI reflects a switch immediately instead of waiting for the next poll.
  A failed write reverts the optimistic value.

## [0.4.3] - 2026-07-13

### Added

- hassfest workflow, required for submission to the HACS default store.

### Changed

- Manifest keys sorted as hassfest expects (`domain`, `name`, then alphabetical).

## [0.4.2] - 2026-07-13

### Added

- Neutral local brand icon, included in the packaged zip, for the HACS brands
  check. Note that a local brand asset does not render an icon in the Home
  Assistant UI; that requires the home-assistant/brands repository.

## [0.4.1] - 2026-07-13

### Fixed

- `PUT /things/{thingId}/settings` answers `200` with a `text/plain` body of
  `OK`. Decoding that as JSON raised, which made every charging-mode switch look
  like a failure. The response is read as text now.

## [0.4.0] - 2026-07-13

### Added

- Charging-mode `select` per wallbox, writing the `OPERATING_MODE_EMS` setting:
  `EXCESS_CONSUMPTION` is offered as "Solar", `FAST_CHARGING` as "Schnell". An
  unknown value reported by the device is offered as an extra raw option so the
  current state is always representable.
- English README with a language switcher.

## [0.3.1] - 2026-04-22

### Added

- Release workflow packaging `custom_components/beaam/` into `beaam.zip` on tag
  push, so releases carry an installable asset.

## [0.3.0] - 2026-04-16

### Added

- Wallbox support: things of type `CHARGING_POINT_AC` are discovered through
  `/site/configuration` by their type, so no thing ID is configured anywhere, and
  each is exposed as its own Home Assistant device with power, current, voltage,
  energy, session and state sensors. Multiple wallboxes are polled in parallel
  and one failing does not stop the others.
- HACS validation workflow.

## [0.2.0] - 2025-09-19

### Added

- `state_class` on the sensors so Home Assistant accepts them for the energy
  dashboard and long-term statistics.

## [0.1.1] - 2025-09-19

### Changed

- Repository restructured to HACS layout and `hacs.json` added.

## [0.1.0] - 2025-09-19

### Added

- First release: sensors for the `energyFlow` datapoints of the local Beaam API
  with units and device classes, fraction values converted from decimal to
  percent, and a config flow taking the Beaam address and bearer token.

[Unreleased]: https://github.com/Fochest/ha-bee-am/compare/v.0.5.1...HEAD
[0.5.1]: https://github.com/Fochest/ha-bee-am/compare/v.0.5.0...v.0.5.1
[0.5.0]: https://github.com/Fochest/ha-bee-am/compare/v.0.4.5...v.0.5.0
[0.4.5]: https://github.com/Fochest/ha-bee-am/compare/v.0.4.4...v.0.4.5
[0.4.4]: https://github.com/Fochest/ha-bee-am/compare/v.0.4.3...v.0.4.4
[0.4.3]: https://github.com/Fochest/ha-bee-am/compare/v.0.4.2...v.0.4.3
[0.4.2]: https://github.com/Fochest/ha-bee-am/compare/v.0.4.1...v.0.4.2
[0.4.1]: https://github.com/Fochest/ha-bee-am/compare/v.0.4.0...v.0.4.1
[0.4.0]: https://github.com/Fochest/ha-bee-am/compare/v.0.3.1...v.0.4.0
[0.3.1]: https://github.com/Fochest/ha-bee-am/compare/v.0.3.0...v.0.3.1
[0.3.0]: https://github.com/Fochest/ha-bee-am/compare/v.0.2.0...v.0.3.0
[0.2.0]: https://github.com/Fochest/ha-bee-am/compare/v.0.1.1...v.0.2.0
[0.1.1]: https://github.com/Fochest/ha-bee-am/compare/v.0.1.0...v.0.1.1
[0.1.0]: https://github.com/Fochest/ha-bee-am/releases/tag/v.0.1.0
