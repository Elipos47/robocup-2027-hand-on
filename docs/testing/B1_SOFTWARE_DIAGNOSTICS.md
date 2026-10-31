# Test B1-4 - diagnostica software di camera, sonar e IMU

**ID:** B1-4
**Data:** 2026-10-31
**Firmware:** `firmware/rcj2027/rcj2027.ino` con configurazione sicura
(`BENCH_MOTION_ENABLED=false`, `PWM_MAX=0`, `WATCHDOG_TIMEOUT_MS=0`)
**Software:** `software/rcj2027/camera_checks.py`, `camera_calibration.py`,
`sensor_checks.py`, `diagnostics.py`
**Hardware:** Raspberry Pi 5 Model B + Arduino Mega 2560 + HC-SR04 + BNO085 + una
telecamera USB 5MP
**Condizioni:** robot fermo, movimento disabilitato, nessun comando `D`; rotazione IMU
eseguita a mano dall'operatore.

## Obiettivo

Fornire test software ripetibili per verificare i dati di:

- telecamera: apertura, frame, luminosita', contrasto, nitidezza, checkerboard;
- HC-SR04: validita', statistiche, salti, riferimento metrico;
- BNO085: validita', stabilita' a riposo, movimento e asse atteso;
- calibrazione intrinseca della telecamera da immagini checkerboard.

I test non usano multimetri, sonde termiche o spazio di frenata.

## Comandi

```sh
cd software

# Telecamera: elenco e probe singolo
python3 -m rcj2027.diagnostics camera --list
python3 -m rcj2027.diagnostics camera --device 0 --save /tmp/camera0.jpg

# Sonar: raccolta e analisi
python3 -m rcj2027.diagnostics sonar --port /dev/ttyACM0 --duration 10
python3 -m rcj2027.diagnostics sonar --port /dev/ttyACM0 --duration 10 \
  --reference-mm 500 --reference-tolerance 50

# IMU: fermo e in movimento
python3 -m rcj2027.diagnostics imu --port /dev/ttyACM0 --duration 10 \
  --imu-mode stationary
python3 -m rcj2027.diagnostics imu --port /dev/ttyACM0 --duration 10 \
  --imu-mode motion --expected-axis yaw --countdown 5

# Calibrazione camera da immagini checkerboard
python3 -m rcj2027.diagnostics camera-calibrate \
  --images "calib/*.jpg" --pattern 9x6 --square-mm 25 --output calib.json
```

Exit code: `0` test superato, `1` test fallito, `2` errore di configurazione o dispositivo.
I report JSON si possono salvare con `--json-out`.

## Test host

I test host non richiedono hardware:

- analisi sonar con sequenze valide, flag incoerenti, salti, fuori range e gap;
- confronto con distanza di riferimento e tolleranza;
- analisi IMU stazionaria, in movimento, asse atteso e fuori range;
- metriche camera su frame sintetici (buio, sovraesposto, sfocato, rumore, checkerboard);
- calibrazione con viste checkerboard sintetiche;
- raccolta status con sessione finta.

La suite completa e' a **123 test**, tutti verdi.

## Camera

`v4l2-ctl --list-devices` mostra una sola telecamera fisica:

```text
5MP USB Camera: 5MP USB Camera (usb-xhci-hcd.1-1):
    /dev/video0
    /dev/video1
```

La probe ha prodotto:

| Device | Aperto | Frame | Luminosita' | Contrasto | Nitidezza | Esito |
|---|---:|---|---:|---:|---:|---|
| 0 | si | 640x480 @30 | 70,9-76,5 | 52,2-54,3 | 67,5-70,0 | PASS |
| 1 | no | - | - | - | - | device assente |
| 2 | si | non leggibile | - | - | - | nodo piattaforma, non camera |
| 3 | no | - | - | - | - | device assente |

La seconda telecamera prevista non e' collegata o non e' enumerata. Il test la segnala come
assente e non inventa un device.

La calibrazione intrinseca e' implementata e testata con immagini sintetiche; la CLI
`camera-calibrate` e' stata eseguita end-to-end su 5 viste sintetiche (RMS 0,045) per verificare
il percorso, ma non e' una calibrazione della camera reale: serve un checkerboard con numero di
corner e lato noti.

## Sonar

Due raccolte da 10 s con il firmware sicuro:

| Run | Campioni | Validi | Distanza min-max | Media | Dev. std | Salto max | Esito |
|---|---:|---:|---|---:|---:|---:|---|
| diag-sonar-001 | 100 | 99 | 871-1597 mm | 1000,1 mm | 129,1 mm | 695 mm | FAIL |
| diag-sonar-002 | 101 | 101 | 867-1595 mm | 1009,5 mm | 147,9 mm | 697 mm | FAIL |

Il sensore risponde e il bit `SONAR_VALID` e' coerente, ma la lettura non e' stabile: il salto
massimo supera la soglia di 500 mm. I valori si distribuiscono intorno a 900, 1000 e 1100 mm,
con un transitorio a circa 1595 mm. La causa probabile e' l'ambiente/cono di emissione, non il
protocollo. Il test fallisce correttamente e resta da ripetere con un bersaglio stabile e una
distanza misurata con un metro.

## IMU

### Stazionario

| Run | Campioni | Validi | Yaw std | Pitch std | Roll std | Deriva yaw | Esito |
|---|---:|---:|---:|---:|---:|---:|---|
| diag-imu-001 | 100 | 98 | 3,2 mdeg | 59,8 mdeg | 28,2 mdeg | -2 mdeg | PASS |

Il test scarta i primi 5 campioni per la convergenza iniziale del game rotation vector.

### Movimento yaw

| Run | Campioni | Validi | Yaw min-max | Asse dominante | Asse atteso | Esito |
|---|---:|---:|---|---|---|---|
| diag-imu-motion-001 | 180 | 178 | -6,7 .. 62,0 deg | yaw | yaw | PASS |

L'operatore ha ruotato il robot a mano di circa 90 gradi e lo ha riportato indietro. Il test ha
rilevato yaw con escursione di circa 68,7 gradi e asse dominante yaw. La deriva residua
(-36,4 deg) indica che la posizione finale non coincideva esattamente con quella iniziale; non
e' un errore del test.

## Cosa e' verificato

- camera 0 acquisisce frame validi e passa le soglie di luminosita'/contrasto/nitidezza;
- sonar e IMU producono status con bit di validita' coerenti;
- IMU stabile a riposo e sensibile alla rotazione yaw;
- analisi e calibrazione sono coperte da test host;
- il comando di calibrazione camera e' pronto per un target reale.

## Cosa non e' verificato

- stabilita' del sonar con bersaglio fermo e riferimento metrico;
- seconda telecamera;
- calibrazione reale della camera con checkerboard;
- orientamento degli assi IMU rispetto al telaio;
- luminosita' in condizioni di gara (luce bassa, riflessi, ombre).

## Note

- I log completi sono in `/tmp` o `software/logs/` e non vengono versionati.
- La telecamera e' esclusiva: non eseguire due probe in parallelo.
- Il test sonar fallito e' un dato da correggere, non un motivo per abbassare la soglia senza
  una prova con bersaglio stabile.
