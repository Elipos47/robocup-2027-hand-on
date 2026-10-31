# Firmware protocollo seriale v1.1

Firmware Arduino Mega 2560 + L298N per il protocollo definito in
`docs/architecture/SERIAL_PROTOCOL.md`.

**Stato:** compilato; protocollo verificato a banco (P1). B0 parziale: rotazione a 255, stop X
con ack 3,7-3,9 ms e watchdog a 1004,9-1008,3 ms con PWM 150/255 e timeout 1000 ms; a 150 i
motori ronzavano senza ruotare. Freno/coast e ripetizione da completare. Firmware riportato a
movimento disabilitato. B1-1: handshake, heartbeat, status, log JSONL e stop X verificati su
Raspberry Pi 5 con il firmware sicuro (`docs/testing/B1_INTEGRATION_TEST.md`). B1-2: comandi
motori a 255 con gate, ack, stop e rotazione confermata dall'operatore; firmware sicuro
ripristinato.

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

Nel Serial Monitor:

- baud **115200**;
- line ending **Newline** (oppure **Both NL & CR**): con "No line ending" il firmware non
  riceve il frame e non risponde;
- copia i frame esatti, comprese le lettere maiuscole e il checksum.

Frame da inviare:

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

Per un handshake automatico, senza digitare il checksum:

```sh
cd software
python3 -m rcj2027 --port /dev/ttyACM0 --duration 5 --run-id prova-001
```

Il comando aspetta il boot del Mega, invia `V`, mantiene `H` ogni 200 ms, registra gli status e
chiude con `X`. Senza `--duration` la sessione dura 5 s. Non invia `D`.

Se la tastiera non produce maiuscole, usa la console interattiva: accetta i payload in
minuscolo e aggiunge il checksum da solo.

```sh
cd software
python3 -m rcj2027 --port /dev/ttyACM0 --interactive --run-id prova-001
```

Esempi: `v,1`, `h,1`, `x,2`, `d,1,100,100`. Scrivi `quit` per uscire.

## Errori comuni

| Risposta | Significato |
|---|---|
| `E,UNKNOWN_COMMAND` | lettera del tipo minuscola o comando non riconosciuto |
| `E,BAD_CHECKSUM` | frame o checksum copiato male |
| `E,BAD_FORMAT` | campi mancanti, ordine sbagliato o newline assente |
| `E,MOTION_DISABLED` | movimento disabilitato o handshake `V` mancante |
| nessuna risposta | firmware di test motori ancora caricato, line ending sbagliato o porta occupata |

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
