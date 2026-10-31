# Test B1-3 - lettura HC-SR04 e BNO085

**ID:** B1-3
**Data:** 2026-10-31
**Firmware:** `firmware/rcj2027/rcj2027.ino` con configurazione sicura:
`BENCH_MOTION_ENABLED=false`, `PWM_MAX=0`, `WATCHDOG_TIMEOUT_MS=0`
**Software:** `software/rcj2027/session.py`, `transport.py`, `logger.py`, `__main__.py`
**Hardware:** Raspberry Pi 5 Model B + Arduino Mega 2560 + HC-SR04 + BNO085, USB
`/dev/ttyACM0`, 115200 8N1
**Condizioni:** robot fermo, movimento disabilitato, nessun comando `D`, nessuna modifica a
cablaggi.

## Obiettivo

Verificare sul link reale:

- lettura HC-SR04 (TRIG 27, ECHO 26) senza bloccare il loop seriale;
- lettura BNO085 su I2C (SDA 20, SCL 21), indirizzo `0x4A`;
- status `A` con bit 0 `SONAR_VALID`, bit 1 `IMU_VALID` e valori numerici;
- ripetibilita' su due sessioni.

## Comando

```sh
cd software
python3 -m rcj2027 --port /dev/ttyACM0 --duration 5 --run-id b1-sensors2
python3 -m rcj2027 --port /dev/ttyACM0 --duration 5 --run-id b1-sensors3
```

## Risultati

| Run | Status | `status=3` | `status=1` | `status=0` | Sonar validi | IMU validi | Errori | Invalidi |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| b1-sensors2 | 51 | 49 | 1 | 1 | 50 | 49 | 0 | 0 |
| b1-sensors3 | 51 | 49 | 1 | 1 | 50 | 49 | 0 | 0 |

Valori:

| Run | Distanza (mm) | Yaw (mdeg) | Pitch (mdeg) | Roll (mdeg) |
|---|---:|---:|---:|---:|
| b1-sensors2 | -1 .. 1126 | -211 .. 2 | 4719 .. 8155 | -2248 .. 21 |
| b1-sensors3 | -1 .. 1206 | -183 .. 8 | 4685 .. 8134 | -2072 .. 15 |

- Il primo status (`status=0`) arriva prima che i sensori abbiano un campione valido; il
  successivo (`status=1`) ha il solo sonar valido. Dal terzo status in poi `status=3`.
- Il primo campione IMU ha pitch/roll in convergenza; dopo circa 0,5 s i valori si stabilizzano
  (pitch ~4,7°, roll ~-2,1°). La distanza resta ~0,9-1,2 m.
- 0 errori, 0 frame invalidi, nessun motore attivo, nessun movimento.

## Diagnostica I2C

Il BNO085 risponde a `0x4A`. Lo scanner `firmware/test/i2c_scan/` ha prodotto:

```text
I2C_SCAN_BEGIN
I2C_FOUND 0x4A
I2C_FOUND_COUNT 1
I2C_SCAN_END
```

Il BNO085 non e' pronto immediatamente al boot: il primo `setupImu()` falliva, quindi il
firmware ritenta l'inizializzazione ogni secondo finche' il bus risponde. Dopo il retry:
`IMU_BEGIN 1`, `IMU_ENABLE 1`.

## Cosa e' verificato

- HC-SR04 letto in modo non bloccante, con timeout e distanza in millimetri;
- bit 0 `SONAR_VALID` coerente e distanza plausibile;
- BNO085 su I2C `0x4A`, bit 1 `IMU_VALID` e angoli in milligradi;
- status periodico con sensori e motori fermi;
- ripetibilita' su due run;
- nessun movimento e nessun comando `D`.

## Cosa non e' verificato

- distanza del sonar confrontata con un metro campione;
- orientamento e montaggio degli assi BNO085, calibrazione e deriva yaw;
- risposta dell'IMU a rotazioni controllate del robot;
- camere, calibrazione ottica e percezione;
- temperatura, corrente e autonomia.

I valori IMU sono dati grezzi del game rotation vector, non una calibrazione di mounting. Il
bit `IMU_VALID` indica che il sensore ha prodotto un campione recente, non che gli assi siano
allineati al robot.

## Note

- Il firmware resta a movimento disabilitato; `D` risponde `E,MOTION_DISABLED`.
- La libreria Arduino richiesta e' `Adafruit BNO08x` (installata: 1.2.5).
- I log completi sono in `/tmp` o `software/logs/` e non vengono versionati.
