# Entwickler-Werkzeuge

Interner Kram für die Wartung der Integration. Für die Nutzung in Home Assistant ist hier nichts nötig — das Release-`beaam.zip` enthält dieses Verzeichnis nicht.

---

## Warum es das gibt

Die Integration entdeckt alles zur Laufzeit: sie legt Entitäten nur für Keys an, die die Beaam-API tatsächlich liefert. Ein Firmware-Update bringt sie deshalb nie zum Absturz — sie hört still auf, eine Entität anzulegen, deren Key verschwunden ist. Genau das ist der Fehlerfall, den niemand bemerkt, bis jemand ein fehlendes Diagramm meldet.

`api_snapshot.py` hält den API-Stand einer Version fest und vergleicht spätere Stände dagegen.

---

## Versionsnummern am Beaam

Es gibt **drei unabhängige Zählungen**, und sie passen absichtlich nicht zueinander. Stand 2026-08-05 an einer produktiven Anlage:

| Quelle | Feld | Wert |
|---|---|---|
| `GET /api-json` (OpenAPI hinter der Swagger-UI auf `/api/`) | `info.version` | **API `2.13.0`** |
| `GET /api-internal/device/versions` | `currentNtuityOs` | `v1.17.0-build3919` |
| dieselbe | `localConfigServer` / `firmware` | `1.17.0` / `1.36.0` |
| neoom-App / Portal | „BEAAM Software" | `v1.78.0-build8959` |

**Nicht gleichsetzen:** die im [neoom-Changelog](https://wissen.neoom.com/changelog-beaam-software) geführte Reihe `1.7x` ist nicht dieselbe Zählung wie das lokal gemeldete NTUITY OS `1.17.x`.

In der Beaam-UI stehen die Werte unter **„Systeminformationen"**. Wer den Endpunkt dahinter sucht: die Admin-SPA spricht ihr Backend über `baseURL: "../api-internal/"` an (im Bundle `/static/js/main.*.js` nach `baseURL` greppen). Client-Routen wie `/device/versions` direkt aufzurufen liefert nur die SPA-Hülle, weil der Express-Catch-all mit `200` und HTML antwortet.

Für Kompatibilitätsfragen ist die **OpenAPI-Spec** die beste Quelle: sie enumeriert alle Datenpunkt-Keys, die die Firmware kennt (aktuell 242 in `DataPoint`/`DataPointState`/`CommandDto`, 14 schreibbare in `SettingDto`) — unabhängig davon, welche davon eine konkrete Anlage liefert.

---

## `api_snapshot.py`

```bash
# Stand der laufenden Software festhalten
BEAAM_TOKEN=sk_beaam_… python tools/api_snapshot.py capture \
    --ip 192.168.1.50 -o tools/baselines/api-2.13.0.json

# nach einem Update: neu aufnehmen und gegen alle vorgehaltenen Stände prüfen
BEAAM_TOKEN=sk_beaam_… python tools/api_snapshot.py capture --ip 192.168.1.50 -o /tmp/neu.json
python tools/api_snapshot.py compare tools/baselines /tmp/neu.json
```

Kein `pip install` nötig, nur die Standardbibliothek. Der Token kommt aus `--token` oder `BEAAM_TOKEN` und landet nie im Snapshot.

### `capture`

Schreibt zwei Dateien:

- **den Snapshot** — Endpunkt-Statuscodes, Datenpunkt-Keys mit dem von NEOOM deklarierten `dataType`/`unitOfMeasure`/`controllable`, der JSON-Typ jedes Werts, die API-Version und die Geräteversionen.
- **das vollständige OpenAPI-Dokument** daneben als `<name>.openapi.json`. Das ist das eigentliche Archiv: es hält die komplette Datenpunkt-Sprache dieser Version fest, auch die Keys, die die eigene Anlage nie liefert.

Absichtlich **nicht** gespeichert: Messwerte, Thing-IDs, Site-ID, Geokoordinaten, Seriennummern. Baselines sind damit committebar. Wer eine eigene Baseline beisteuert, sollte das vor dem Commit stichprobenartig prüfen.

### `compare`

Stuft jeden Unterschied ein:

| Stufe | Bedeutung |
|---|---|
| **BREAKING** | etwas, das die Integration wirklich benutzt, ist weg oder hat den Typ gewechselt — auch eine fehlende OpenAPI-Operation oder ein nicht mehr deklarierter Setting-Key. Exit-Code 1. |
| **WARN** | ein Key oder Thing-Typ ist verschwunden, aus dem keine Entität gebaut wurde. |
| **INFO** | neue Keys, Versionssprünge, geänderte `controllable`-Flags, gewachsenes Vokabular. |

Bei neuen Keys steht dabei, ob die `POWER_`/`ENERGY_`/`FRACTION_`-Prefix-Regel sie auffängt oder ob sie deaktiviert angelegt würden und gemappt werden sollten.

Welche Keys als „wirklich benutzt" gelten, liest das Skript **per AST aus `custom_components/beaam/`** (`SENSOR_DEFINITIONS`, `CHARGING_POINT_SENSOR_DEFINITIONS`, `SITE_CONNECTIVITY_KEYS`, `CHARGING_MODE_SETTING`) statt aus einer zweiten Liste. Die Prüfung folgt damit automatisch dem Code; per Import geht es nicht, weil `sensor.py` `homeassistant` braucht.

Zeigt man `compare` auf das Verzeichnis statt auf eine Datei, wird der Kandidat gegen **jede** vorgehaltene Baseline geprüft.

---

## `baselines/`

Eine Baseline pro API-Version, benannt nach `info.version`, plus das zugehörige `*.openapi.json`. Bestehende Dateien werden nicht überschrieben, wenn eine neue Version dazukommt — der Sinn ist, gegen mehrere ältere Stände testen zu können.
