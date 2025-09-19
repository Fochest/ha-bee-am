# Home Assistant Custom Integration – BEAAM API

Diese Home Assistant Custom-Integration bindet die **interne Beaam API** an.  (https://developer.neoom.com/reference/concepts-terms-1)

Es werden Messwerte wie Stromproduktion, Verbrauch, Netzbezug, Speicherzustand sowie **Fraktionswerte (z. B. PV → Speicher, PV → Netz)** als Sensoren in Home Assistant verfügbar gemacht.

Alle Sensoren unterstützen nun zusätzlich das Attribut `state_class`, um korrekte Auswertungen in den Home Assistant Dashboards zu ermöglichen.

---

## Installation

1. Lade das Repository/ZIP herunter und entpacke es nach:

   ```
   config/custom_components/beaam/
   ```

   sodass z. B. folgende Struktur existiert:

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
  → liefert Konfigurationsdaten der Site
- `GET http://{beaamIp}/api/v1/things/{thingId}/states`  
  → liefert Zustände einzelner Things (kann später ergänzt werden)

---

## Sensoren & Einheiten

Die wichtigsten Sensoren erhalten automatisch **Einheiten**, **Device Classes** und **state_class**, damit sie in Home Assistant korrekt visualisiert werden:

| Key                             | Einheit | Device Class | state_class |
|---------------------------------|---------|--------------|-------------|
| POWER_PRODUCTION                | W       | power        | measurement |
| POWER_CONSUMPTION_CALC          | W       | power        | measurement |
| POWER_GRID                      | W       | power        | measurement |
| POWER_STORAGE                   | W       | power        | measurement |
| ENERGY_PRODUCED                 | Wh      | energy       | total_increasing |
| ENERGY_CONSUMED_CALC            | Wh      | energy       | total_increasing |
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

- Schreibenden Zugriff via POST auf things/{thingId}/commands
- Unterstützung für weitere Endpunkte (`things/states`)
- Automatische Geräte- und Entitätsklassifizierung basierend auf `site/configuration`
- Konfigurierbares Polling-Intervall

---

## Lizenz

MIT

## Disclaimer

Ich bin in keinster Weise mit NEOOM assoziiert, dies Projekt betreibe ich als rein privates Entwicklungsprojekt ohne Gewinnabsicht.
