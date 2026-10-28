# Energiemanager

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)
[![hacs][hacsbadge]][hacs]
![Project Maintenance][maintenance-shield]

Home Assistant Custom Integration zur intelligenten Nulleinspeisung, Prioritäten-Kaskadierung und dynamischen 1-phasigen PV-Überschussladung (Tesla via lokalem BLE-über-MQTT) inklusive Hardware-Schutzverriegelung für Heimspeicher (Anker Solarbank) und transparentem Session-Tracking nach dem WashData-Prinzip.

---

## ✨ Features im Überblick

- **Nulleinspeisung mit EMA-Filterung:**
  - Glättung des Netzzählers mittels exponentiellem gleitendem Mittelwert (EMA, $\alpha = 0{,}35$) gegen kurzzeitige Leistungsspitzen (z. B. Induktionskochfeld).
  - Symmetrische Totzone von $\pm 60\,\text{W}$ verhindert ständiges Takten und Schwingungen der Stellglieder.
- **5-stufige Prioritäten-Kaskade:**
  1. **Hausgrundlast:** Automatisch vorrangig durch phasenübergreifende Saldierung des Netzzählers.
  2. **Heimspeicher (Anker Solarbank):** Konfigurierbarer Mindest-Reserve-SOC (0–100 %) via Schieberegler (z. B. Sommer 60 %, Winter 0 %).
  3. **Thermischer Puffer (Multisplit-Klimaanlage):** Nutzt moderate Überschüsse ($500\,\text{W}$ bis $1.350\,\text{W}$) zur Verschiebung der Raum-Solltemperatur um $\pm 1{,}5\,^\circ\text{C}$ (mit 20 Minuten Kompressorschutz-Mindestlaufzeit).
  4. **Elektrofahrzeug (Tesla via Mobile Connector):** Dynamische 1-phasige Überschussladung ab $1.380\,\text{W}$ ($6\,\text{A}$).
  5. **Resteinspeisung ins Netz:** Verbleibender Überschuss nach Deckung der Stufen 1–4.
- **Akku-Schutzverriegelung (Hardware-Schutz):**
  - Verhindert das verlustbehaftete Entladen des Heimspeichers in die Autobatterie.
  - Sobald Ladeleistung $> 250\,\text{W}$: Automatische Aktivierung der Entladesperre des Speichers.
  - Abschaltverzögerung von 60 Sekunden nach Ladeende ($\le 250\,\text{W}$) vor Freigabe der Speicherentladung.
- **1-Phasen Tesla-Ladesteuerung (230 V via lokalem BLE-über-MQTT):**
  - Einstellbereich von $6\,\text{A}$ ($1.380\,\text{W}$) bis $16\,\text{A}$ ($3.680\,\text{W}$) in präzisen $230\,\text{W}$-Schritten ($1\,\text{A}$).
  - Modi: `Aus`, `PV-Überschuss` (inkl. 180 s Wolkenpuffer bei 6 A), `Schnellladen` (maximale Ladeleistung bis Ziel-SOC).
  - Lokale Steuerung: Automatische Fahrzeug-Präsenzerkennung und Wake-up-Trigger ohne Cloud-Latenz.
- **Session-Tracking nach dem WashData-Prinzip:**
  - Automatische Lade-Sitzungserkennung (Steckerstatus & Ladeleistung $> 200\,\text{W}$).
  - Echtzeit-Zerlegung des Ladestroms in Solar- und Netzanteil.
  - Native Energiezähler (`state_class: total_increasing`) zur direkten Integration in das Home Assistant Energy Dashboard:
    - `sensor.sam_energiemanager_ev_solar_lifetime_kwh`
    - `sensor.sam_energiemanager_ev_grid_lifetime_kwh`
  - Automatische Erstellung einer Session-Zusammenfassung und Auslösen des Events `sam_energiemanager_session_completed`.

---

## 🏛️ Architektur & Regelkreis

```text
               ┌──────────────────────────────────────┐
               │    Netzzähler (Leistung in Watt)     │
               └──────────────────┬───────────────────┘
                                  │
                                  ▼
               ┌──────────────────────────────────────┐
               │   EMA-Filter (α = 0,35) + Totzone    │
               │             (±60 W)                  │
               └──────────────────┬───────────────────┘
                                  │
                                  ▼
                    P_surplus = max(0, -P_grid)
                                  │
       ┌──────────────────────────┼──────────────────────────┐
       │                          │                          │
       ▼                          ▼                          ▼
┌──────────────┐          ┌──────────────┐          ┌──────────────────┐
│ Stufe 2:     │          │ Stufe 3:     │          │ Stufe 4:         │
│ Heimspeicher │          │ Klima-Puffer │          │ E-Auto (Tesla)   │
│ Reserve-SOC  │          │ (500–1350 W) │          │ 6–16 A (1-phasig)│
└──────────────┘          └──────────────┘          └──────────────────┘
                                                             │
                                                             ▼
                                                    ┌──────────────────┐
                                                    │ Hardware-Schutz: │
                                                    │ Entladesperre    │
                                                    │ Speicher aktiv   │
                                                    └──────────────────┘
```

### 1. Filterung & Totzone

Zur Vermeidung von Fehlauslösungen durch kurzzeitige Einschaltströme (z. B. Herdplatten) wird der Rohwert des Netzzählers über einen exponentiell geglätteten Mittelwert (EMA) berechnet:

$$P_{\text{grid\_gefiltert}}(t) = \alpha \cdot P_{\text{grid\_roh}}(t) + (1 - \alpha) \cdot P_{\text{grid\_gefiltert}}(t-1) \quad (\alpha = 0{,}35)$$

Liegt die gefilterte Leistung im Totzonen-Fenster von $[-60\,\text{W}, +60\,\text{W}]$, verbleiben alle Stellgrößen im aktuellen Zustand, um Regelschwingungen zu unterbinden.

Der verfügbare Überschuss ergibt sich aus:

$$P_{\text{surplus}} = \max(0, -P_{\text{grid\_gefiltert}})$$

### 2. Prioritäten-Kaskade

| Stufe | Verbraucher            | Aktivierungsbedingung                                                          | Verhalten                                                                                                         |
| :---: | :--------------------- | :----------------------------------------------------------------------------- | :---------------------------------------------------------------------------------------------------------------- |
| **1** | **Hausgrundlast**      | Immer aktiv                                                                    | Wird physikalisch vorrangig durch den Hausanschluss saldiert.                                                     |
| **2** | **Heimspeicher**       | `battery_soc < reserve_soc`                                                    | Überschuss fließt primär in den Speicher. E-Auto-Ladung und Klimapufferung bleiben blockiert.                     |
| **3** | **Thermischer Puffer** | `ac_buffer_enabled` & $500\,\text{W} \le P_{\text{surplus}} < 1.350\,\text{W}$ | Verschiebung der Raum-Solltemperatur um $\pm 1{,}5\,^\circ\text{C}$. Mindestlaufzeit: 20 Min. (Kompressorschutz). |
| **4** | **Tesla E-Auto**       | $P_{\text{surplus}} \ge 1.380\,\text{W}$ oder Stufe 2 & 3 gesättigt            | 1-phasige Ladung mit $6\,\text{A}$ bis $16\,\text{A}$ ($230\,\text{W}$-Schritte).                                 |
| **5** | **Netzeinspeisung**    | Stufen 1–4 vollständig gesättigt                                               | Überschuss wird ins öffentliche Netz eingespeist.                                                                 |

### 3. Akku-Schutzverriegelung

Sobald die Ladeleistung des E-Autos $250\,\text{W}$ überschreitet, schaltet der Energiemanager die Entladesperre des Speichers (`switch.anker_discharge_disabled` bzw. die konfigurierte Entitäts-ID) auf `on`. Erst wenn die Ladeleistung für mindestens 60 Sekunden ununterbrochen $\le 250\,\text{W}$ beträgt, wird die Sperre wieder freigegeben (`off`).

### 4. Dynamische 1-Phasen-Ladesteuerung

- **Spannungsbasis:** $230\,\text{V}$ (1 Phase).
- **Regelformel:**

$$I_{\text{target}} = \text{clamp}\left(\left\lfloor \frac{P_{\text{surplus}} + P_{\text{ev\_aktuell}}}{230} \right\rfloor, 6, I_{\text{max}}\right)$$

- **Lademodi:**
  - `Aus`: Ladung gestoppt bzw. pausiert.
  - `PV-Überschuss`: Dynamische Anpassung des Ladestroms ($6\,\text{A}$ bis $I_{\text{max}}$). Fällt der Überschuss unter $1.380\,\text{W}$, puffert ein Hysterese-Timer von 180 Sekunden bei $6\,\text{A}$ kurzzeitige Wolken ab, bevor die Ladung pausiert wird.
  - `Schnellladen`: Lädt mit voller konfigurierter Stromstärke ($I_{\text{max}}$) aus PV und Netz, bis der Ziel-SOC (`number.sam_energiemanager_tesla_target_soc`) erreicht ist; wechselt danach automatisch auf `Aus`.

---

## 📊 WashData-Prinzip & Session-Tracking

Bei jedem Rechenzyklus (z. B. alle 5 bis 10 Sekunden) wird die aktuelle Ladeleistung des Fahrzeugs anhand des realen Netzflusses zerlegt:

$$P_{\text{ev\_solar}} = \min(P_{\text{ev}}, P_{\text{surplus\_vor\_ladesteigerung}})$$
$$P_{\text{ev\_grid}} = P_{\text{ev}} - P_{\text{ev\_solar}}$$

Daraus werden zwei fortlaufende Zähler gespeist, die direkt als Verbraucher im Home Assistant Energy Dashboard hinzugefügt werden können:

- `sensor.sam_energiemanager_ev_solar_lifetime_kwh`
- `sensor.sam_energiemanager_ev_grid_lifetime_kwh`

### Session-Abschluss & Automation Event

Nach dem Abstecken des Ladekabels oder bei Ladeende wird der Sensor `sensor.sam_energiemanager_last_session_summary` aktualisiert und das Event `sam_energiemanager_session_completed` gefeuert:

```yaml
event_type: sam_energiemanager_session_completed
data:
  session_id: "2026-10-28_14-30-00"
  energy_total_kwh: 14.85
  energy_solar_kwh: 12.40
  energy_grid_kwh: 2.45
  solar_percentage: 83.5
  grid_percentage: 16.5
  duration_minutes: 185
  start_soc: 42
  end_soc: 68
  cost_eur: 0.78
```

---

## 🚀 Installation & Einrichtung

### 1. Installation über HACS

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Gamers-ElitE&repository=ha-energiemanager&category=integration)

1. Öffne **HACS** → **Integrationen**.
2. Klicke auf die drei Punkte oben rechts → **Benutzerdefinierte Repositories**.
3. URL hinzufügen: `https://github.com/Gamers-ElitE/ha-energiemanager`, Kategorie: **Integration**.
4. Installiere **Energiemanager** und starte Home Assistant neu.

### 2. UI-Konfiguration (Config Flow)

Füge die Integration unter **Einstellungen** → **Geräte & Dienste** → **Integration hinzufügen** → **Energiemanager** hinzu.

Der Einrichtungs-Assistent führt dich durch die Zuordnung deiner Entitäten:

- **Netzzähler:** Leistungssensor in Watt (positiv = Bezug, negativ = Einspeisung).
- **Heimspeicher:** Batterie-SOC (%) und Entladesperren-Switch (z. B. Anker Solarbank).
- **Tesla (lokales BLE-über-MQTT):**
  - Ladeleistung (W)
  - Ladestrom-Sollwert (Number/Select)
  - Ladestatus / Steckerstatus
  - Batterie-SOC (%)
  - Wake-up-Button
  - BLE-Verbindungsstatus (Präsenz)
- **Klima / Wärmepumpe:** Climate-Entität für die thermische Pufferung.

---

## 🎛️ Dashboard-Beispiele (Lovelace)

### 1. Energiemanager Steuerungs-Karte

```yaml
type: entities
title: Energiemanager Steuerung
entities:
  - entity: select.sam_energiemanager_charging_mode
    name: Lademodus
  - entity: number.sam_energiemanager_tesla_max_current
    name: Maximaler Ladestrom
  - entity: number.sam_energiemanager_tesla_target_soc
    name: Schnelllade-Ziel-SOC
  - entity: number.sam_energiemanager_battery_reserve_soc
    name: Speicher Vorrang-Reserve
  - entity: switch.sam_energiemanager_ac_buffer_enabled
    name: Klima-Pufferung aktivieren
```

### 2. Status & WashData-Statistik

```yaml
type: vertical-stack
cards:
  - type: glance
    title: Aktuelle Leistungsflüsse
    entities:
      - entity: sensor.sam_energiemanager_grid_power_filtered
        name: Netz (gefiltert)
      - entity: sensor.sam_energiemanager_surplus_power
        name: PV-Überschuss
      - entity: sensor.sam_energiemanager_ev_charging_power
        name: Ladeleistung E-Auto
  - type: entities
    title: Letzte Ladesitzung (WashData)
    entities:
      - entity: sensor.sam_energiemanager_last_session_summary
        name: Zusammenfassung
      - entity: sensor.sam_energiemanager_ev_solar_lifetime_kwh
        name: E-Auto Solar gesamt
      - entity: sensor.sam_energiemanager_ev_grid_lifetime_kwh
        name: E-Auto Netz gesamt
```

### 3. Benachrichtigungs-Automation bei Ladeabschluss

```yaml
alias: "Energiemanager: Ladezusammenfassung senden"
trigger:
  - platform: event
    event_type: sam_energiemanager_session_completed
action:
  - action: notify.notify
    data:
      title: "🚗 E-Auto Ladesitzung beendet"
      message: >
        Geladen: {{ trigger.event.data.energy_total_kwh }} kWh
        Solar-Anteil: {{ trigger.event.data.solar_percentage }}% ({{ trigger.event.data.energy_solar_kwh }} kWh)
        Netz-Anteil: {{ trigger.event.data.grid_percentage }}% ({{ trigger.event.data.energy_grid_kwh }} kWh)
        Dauer: {{ trigger.event.data.duration_minutes }} Min. | Kosten: {{ trigger.event.data.cost_eur }} €
```

---

## 📄 Lizenz

Dieses Projekt ist lizenziert unter der MIT-Lizenz – siehe [LICENSE](LICENSE) für Details.

---

**Made with ❤️ by [@Gamers-ElitE][user_profile]**

[commits-shield]: https://img.shields.io/github/commit-activity/y/Gamers-ElitE/ha-energiemanager.svg?style=for-the-badge
[commits]: https://github.com/Gamers-ElitE/ha-energiemanager/commits/main
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/Gamers-ElitE/ha-energiemanager.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40Gamers-ElitE-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/Gamers-ElitE/ha-energiemanager.svg?style=for-the-badge
[releases]: https://github.com/Gamers-ElitE/ha-energiemanager/releases
[user_profile]: https://github.com/Gamers-ElitE
