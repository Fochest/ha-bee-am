# Home Assistant Custom Integration – BEAAM API

*[English](README.en.md) • **Deutsch***

Diese Home Assistant Custom-Integration bindet die **interne Beaam API** an.  (https://developer.neoom.com/reference/concepts-terms-1)

Es werden Messwerte wie Stromproduktion, Verbrauch, Netzbezug, Speicherzustand sowie **Fraktionswerte (z. B. PV → Speicher, PV → Netz)** als Sensoren in Home Assistant verfügbar gemacht.

Alle Sensoren unterstützen nun zusätzlich das Attribut `state_class`, um korrekte Auswertungen in den Home Assistant Dashboards zu ermöglichen.

> **Kompatibilität:** Es gibt **keinen bekannten Mindest-Softwarestand** des Beaam. Die Integration legt Entitäten ausschließlich für Datenpunkte an, die deine Anlage tatsächlich liefert — fehlt einer, fehlt die Entität, es gibt keinen Fehler. Nur das **Umschalten des Lademodus** braucht eine Beaam-Software, die das Schreiben von Settings unterstützt (von NEOOM mit **1.77** eingeführt); fehlt es, entfällt lediglich der Select und die Sensoren laufen weiter. Zuletzt geprüft gegen BEAAM API `2.13.0` (Details und Prüfwerkzeug: [`tools/README.md`](tools/README.md)).

---

## Installation

Was sich je Version geändert hat, steht im [Changelog](CHANGELOG.md).

1. Lade das `beaam.zip` aus dem neuesten [Release](https://github.com/Fochest/ha-bee-am/releases/latest) herunter und entpacke es nach:

   ```
   config/custom_components/beaam/
   ```

   sodass folgende Struktur existiert:

   ```
   config/custom_components/beaam/__init__.py
   config/custom_components/beaam/manifest.json
   config/custom_components/beaam/sensor.py
   ...
   ```

2. Home Assistant neu starten.

3. Unter **Einstellungen → Geräte & Dienste → Integration hinzufügen** nach `Beaam` suchen.

---

## Konfiguration

Wie man den **Bearer Token** erstellt:
- Login unter https://connect.neoom.com/users/sign_in mit den Neoom Credentials.
- Lokalen Standort auswählen
- Im Menü unter **Zugriffsverwaltung** auf **API-Schlüssel** klicken
- Einen **Schlüssel für die BEAAM API** erstellen und sicher abspeichern. Dies ist der Bearer Token, den wir im nächsten Schritt benötigen.

Bei der Einrichtung im UI müssen folgende Parameter angegeben werden:

- **Beaam IP/Adresse** → z. B. `192.168.1.50`
- **Bearer Token** → API-Token für die Authentifizierung

Danach werden automatisch Sensoren für alle verfügbaren Datenpunkte angelegt.

---

## Unterstützte Endpunkte

Die Integration nutzt die folgenden REST-Endpunkte der Beaam-API:

- `GET http://{beaamIp}/api/v1/site/state`  
  → liefert aktuelle Energieflüsse und KPIs
- `GET http://{beaamIp}/api/v1/site/configuration`  
  → liefert Konfigurationsdaten der Site (wird u. a. zur automatischen Erkennung der Wallboxen genutzt)
- `GET http://{beaamIp}/api/v1/things/{thingId}/states`  
  → liefert Zustände einzelner Things (derzeit für `CHARGING_POINT_AC` genutzt)
- `GET http://{beaamIp}/api/v1/things/{thingId}/settings`  
  → liefert Einstellungen eines Things (u. a. den Lademodus `OPERATING_MODE_EMS`)
- `PUT http://{beaamIp}/api/v1/things/{thingId}/settings`  
  → schreibt Einstellungen (wird zum Umschalten des Wallbox-Lademodus genutzt)

---

## Sensoren & Einheiten

Die wichtigsten Sensoren erhalten automatisch **Einheiten**, **Device Classes** und **state_class**, damit sie in Home Assistant korrekt visualisiert werden:

| Key                             | Einheit | Device Class | state_class |
|---------------------------------|---------|--------------|-------------|
| POWER_PRODUCTION                | W       | power        | measurement |
| POWER_CONSUMPTION                | W       | power        | measurement |
| POWER_CONSUMPTION_CALC          | W       | power        | measurement |
| POWER_APPLIANCES                | W       | power        | measurement |
| POWER_CHARGING_STATIONS         | W       | power        | measurement |
| POWER_HEATING                   | W       | power        | measurement |
| POWER_GRID                      | W       | power        | measurement |
| POWER_GRID_REMAINING            | W       | power        | measurement |
| POWER_STORAGE                   | W       | power        | measurement |
| MAX_NETWORK_UTILIZATION         | W       | power        | measurement |
| ENERGY_PRODUCED                 | Wh      | energy       | total_increasing |
| ENERGY_CONSUMED                 | Wh      | energy       | total_increasing |
| ENERGY_CONSUMED_CALC            | Wh      | energy       | total_increasing |
| ENERGY_APPLIANCES               | Wh      | energy       | total_increasing |
| ENERGY_CHARGING_STATIONS        | Wh      | energy       | total_increasing |
| ENERGY_HEATING                  | Wh      | energy       | total_increasing |
| ENERGY_IMPORTED                 | Wh      | energy       | total_increasing |
| ENERGY_EXPORTED                 | Wh      | energy       | total_increasing |
| ENERGY_CHARGED                  | Wh      | energy       | total_increasing |
| ENERGY_DISCHARGED               | Wh      | energy       | total_increasing |
| STATE_OF_CHARGE                 | %       | battery      | measurement |
| SELF_SUFFICIENCY                | %       | –            | measurement |
| FRACTION_PV_TO_STORAGE          | %       | –            | measurement |
| FRACTION_PV_TO_GRID             | %       | –            | measurement |
| FRACTION_PV_TO_CONSUMPTION      | %       | –            | measurement |
| FRACTION_GRID_TO_STORAGE        | %       | –            | measurement |
| FRACTION_GRID_TO_CONSUMPTION    | %       | –            | measurement |
| FRACTION_STORAGE_TO_CONSUMPTION | %       | –            | measurement |
| FRACTION_STORAGE_TO_GRID        | %       | –            | measurement |

Alle **Fraction-Werte** werden automatisch von Dezimal (z. B. `0.1188`) in Prozent (z. B. `11.88 %`) umgerechnet.

Hinweise zum Verbrauch:

- `POWER_CONSUMPTION_CALC` / `ENERGY_CONSUMED_CALC` sind der **berechnete Gesamtverbrauch** für Sites ohne dedizierten Verbrauchszähler. Mit eigenem Zähler liefert NEOOM stattdessen `POWER_CONSUMPTION` / `ENERGY_CONSUMED` (gemessen). Für den Hausverbrauch diese Keys nutzen.
- `POWER_APPLIANCES` ist laut NEOOM ein **Residualwert**: Gesamtverbrauch minus alle anderen Unterverbraucher (`POWER_CHARGING_STATIONS`, `POWER_HEATING`, …). Also *nicht* als Gesamtverbrauch verwenden.
- Nicht explizit gemappte Keys bekommen anhand ihres `POWER_*`/`ENERGY_*`-Präfixes automatisch W bzw. Wh zugewiesen. Keys ohne bekanntes Präfix (z. B. reine Status-Strings) werden **standardmäßig deaktiviert** angelegt, damit sie den Aktivitätsstream nicht zumüllen — bei Bedarf in Home Assistant manuell aktivieren.
- `POWER_GRID_REMAINING` ist die verbleibende Leistungsreserve am Hausanschluss. Die zugehörigen Grenzwerte liefert `/site/configuration` unter `siteInfo.gridConnections` (`maxPowerSupply` / `maxPowerFeedIn`). Sites, für die NEOOM den Wert nicht berechnet, melden `null` — der Sensor steht dann auf „unbekannt".

---

## Erreichbarkeit (Binary Sensors)

NEOOM liefert im `energyFlow` je Gerätekategorie ein **BOOLEAN-Flag**, ob der Beaam die Things dieser Klasse gerade erreicht. Diese Keys werden als `binary_sensor` mit `device_class: connectivity` angelegt (und deshalb *nicht* mehr als normaler Sensor):

| Key                     | Bedeutung                                  |
|-------------------------|--------------------------------------------|
| PRODUCERS_ONLINE        | Erzeuger (PV) erreichbar                    |
| STORAGES_ONLINE         | Speicher/Batterie erreichbar                |
| GRID_METERS_ONLINE      | Netz-/Stromzähler erreichbar                |
| CHARGING_POINTS_ONLINE  | Ladepunkte erreichbar                       |
| HEATING_ONLINE          | Heizung erreichbar                          |

Zusätzlich bekommt jede Wallbox einen `binary_sensor` aus ihrem State **`CONNECTION`** — ob der Beaam die Station selbst erreicht.

Hinweise:

- Existiert in der Site keine Kategorie (z. B. keine Heizung), meldet NEOOM `null`. Der Binary Sensor bleibt dann bewusst auf **„unbekannt"** und wird nicht auf „getrennt" abgeflacht — sonst würde eine nicht vorhandene Kategorie als Störung aussehen.
- `CHARGING_POINTS_ONLINE` bzw. `CONNECTION` sind unabhängig von `CP_STATE_CODE`: eine Station kann erreichbar (`true`) sein und sich gleichzeitig als `UNAVAILABLE` melden. Für Ausfallalarme das Connectivity-Flag nutzen, für den Ladezustand `CP_STATE_CODE`.
- **Upgrade von ≤ 0.5.0:** die `*_ONLINE`-Keys wurden dort als (standardmäßig deaktivierte) normale Sensoren angelegt. Nach dem Update erscheinen sie als Binary Sensors; die alten, deaktivierten `sensor.*`-Einträge bleiben als Registry-Reste zurück und können gelöscht werden.

---

## Wallbox (CHARGING_POINT_AC)

Jede in der Site konfigurierte Wallbox vom Typ `CHARGING_POINT_AC` wird automatisch erkannt (Discovery über `/site/configuration` anhand des Thing-Typs, die konkrete Thing-ID wird nicht hart kodiert) und als eigenes Gerät in Home Assistant angelegt. Je Wallbox werden folgende Sensoren erzeugt:

| Key                       | Einheit | Device Class | state_class       |
|---------------------------|---------|--------------|-------------------|
| ACTIVE_POWER              | W       | power        | measurement       |
| MAX_POWER_CHARGE          | W       | power        | measurement       |
| MAX_POWER_CHARGE_FALLBACK | W       | power        | measurement       |
| CURRENT_P1 / P2 / P3      | A       | current      | measurement       |
| VOLTAGE_P1 / P2 / P3      | V       | voltage      | measurement       |
| CONSUMED_ENERGY_TOTAL     | Wh      | energy       | total_increasing  |
| CONSUMED_ENERGY_ACTUAL    | Wh      | energy       | total             |
| CHARGING_PROCESS_ENERGY   | Wh      | energy       | total             |
| CHARGING_TIME             | s       | duration     | measurement       |
| EV_STATE_CODE             | –       | –            | –                 |
| CP_STATE_CODE             | –       | –            | –                 |
| PHASE_SWITCHING_MODE      | –       | –            | –                 |
| LAST_RFID_CARD            | –       | –            | –                 |
| SERIAL_NUMBER             | –       | –            | –                 |
| FIRMWARE_VERSION          | –       | –            | –                 |
| ERROR_CODES               | –       | –            | – (Diagnose)      |

Hinweise:

- `CONSUMED_ENERGY_TOTAL` ist der kumulierte Lebenszeit-Zähler der Wallbox und eignet sich für das Home Assistant Energie-Dashboard.
- `ERROR_CODES` liefert die API als String-Array. Da ein Home-Assistant-Status skalar sein muss, werden mehrere Codes komma-separiert zusammengefasst; eine leere Liste wird als **`OK`** dargestellt. Die Entität ist als **Diagnose** kategorisiert.
- `SERIAL_NUMBER` und `FIRMWARE_VERSION` können leer bleiben, wenn der Beaam diese Angaben von der Station nicht erhalten hat — auch dann, wenn `CONNECTION` `true` meldet.
- `CONSUMED_ENERGY_ACTUAL` und `CHARGING_PROCESS_ENERGY` beziehen sich auf den **aktuellen Ladevorgang** und werden daher als `total` (nicht `total_increasing`) klassifiziert, da sie mit jedem neuen Vorgang zurückgesetzt werden.
- Mehrere Wallboxen werden parallel abgefragt; der Ausfall einer einzelnen Wallbox verhindert nicht die Aktualisierung der übrigen Sensoren.

### Lademodus umschalten (Select)

Für jede Wallbox mit dem Setting `OPERATING_MODE_EMS` wird zusätzlich eine **`select`-Entität „Lademodus"** angelegt. Damit lässt sich der Lademodus direkt aus Home Assistant umschalten (schreibt via `PUT /things/{thingId}/settings`):

| Auswahl         | `OPERATING_MODE_EMS` | angeboten |
|-----------------|----------------------|-----------|
| Solar           | `EXCESS_CONSUMPTION` | ja        |
| Schnell         | `FAST_CHARGING`      | ja        |
| Intelligent     | `GRIID_CONTROLLED`   | nein      |
| Ausgenommen     | `DEVICE_CONTROLLED`  | nein      |
| Flexibilitätsvermarktung | `FLEXIBILITY_MARKETING` | nein |

- **Solar** lädt aus PV-Überschuss, **Schnell** mit voller Leistung. Beide sind immer wählbar.
- **Intelligent** überlässt neoom CONNECT Ai die Entscheidung, wann am kostengünstigsten geladen wird, und **setzt ein CONNECT-Abo Mega oder Giga voraus**. Ob eines besteht, ist über die lokale API **nicht feststellbar** — es gibt kein Berechtigungsfeld, und ein Beaam ohne Abo nimmt den Wert trotzdem an und behält ihn (gemessen: `200`, fünf Minuten gehalten, kein serverseitiges Zurückrollen). Es gibt also nichts, worauf man reagieren könnte, und was eine so geschaltete Station tut, ist unbekannt — plausibel ist, dass nie ein Ladeplan eintrifft und das Auto stillschweigend nicht lädt. Deshalb wird der Modus **nicht zur Auswahl gestellt**: wer das Abo hat, stellt ihn einmal in der neoom-App ein, danach meldet ihn die Wallbox und er ist hier wählbar. Der Weg heraus ist eine Einbahnstraße, was nach einer Kündigung genau richtig ist.
- **Ausgenommen** würde die Wallbox der CONNECT-Steuerung ganz entziehen, **Flexibilitätsvermarktung** ist kein Lademodus — beide werden daher nur benannt, nicht angeboten.
- Solange die Wallbox einen dieser Modi tatsächlich meldet, bleibt er in der Liste, damit der aktuelle Zustand darstellbar ist. Bei einem **unbekannten** Wert erscheint er als rohe Option.
- Die Parameter für „Intelligent" — Lademenge und Abfahrtszeit — liegen als Settings `GRIID_CHARGING_ENERGY` und `GRIID_EV_DEPARTURE_TIME` vor und werden derzeit nicht angeboten.
- Nach dem Umschalten wird der Coordinator sofort aktualisiert, sodass der neue Modus ohne Wartezeit auf das Polling-Intervall erscheint.

NEOOM dokumentiert die erlaubten Werte nirgends in der API (`SettingDto.value` ist nur `string|number|boolean`); die Tabelle stammt aus den Übersetzungen des CONNECT-Portals unter dem Schlüssel `OPERATING_MODE_EMS/values`.

---

## Hinweise

- Die Integration arbeitet **lokal** gegen die interne API des Beaam, keine Cloud-Verbindung notwendig.
- Abfrageintervall: standardmäßig **30 Sekunden** (konfiguriert im `DataUpdateCoordinator`).
- Für Debugging im Home Assistant Log ggf. den Logger aktivieren:

  ```yaml
  logger:
    default: info
    logs:
      custom_components.beaam: debug
  ```

---

## ToDo / Erweiterungen

- Weitere schreibende Aktionen via `POST /things/{thingId}/commands` (z. B. Ladeleistung, Start/Stop). Zu beachten: Kommandos greifen laut NEOOM nur auf Datenpunkten, die in `/site/configuration` mit `"controllable": true` markiert sind. Beim `CHARGING_POINT_AC` sind das je nach Station ggf. nur `MAX_POWER_CHARGE`, `MAX_POWER_CHARGE_FALLBACK` und `PHASE_SWITCHING_MODE` — Kommandos wie `STATION_AVAILABILITY` oder `ENABLE_CHARGING` stehen im API-Enum, sind aber nicht zwingend am eigenen Thing verfügbar.
- Unterstützung für weitere Thing-Typen (BATTERY, PV, INVERTER, ELECTRICITY_METER_AC) analog zur Wallbox-Integration. Der `BATTERY` exponiert ebenfalls `OPERATING_MODE_EMS` — der Lademodus-Select ließe sich also unverändert auf den Speicher anwenden.
- `GRIID_CHARGING_ENERGY` und `GRIID_EV_DEPARTURE_TIME` als Number- bzw. Datetime-Entität, damit der Modus „Intelligent" auch parametriert werden kann
- Konfigurierbares Polling-Intervall

---

## Lizenz

MIT

## Disclaimer

Ich bin in keinster Weise mit NEOOM assoziiert, dies Projekt betreibe ich als rein privates Entwicklungsprojekt ohne Gewinnabsicht.
