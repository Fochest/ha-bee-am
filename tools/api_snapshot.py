#!/usr/bin/env python3
"""Record and compare the shape of the Beaam local API across firmware versions.

The integration discovers everything at runtime, so a firmware update never
crashes it — it just silently stops creating entities whose keys disappeared.
This tool makes that visible before users notice.

    # take a snapshot of the API as it is served right now
    python tools/api_snapshot.py capture --ip 192.168.1.50 -o tools/baselines/api-2.13.0.json

    # after a firmware update: capture again, then diff against every kept baseline
    python tools/api_snapshot.py capture --ip 192.168.1.50 -o /tmp/new.json
    python tools/api_snapshot.py compare tools/baselines /tmp/new.json

Versions are read from the device, so baselines are self-describing: the API
contract version comes from the OpenAPI document at http://<beaam>/api-json,
the OS/firmware numbers from the admin backend. `--label` adds a free-text note.
Each capture also archives the full OpenAPI document as `<output>.openapi.json`,
which is what pins the complete datapoint vocabulary of that version. Passing a
directory to `compare` checks a candidate against every kept baseline at once.

`capture` records only the *shape*: endpoint status codes, datapoint keys, the
`dataType`/`unitOfMeasure`/`controllable` NEOOM declares for them, and the JSON
type of each state value. It deliberately stores no measurements, no thing IDs,
no site ID and no geo coordinates, so a baseline is safe to commit.

`compare` classifies every difference as BREAKING, WARN or INFO. BREAKING means
something the integration actually consumes vanished or changed type — the keys
are read straight out of `custom_components/beaam/`, so this check follows the
code instead of duplicating its key lists. Exit code is 1 if anything BREAKING
is found, 0 otherwise.

The API token is read from --token or the BEAAM_TOKEN environment variable and
is never written to the snapshot.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

SNAPSHOT_SCHEMA = 1

COMPONENT_DIR = pathlib.Path(__file__).resolve().parent.parent / "custom_components" / "beaam"

SITE_STATE = "/api/v1/site/state"
SITE_CONFIGURATION = "/api/v1/site/configuration"
THING_STATES = "/api/v1/things/{thing_id}/states"
THING_SETTINGS = "/api/v1/things/{thing_id}/settings"

# Not part of the documented local API: the admin UI's own backend, which is
# where the Beaam reports its version numbers ("System information" in the UI).
# Captured so a snapshot says for itself which software served it.
DEVICE_VERSIONS = "/api-internal/device/versions"

# The OpenAPI document behind the Swagger UI at http://<beaam>/api/. Its
# info.version is the API contract version (e.g. 2.13.0) and is the most
# meaningful thing to pin a baseline to.
OPENAPI = "/api-json"

# Operations the integration actually calls. Losing one of these from the spec
# is a breaking change even if every datapoint key survived.
USED_OPERATIONS = {
    "GET /api/v1/site/state",
    "GET /api/v1/site/configuration",
    "GET /api/v1/things/{thingId}/states",
    "GET /api/v1/things/{thingId}/settings",
    "PUT /api/v1/things/{thingId}/settings",
}

# Thing type the integration discovers and builds entities for. A firmware that
# stops reporting it takes the whole wallbox device with it.
CRITICAL_THING_TYPE = "CHARGING_POINT_AC"


# --------------------------------------------------------------------------
# reading the integration's own key lists
# --------------------------------------------------------------------------


def _module_tree(name: str) -> ast.Module:
    return ast.parse((COMPONENT_DIR / name).read_text(encoding="utf-8"))


def _literal_names(tree: ast.Module, variable: str) -> set[str]:
    """Collect the string literals assigned to `variable` as a dict's keys or a set.

    Parsed rather than imported: sensor.py imports homeassistant, which is not
    available outside a Home Assistant environment.
    """
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(t, ast.Name) and t.id == variable for t in node.targets):
            continue
        value = node.value
        if isinstance(value, ast.Dict):
            return {k.value for k in value.keys if isinstance(k, ast.Constant)}
        if isinstance(value, (ast.Set, ast.List, ast.Tuple)):
            return {e.value for e in value.elts if isinstance(e, ast.Constant)}
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            return {value.value}
    return set()


def consumed_keys() -> dict[str, set[str]]:
    """Keys the integration turns into entities, grouped by where they live."""
    sensor = _module_tree("sensor.py")
    const = _module_tree("const.py")

    site = _literal_names(sensor, "SENSOR_DEFINITIONS")
    site |= _literal_names(const, "SITE_CONNECTIVITY_KEYS")

    states = _literal_names(sensor, "CHARGING_POINT_SENSOR_DEFINITIONS")
    states |= _literal_names(const, "CHARGING_POINT_CONNECTIVITY_KEY")

    return {
        "energy_flow": site,
        "thing_states": states,
        "thing_settings": _literal_names(const, "CHARGING_MODE_SETTING"),
    }


def prefix_fallback_covers(key: str) -> bool:
    """Whether sensor.py can infer a unit for an unmapped key (see BeaamSensor)."""
    return key.startswith(("POWER_", "ENERGY_", "FRACTION_"))


# --------------------------------------------------------------------------
# capture
# --------------------------------------------------------------------------


def _value_type(value) -> str | None:
    if value is None:
        return None  # NEOOM reports null for absent categories; type unknown
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    return type(value).__name__


class Client:
    def __init__(self, ip: str, token: str, timeout: int = 15):
        self._base = f"http://{ip}"
        self._token = token
        self._timeout = timeout

    def get(self, path: str) -> tuple[int, object]:
        request = urllib.request.Request(
            f"{self._base}{path}",
            headers={"Authorization": f"Bearer {self._token}"},
        )
        try:
            with urllib.request.urlopen(request, timeout=self._timeout) as response:
                body = response.read().decode("utf-8")
                status = response.status
        except urllib.error.HTTPError as err:
            return err.code, None
        except (urllib.error.URLError, TimeoutError) as err:
            raise SystemExit(f"cannot reach {self._base}{path}: {err}") from err
        try:
            return status, json.loads(body)
        except json.JSONDecodeError:
            return status, None


def _states_shape(payload: object, collection: str) -> dict[str, dict]:
    """Reduce a `{"states": [{"key","value"}]}` payload to key -> type info."""
    shape: dict[str, dict] = {}
    if not isinstance(payload, dict):
        return shape
    for entry in payload.get(collection, []) or []:
        key = entry.get("key")
        if not key:
            continue
        value_type = _value_type(entry.get("value"))
        existing = shape.get(key)
        if existing and existing["value_type"] is None:
            existing["value_type"] = value_type
        elif existing:
            existing["nullable"] = existing["nullable"] or value_type is None
        else:
            shape[key] = {"value_type": value_type, "nullable": value_type is None}
    return shape


def _declared(datapoints: object) -> dict[str, dict]:
    """Reduce a configuration `dataPoints` object to key -> declared metadata.

    The datapoint UUIDs are dropped; only the keys carry meaning across sites.
    """
    declared: dict[str, dict] = {}
    if not isinstance(datapoints, dict):
        return declared
    for definition in datapoints.values():
        key = definition.get("key")
        if not key:
            continue
        declared[key] = {
            "dataType": definition.get("dataType"),
            "unitOfMeasure": definition.get("unitOfMeasure"),
            "controllable": definition.get("controllable"),
        }
    return declared


def _operations(spec: object) -> list[str]:
    """"METHOD path" for every operation the OpenAPI document declares."""
    if not isinstance(spec, dict):
        return []
    methods = ("get", "put", "post", "patch", "delete", "head", "options")
    found = []
    for path, item in (spec.get("paths") or {}).items():
        if not isinstance(item, dict):
            continue
        for method in item:
            if method.lower() in methods:
                found.append(f"{method.upper()} {path}")
    return sorted(found)


def _key_enum(spec: object, schema: str) -> list[str]:
    """The `key` enum of a component schema: the vocabulary the firmware knows.

    The spec enumerates every key the software supports, while
    /site/configuration only reports the ones a given site actually has — the
    two together separate "NEOOM added a key" from "my site gained a device".
    """
    if not isinstance(spec, dict):
        return []
    schemas = (spec.get("components") or {}).get("schemas") or {}
    properties = (schemas.get(schema) or {}).get("properties") or {}
    return sorted((properties.get("key") or {}).get("enum") or [])


def capture(ip: str, token: str, label: str | None = None) -> tuple[dict, object]:
    client = Client(ip, token)
    endpoints: dict[str, int] = {}

    status, versions = client.get(DEVICE_VERSIONS)
    endpoints[DEVICE_VERSIONS] = status
    if not isinstance(versions, dict):
        versions = {}

    status, spec = client.get(OPENAPI)
    endpoints[OPENAPI] = status
    info = (spec or {}).get("info", {}) if isinstance(spec, dict) else {}

    status, state = client.get(SITE_STATE)
    endpoints[SITE_STATE] = status
    status, config = client.get(SITE_CONFIGURATION)
    endpoints[SITE_CONFIGURATION] = status

    energy_flow = _states_shape(
        (state or {}).get("energyFlow", {}) if isinstance(state, dict) else {},
        "states",
    )
    declared_flow = _declared(
        ((config or {}).get("energyFlow", {}) or {}).get("dataPoints")
        if isinstance(config, dict)
        else None
    )
    for key, meta in energy_flow.items():
        meta.update(declared_flow.get(key, {}))
    # keys NEOOM declares but does not currently report
    for key, meta in declared_flow.items():
        if key not in energy_flow:
            energy_flow[key] = {"value_type": None, "nullable": True, "declared_only": True, **meta}

    things = (config or {}).get("things", {}) if isinstance(config, dict) else {}
    by_type: dict[str, dict] = {}
    for thing_id, thing in (things or {}).items():
        thing_type = thing.get("type") or "UNKNOWN"
        bucket = by_type.setdefault(
            thing_type, {"count": 0, "declared": {}, "states": {}, "settings": {}}
        )
        bucket["count"] += 1
        bucket["declared"].update(_declared(thing.get("dataPoints")))

        states_path = THING_STATES.format(thing_id=thing_id)
        settings_path = THING_SETTINGS.format(thing_id=thing_id)
        status, payload = client.get(states_path)
        endpoints.setdefault(THING_STATES, status)
        for key, meta in _states_shape(payload, "states").items():
            bucket["states"].setdefault(key, meta)
        status, payload = client.get(settings_path)
        endpoints.setdefault(THING_SETTINGS, status)
        for key, meta in _states_shape(payload, "settings").items():
            bucket["settings"].setdefault(key, meta)

    for bucket in by_type.values():
        for key, meta in bucket["declared"].items():
            bucket["states"].setdefault(key, {"value_type": None, "nullable": True})
            bucket["states"][key].update(meta)
        del bucket["declared"]

    snapshot = {
        "snapshot_schema": SNAPSHOT_SCHEMA,
        # The API's own contract version, straight out of the OpenAPI document.
        "api": {
            "version": info.get("version"),
            "title": info.get("title"),
            "openapi": (spec or {}).get("openapi") if isinstance(spec, dict) else None,
            "operations": _operations(spec),
            # size of the datapoint vocabulary; the full lists live in the
            # archived OpenAPI document next to this snapshot
            "datapoint_keys": len(_key_enum(spec, "DataPoint")),
            "command_keys": len(_key_enum(spec, "CommandDto")),
            # small enough to keep inline, and it is the writable surface the
            # charging-mode select depends on
            "setting_keys": _key_enum(spec, "SettingDto"),
        },
        # What the device reports about itself. Note that these numbers are not
        # the "BEAAM Software" version series used by NEOOM's public changelog.
        "versions": versions,
        "label": label,
        "endpoints": endpoints,
        "energy_flow": dict(sorted(energy_flow.items())),
        "thing_types": {
            thing_type: {
                "count": bucket["count"],
                "states": dict(sorted(bucket["states"].items())),
                "settings": dict(sorted(bucket["settings"].items())),
            }
            for thing_type, bucket in sorted(by_type.items())
        },
    }
    return snapshot, spec


# --------------------------------------------------------------------------
# compare
# --------------------------------------------------------------------------


class Report:
    def __init__(self) -> None:
        self.findings: list[tuple[str, str]] = []

    def add(self, level: str, message: str) -> None:
        self.findings.append((level, message))

    @property
    def breaking(self) -> int:
        return sum(1 for level, _ in self.findings if level == "BREAKING")

    def render(self) -> str:
        if not self.findings:
            return "No differences in the API surface."
        order = {"BREAKING": 0, "WARN": 1, "INFO": 2}
        lines = []
        for level, message in sorted(self.findings, key=lambda f: order[f[0]]):
            lines.append(f"[{level:8}] {message}")
        return "\n".join(lines)


def _compare_keys(
    report: Report,
    where: str,
    old: dict[str, dict],
    new: dict[str, dict],
    consumed: set[str],
) -> None:
    for key, before in old.items():
        after = new.get(key)
        used = key in consumed or prefix_fallback_covers(key)
        if after is None:
            level = "BREAKING" if key in consumed else "WARN"
            note = "" if key in consumed else " (no entity was built from it)"
            report.add(level, f"{where}: key {key} disappeared{note}")
            continue
        old_type, new_type = before.get("value_type"), after.get("value_type")
        if old_type and new_type and old_type != new_type:
            report.add(
                "BREAKING" if used else "WARN",
                f"{where}: key {key} changed value type {old_type} -> {new_type}",
            )
        old_unit, new_unit = before.get("unitOfMeasure"), after.get("unitOfMeasure")
        if old_unit != new_unit and (old_unit or new_unit):
            report.add(
                "BREAKING" if used else "WARN",
                f"{where}: key {key} changed unitOfMeasure {old_unit} -> {new_unit}",
            )
        if before.get("controllable") != after.get("controllable"):
            report.add(
                "INFO",
                f"{where}: key {key} controllable "
                f"{before.get('controllable')} -> {after.get('controllable')}",
            )

    for key in new.keys() - old.keys():
        if key in consumed:
            hint = "already mapped in the integration"
        elif prefix_fallback_covers(key):
            hint = "picked up by the POWER_/ENERGY_/FRACTION_ fallback"
        else:
            hint = "would be created disabled-by-default; consider mapping it"
        report.add("INFO", f"{where}: new key {key} ({hint})")


def describe(snapshot: dict) -> str:
    """Short human label for a snapshot: API version, device version, free text."""
    versions = snapshot.get("versions") or {}
    api = snapshot.get("api") or {}
    parts = [
        f"API {api['version']}" if api.get("version") else None,
        versions.get("currentNtuityOs"),
        f"firmware {versions['firmware']}" if versions.get("firmware") else None,
        snapshot.get("label"),
    ]
    return " / ".join(p for p in parts if p) or "unlabelled snapshot"


def compare(old: dict, new: dict) -> Report:
    report = Report()
    consumed = consumed_keys()

    old_versions = old.get("versions") or {}
    new_versions = new.get("versions") or {}
    for field in sorted(set(old_versions) | set(new_versions)):
        before, after = old_versions.get(field), new_versions.get(field)
        if before != after:
            report.add("INFO", f"version {field}: {before} -> {after}")

    old_api = old.get("api") or {}
    new_api = new.get("api") or {}
    if old_api.get("version") != new_api.get("version"):
        report.add(
            "INFO",
            f"API version: {old_api.get('version')} -> {new_api.get('version')}",
        )
    old_ops = set(old_api.get("operations") or [])
    new_ops = set(new_api.get("operations") or [])
    if old_ops and not new_ops:
        report.add("WARN", "candidate snapshot has no OpenAPI operations to compare")
    elif old_ops or new_ops:
        for operation in sorted(old_ops - new_ops):
            report.add(
                "BREAKING" if operation in USED_OPERATIONS else "WARN",
                f"OpenAPI: operation {operation} is gone",
            )
        for operation in sorted(new_ops - old_ops):
            report.add("INFO", f"OpenAPI: new operation {operation}")

    for field in ("datapoint_keys", "command_keys"):
        before, after = old_api.get(field), new_api.get(field)
        if before is not None and after is not None and before != after:
            report.add("INFO", f"OpenAPI: {field} vocabulary {before} -> {after}")

    old_settings = set(old_api.get("setting_keys") or [])
    new_settings = set(new_api.get("setting_keys") or [])
    if old_settings or new_settings:
        writable = consumed["thing_settings"]
        for key in sorted(old_settings - new_settings):
            report.add(
                "BREAKING" if key in writable else "WARN",
                f"OpenAPI: setting key {key} is no longer declared",
            )
        for key in sorted(new_settings - old_settings):
            report.add("INFO", f"OpenAPI: new setting key {key}")

    if old.get("snapshot_schema") != new.get("snapshot_schema"):
        report.add(
            "WARN",
            f"snapshot schema differs ({old.get('snapshot_schema')} vs "
            f"{new.get('snapshot_schema')}); recapture the baseline",
        )

    for path, status in old.get("endpoints", {}).items():
        new_status = new.get("endpoints", {}).get(path)
        if status == 200 and new_status != 200:
            report.add("BREAKING", f"endpoint {path} was 200, now {new_status}")
        elif status != new_status:
            report.add("INFO", f"endpoint {path} status {status} -> {new_status}")

    _compare_keys(
        report,
        "energyFlow",
        old.get("energy_flow", {}),
        new.get("energy_flow", {}),
        consumed["energy_flow"],
    )

    old_types = old.get("thing_types", {})
    new_types = new.get("thing_types", {})
    for thing_type, before in old_types.items():
        after = new_types.get(thing_type)
        if after is None:
            level = "BREAKING" if thing_type == CRITICAL_THING_TYPE else "WARN"
            report.add(level, f"thing type {thing_type} is no longer reported")
            continue
        is_critical = thing_type == CRITICAL_THING_TYPE
        _compare_keys(
            report,
            f"{thing_type}.states",
            before.get("states", {}),
            after.get("states", {}),
            consumed["thing_states"] if is_critical else set(),
        )
        _compare_keys(
            report,
            f"{thing_type}.settings",
            before.get("settings", {}),
            after.get("settings", {}),
            consumed["thing_settings"] if is_critical else set(),
        )
    for thing_type in new_types.keys() - old_types.keys():
        report.add("INFO", f"new thing type {thing_type} appeared")

    return report


# --------------------------------------------------------------------------
# cli
# --------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    grab = sub.add_parser("capture", help="record the API surface of a live Beaam")
    grab.add_argument("--ip", required=True, help="Beaam IP address")
    grab.add_argument("--token", default=os.environ.get("BEAAM_TOKEN"))
    grab.add_argument(
        "--label",
        help="optional free-text note, e.g. the version the neoom app displays",
    )
    grab.add_argument("-o", "--output", required=True, help="snapshot file to write")
    grab.add_argument(
        "--no-spec",
        action="store_true",
        help="do not archive the raw OpenAPI document next to the snapshot",
    )

    diff = sub.add_parser("compare", help="diff two snapshots")
    diff.add_argument(
        "baseline",
        help="a snapshot file, or a directory of snapshots to check against all of them",
    )
    diff.add_argument("candidate")

    args = parser.parse_args(argv)

    if args.command == "capture":
        if not args.token:
            parser.error("no token: pass --token or set BEAAM_TOKEN")
        snapshot, spec = capture(args.ip, args.token, args.label)
        path = pathlib.Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(snapshot, indent=2, sort_keys=False) + "\n", encoding="utf-8")
        flow = len(snapshot["energy_flow"])
        types = len(snapshot["thing_types"])
        print(
            f"wrote {path} - {describe(snapshot)}, "
            f"{flow} energyFlow keys, {types} thing types"
        )
        if spec is not None and not args.no_spec:
            spec_path = path.with_suffix(".openapi.json")
            spec_path.write_text(
                json.dumps(spec, indent=2, sort_keys=False) + "\n", encoding="utf-8"
            )
            print(f"wrote {spec_path} - full OpenAPI document for this version")
        return 0

    candidate = json.loads(pathlib.Path(args.candidate).read_text(encoding="utf-8"))
    baseline_path = pathlib.Path(args.baseline)
    if baseline_path.is_dir():
        # the archived OpenAPI documents live alongside the snapshots
        baselines = sorted(
            p for p in baseline_path.glob("*.json") if not p.name.endswith(".openapi.json")
        )
        if not baselines:
            parser.error(f"no snapshots in {baseline_path}")
    else:
        baselines = [baseline_path]

    breaking = 0
    for index, path in enumerate(baselines):
        baseline = json.loads(path.read_text(encoding="utf-8"))
        report = compare(baseline, candidate)
        breaking += report.breaking
        if index:
            print()
        print(f"=== {describe(baseline)}  ->  {describe(candidate)} ===")
        print(report.render())

    if len(baselines) > 1:
        print(
            f"\n{len(baselines)} baselines checked, "
            f"{breaking} breaking difference(s) in total"
        )
    return 1 if breaking else 0


if __name__ == "__main__":
    sys.exit(main())
