# Home Assistant Custom Integration – BEAAM API

Diese Home Assistant Custom-Integration bindet die **interne Beaam API** an.  (https://developer.neoom.com/reference/concepts-terms-1)

Es werden Messwerte wie Stromproduktion, Verbrauch, Netzbezug, Speicherzustand sowie **Fraktionswerte (z. B. PV → Speicher, PV → Netz)** als Sensoren in Home Assistant verfügbar gemacht.

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

Die wichtigsten Sensoren erhalten automatisch **Einheiten** und **Device Classes**, damit sie in Home Assistant korrekt visualisiert werden:

| Key                             | Einheit | Device Class |
|---------------------------------|---------|--------------|
| POWER_PRODUCTION                | W       | power        |
| POWER_CONSUMPTION_CALC          | W       | power        |
| POWER_GRID                      | W       | power        |
| POWER_STORAGE                   | W       | power        |
| ENERGY_PRODUCED                 | Wh      | energy       |
| ENERGY_CONSUMED_CALC            | Wh      | energy       |
| ENERGY_IMPORTED                 | Wh      | energy       |
| ENERGY_EXPORTED                 | Wh      | energy       |
| ENERGY_CHARGED                  | Wh      | energy       |
| ENERGY_DISCHARGED               | Wh      | energy       |
| STATE_OF_CHARGE                 | %       | battery      |
| SELF_SUFFICIENCY                | %       | –            |
| FRACTION_PV_TO_STORAGE          | %       | –            |
| FRACTION_PV_TO_GRID             | %       | –            |
| FRACTION_PV_TO_CONSUMPTION      | %       | –            |
| FRACTION_GRID_TO_STORAGE        | %       | –            |
| FRACTION_GRID_TO_CONSUMPTION    | %       | –            |
| FRACTION_STORAGE_TO_CONSUMPTION | %       | –            |
| FRACTION_STORAGE_TO_GRID        | %       | –            |

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
