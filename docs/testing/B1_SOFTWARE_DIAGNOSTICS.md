# Test B1-4 - diagnostica software di camera, sonar e IMU

**ID:** B1-4
**Data:** 2026-10-31
**Firmware:** `firmware/rcj2027/rcj2027.ino` con configurazione sicura
(`BENCH_MOTION_ENABLED=false`, `PWM_MAX=0`, `WATCHDOG_TIMEOUT_MS=0`)
**Software:** `software/rcj2027/camera_checks.py`, `camera_calibration.py`,
`sensor_checks.py`, `diagnostics.py`
**Hardware:** Raspberry Pi 5 Model B + Arduino Mega 2560 + HC-SR04 + BNO085 + telecamera USB
5MP + telecamera CSI IMX708
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

# Telecamera: elenco, probe USB e probe CSI
python3 -m rcj2027.diagnostics camera --list
python3 -m rcj2027.diagnostics camera --device 0 --save /tmp/camera0.jpg
python3 -m rcj2027.diagnostics camera --csi --camera-num 0 --warmup 2 \
  --save /tmp/csi0.jpg

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
python3 -m rcj2027.diagnostics checkerboard \
  --pattern 9x6 --square-mm 25 --output checkerboard.pdf
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

La suite completa e' a **130 test**, tutti verdi.

## Camera

Sono presenti due sorgenti distinte:

```text
5MP USB Camera (USB):  /dev/video0, /dev/video1
IMX708 (CSI):          camera libcamera 0, /base/.../imx708@1a
```

`v4l2-ctl --list-devices` vede la USB; `rpicam-hello --list-cameras` e Picamera2 vedono la CSI
IMX708. La CSI non va aperta con un indice OpenCV: si usa `--csi`, che passa da
Picamera2/libcamera.

La probe USB (OpenCV) ha prodotto:

| Device | Aperto | Frame | Luminosita' | Contrasto | Nitidezza | Esito |
|---|---:|---|---:|---:|---:|---|
| 0 | si | 640x480 @30 | 70,9-80,9 | 52,2-54,3 | 67,5-73,1 | PASS |
| 1 | no | - | - | - | - | device assente |
| 2 | si | non leggibile | - | - | - | nodo piattaforma, non camera |
| 3 | no | - | - | - | - | device assente |

La probe CSI (Picamera2, camera 0, warm-up 2 s) ha prodotto:

| Camera | Modello | Frame | Luminosita' | Contrasto | Nitidezza | Esito |
|---|---|---|---:|---:|---:|---|
| libcamera:0 | imx708 | 640x480 | 147,9 | 34,6 | 9,3 | **FAIL** |

La CSI acquisisce correttamente, ma il frame e' fuori fuoco (`sharpness=9,3` contro la soglia
50). La IMX708 ha autofocus: il test imposta AF continuo e attende 2 s, ma la scena inquadrata
resta sfocata. Non e' un problema di acquisizione: vanno verificati messa a fuoco e montaggio
della camera. Il test fallisce correttamente.

La calibrazione intrinseca e' implementata e testata con immagini sintetiche; la CLI
`camera-calibrate` e' stata eseguita end-to-end su 5 viste sintetiche (RMS 0,045) per verificare
il percorso, ma non e' una calibrazione delle camere reali. Il target si genera con
`python3 -m rcj2027.diagnostics checkerboard` (A4 landscape, 9x6 corner, quadrati 25 mm, barra
da 100 mm) e va stampato al 100% su carta opaca. Servono 12-20 viste reali con il pattern che
occupa circa il 50-80% del frame.

## Sonar

Raccolte da 10 s con il firmware sicuro:

| Run | Campioni | Validi | Distanza min-max | Media | Mediana | Dev. std | Salto max | Esito |
|---|---:|---:|---|---:|---:|---:|---:|---|
| diag-sonar-001 | 100 | 99 | 871-1597 mm | 1000,1 mm | 996 mm | 129,1 mm | 695 mm | FAIL |
| diag-sonar-002 | 101 | 101 | 867-1595 mm | 1009,5 mm | 997 mm | 147,9 mm | 697 mm | FAIL |
| sonar-500-001 | 100 | 100 | 400-1202 mm | 597,6 mm | 598 mm | 112,2 mm | 703 mm | FAIL |
| sonar-500-002 | 100 | 100 | 397-1154 mm | 487,5 mm | 404 mm | 138,5 mm | 754 mm | FAIL |
| sonar-500-003 | 100 | 99 | 382-1095 mm | 483,7 mm | 414 mm | 121,0 mm | 694 mm | FAIL |

I test a 500 mm hanno mostrato un problema di riferimento: la media di sonar-500-002 passava
(487,5 mm) ma la mediana era 404 mm, quindi la media era trascinata dagli outlier a 1100 mm. Il
test usa ora la **mediana**. Il risultato finale e' 414 mm, cioe' il target appare a circa
**400 mm**, non 500. La causa piu' probabile e' che i 500 mm siano stati misurati dal telaio
invece che dalla faccia del sensore: il sensore e' arretrato di circa 100 mm. I picchi a 1095 mm
indicano anche riflessioni o un oggetto dietro il target. Il test resta FAIL: non va abbassata
la tolleranza.

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
| imu-stationary-after-swap | 100 | 100 | 7,1 mdeg | 4,2 mdeg | 10,7 mdeg | 0 mdeg | PASS |

Il test scarta i primi 5 campioni per la convergenza iniziale del game rotation vector.

### Movimento yaw

| Run | Campioni | Validi | Yaw min-max | Asse dominante | Asse atteso | Esito |
|---|---:|---:|---|---|---|---|
| diag-imu-motion-001 | 180 | 178 | -6,7 .. 62,0 deg | yaw | yaw | PASS |

L'operatore ha ruotato il robot a mano di circa 90 gradi e lo ha riportato indietro. Il test ha
rilevato yaw con escursione di circa 68,7 gradi e asse dominante yaw. La deriva residua
(-36,4 deg) indica che la posizione finale non coincideva esattamente con quella iniziale; non
e' un errore del test.

### Pitch e roll: correzione del montaggio

I primi test hanno mostrato che pitch e roll erano **scambiati** rispetto al telaio. Il firmware
applica ora `IMU_SWAP_PITCH_ROLL=true`; non e' una calibrazione del sensore, ma una correzione di
montaggio.

| Run | Campioni | Validi | Intervallo | Asse dominante | Asse atteso | Esito |
|---|---:|---:|---|---|---|---|
| imu-pitch-after-swap | 151 | 149 | pitch -21,2 .. 8,0 deg | pitch | pitch | PASS |
| imu-roll-after-swap | 150 | 150 | roll -19,8 .. 25,6 deg | roll | roll | PASS |

Le due run sono state eseguite inclinando il robot a mano attorno all'asse indicato. La
convenzione dei segni (positivo/negativo) non e' ancora fissata: i test verificano l'asse
dominante, non il verso.

## Cosa e' verificato

- USB 0 acquisisce frame validi e passa le soglie di luminosita'/contrasto/nitidezza;
- CSI IMX708 viene enumerata da libcamera/Picamera2 e acquisisce un frame;
- sonar e IMU producono status con bit di validita' coerenti;
- IMU stabile a riposo e sensibile alle rotazioni yaw, pitch e roll;
- pitch/roll scambiati sul montaggio corretti nel firmware;
- analisi e calibrazione sono coperte da test host;
- il comando di calibrazione camera e' pronto per un target reale.

## Cosa non e' verificato

- stabilita' del sonar con bersaglio fermo e riferimento metrico;
- messa a fuoco e montaggio della CSI: il frame attuale e' sfocato;
- calibrazione reale di USB e CSI con checkerboard;
- convenzione dei segni pitch/roll e comportamento dopo un rimontaggio del BNO085;
- luminosita' in condizioni di gara (luce bassa, riflessi, ombre).

## Note

- I log completi sono in `/tmp` o `software/logs/` e non vengono versionati.
- Ogni telecamera e' esclusiva: non eseguire due probe in parallelo sulla stessa sorgente.
  USB e CSI sono sorgenti distinte, ma Picamera2 elenca anche la USB: non aprirla due volte.
- Il test sonar fallito e' un dato da correggere, non un motivo per abbassare la soglia senza
  una prova con bersaglio stabile.
