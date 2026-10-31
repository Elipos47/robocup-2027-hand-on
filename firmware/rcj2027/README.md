# Firmware protocollo seriale v1.1

Firmware Arduino Mega 2560 + L298N per il protocollo definito in
`docs/architecture/SERIAL_PROTOCOL.md`.

**Stato:** compilato; movimento disabilitato di default. Pronto per i test di banco del
protocollo.

## Cablaggio

| Segnale L298N | Pin Mega 2560 |
|---|---:|
| `ENA` | 12 |
| `IN1` | 22 |
| `IN2` | 23 |
| `ENB` | 13 |
| `IN3` | 24 |
| `IN4` | 25 |

Mappa verificata: canale A = ruota destra, canale B = ruota sinistra. La polarita' di entrambi i
canali e' invertita nel firmware. Alimentazione motori separata dall'Arduino, con GND comune.

## Build e upload

```sh
bash scripts/build.sh
arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:avr:mega firmware/rcj2027
```

Apri il Serial Monitor a **115200 baud**.

## Configurazione di sicurezza

All'inizio di `rcj2027.ino`:

```cpp
const bool BENCH_MOTION_ENABLED = false;
const uint8_t PWM_MAX = 0;                 // 0 = disabilitato
const unsigned long WATCHDOG_TIMEOUT_MS = 0;  // 0 = disabilitato
```

Con questi valori il movimento e' disabilitato: `D` risponde `E,MOTION_DISABLED`, mentre `X`
funziona sempre. Non sono valori di fallback.

Per il test di banco B0 si possono impostare valori espliciti e temporanei:

```cpp
const bool BENCH_MOTION_ENABLED = true;
const uint8_t PWM_MAX = 150;
const unsigned long WATCHDOG_TIMEOUT_MS = 1000;
```

`PWM_MAX = 150` e `WATCHDOG_TIMEOUT_MS = 1000` sono valori di prova, non definitivi. Il valore
finale di `pwm_max` e il timeout del watchdog vanno scelti dopo la misura e registrati in
`docs/MEASUREMENT_LOG.md`.

## Test del protocollo senza movimento

Frame da inviare dal Serial Monitor:

| Frame | Risposta attesa |
|---|---|
| `V,1*4B` | `V,1,ARDUINO_MEGA,1*61` |
| `H,1*55` | nessun ack; aggiorna il watchdog |
| `D,1,100,100*59` | `E,MOTION_DISABLED*38` |
| `X,2*46` | `K,2*55` |
| `Z,3,90*60` | `E,SERVO_UNVERIFIED*76` |

Dopo `V` il firmware invia un frame `A` ogni 100 ms:

```text
A,<sequence>,-1,0,0,0,<status>*HH
```

- `distance_mm = -1`: HC-SR04 non ancora implementato;
- angoli IMU a `0`: BNO085 non ancora implementato;
- bit 2 dello status: motori attivi;
- bit 3: watchdog scattato.

## Test B0 con movimento

1. Imposta la configurazione di banco qui sopra.
2. Ricompila e carica con le **ruote sollevate**.
3. Invia `V,1*4B`, poi `H,1*55`, poi `D,1,100,100*59`: i motori devono partire e rispondere `K,1*56`.
4. Continua a inviare `H` almeno ogni secondo; i motori restano attivi.
5. Smetti di inviare `H`: dopo il timeout il firmware ferma i motori e invia
   `E,WATCHDOG_STOP*2B`.
6. Invia `X,2*46` per lo stop manuale; risposta `K,2*55`.
7. Misura il tempo reale tra l'ultimo `H` e l'arresto e registralo nel registro misure.
8. Riporta `BENCH_MOTION_ENABLED` a `false` prima dell'uso normale.

Se `D` supera `PWM_MAX`, il firmware risponde `E,BAD_RANGE` e non muove i motori.

## Note

- Il servo non e' implementato: `Z` risponde `E,SERVO_UNVERIFIED`.
- HC-SR04 e BNO085 non sono ancora letti; lo status li segnala come non validi.
- Il firmware non usa `String`: buffer e memoria sono statici.
- Il watchdog e' attivo solo con `WATCHDOG_TIMEOUT_MS > 0` e motori in movimento.
