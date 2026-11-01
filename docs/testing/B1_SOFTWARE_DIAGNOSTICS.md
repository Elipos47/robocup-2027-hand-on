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
python3 -m rcj2027.diagnostics camera --device auto --save /tmp/camera0.jpg
python3 -m rcj2027.diagnostics camera --csi --camera-num 0 \
  --size 1280x720 --full-fov --warmup 2 --save /tmp/csi0.jpg

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

La suite completa e' a **144 test**, tutti verdi.

## Camera

Sono presenti due sorgenti distinte:

```text
5MP USB Camera (USB):  /dev/video8, /dev/video9 (la numerazione cambia al boot)
IMX708 (CSI):          camera libcamera 0, /base/.../imx708@1a
```

`v4l2-ctl --list-devices` vede la USB; `rpicam-hello --list-cameras` e Picamera2 vedono la CSI
IMX708. La CSI non va aperta con un indice OpenCV: si usa `--csi`, che passa da
Picamera2/libcamera.

Ruoli confermati dall'operatore:

- **USB 5MP = stanza/vittime e palline**;
- **CSI IMX708 = linea**.

La calibrazione USB a 640x480 vale per la stanza, non per la linea. La CSI va calibrata alla
risoluzione usata dal pipeline della linea.

La probe USB (OpenCV) ha prodotto:

| Device | Aperto | Frame | Luminosita' | Contrasto | Nitidezza | Esito |
|---|---:|---|---:|---:|---:|---|
| 0 | si | 640x480 @30 | 70,9-80,9 | 52,2-54,3 | 67,5-73,1 | PASS |
| 1 | no | - | - | - | - | device assente |
| 2 | si | non leggibile | - | - | - | nodo piattaforma, non camera |
| 3 | no | - | - | - | - | device assente |

Dopo il riavvio la numerazione e' cambiata: la USB e' passata a `/dev/video8` e `/dev/video0` e'
diventato un nodo CSI. Per questo la CLI usa `--device auto`, che trova la USB tramite sysfs.

La probe CSI (Picamera2, camera 0, autofocus continuo e warm-up 2 s) e' stata ripetuta con il
checkerboard davanti alla camera:

| Risoluzione | Nitidezza normalizzata a 640 px | Esito |
|---|---:|---|
| 640x480 | 103,0 | PASS |
| 1280x720 | 149,3 | PASS |
| 1536x864 | 133,9 | PASS |
| 2304x1296 | 213,8 | PASS |

La misura precedente (`sharpness=9,3`) era una scena fuori fuoco, non un problema del sensore.
La IMX708 con autofocus e checkerboard e' nitida. La nitidezza viene ora normalizzata a 640 px
di larghezza, altrimenti il valore numerico cambia con la risoluzione.

La preview puo' mostrare piu' campo dello still perche' libcamera sceglie un modo sensore diverso:
1280x720 usa di default 1536x864, che e' un crop 2x. Con `--full-fov` si forza il sensore intero
2304x1296 mantenendo l'output 1280x720. Verificato: checkerboard completo, 54 corner,
`quality_passed=true`, `passed=true`.

Una prova con il checkerboard troppo vicino ha dato `quality_passed=true` ma
`checkerboard_corners=0`: il pattern era tagliato dal frame. Per la calibrazione deve essere
visibile **tutta** la scacchiera, bordo bianco compreso. Se `quality_passed` e' vero ma i corner
sono zero, allontanare il foglio o alzare la camera.

Per la linea va scelta una risoluzione di lavoro (candidata: 1280x720) e la CSI va calibrata a
quella risoluzione, non a 640x480.

La calibrazione USB a 640x480 e' accettata. Per la CSI, un set di 15 frame ha dato copertura
14,0% ma **dispersione dei centri 0,6 px e rapporto dimensioni 1,00**: tutte le viste erano la
stessa posa. Il calibratore ora rifiuta questo caso con `viste troppo simili`. Per una calibrazione
utile servono 8-10 pose diverse (inclinazioni e posizioni), non 15 copie. Con copertura 14-20% e
pose varie si puo' usare `--min-coverage 0.14`.

La calibrazione intrinseca e' implementata e testata con immagini sintetiche; la CLI
`camera-calibrate` e' stata eseguita end-to-end su 5 viste sintetiche (RMS 0,045) per verificare
il percorso. Il target pronto e' in `docs/hardware/checkerboard-a4.pdf` (A4 landscape, 9x6
corner, quadrati 25 mm, barra da 100 mm); va stampato al 100% su carta opaca. Se la barra misura
95 mm, usare `--square-mm 23.75`. Il calibratore ora rifiuta una copertura media inferiore al
20%: le 15 foto USB attuali coprono solo 3,6-9,6% e non sono valide per una calibrazione reale.
Un secondo set di 15 foto ha rilevato il pattern in 8 immagini, con copertura 3,8-28,8% e media
11,0%: solo 3 viste superano il 20%. Il problema e' la distanza incoerente tra i frame; servono
almeno 8-10 viste con il pattern grande e interamente visibile. Il terzo set ha rilevato 15/15
immagini, copertura media 22,7% (20,0-31,3%) e RMS 0,523 px: e' accettato come prima calibrazione
USB ed e' salvato in `rcj2027/calibrations/usb_640x480.json`. La sequenza si acquisisce con:

```sh
python3 -m rcj2027.diagnostics camera-capture --device auto \
  --count 15 --interval 2 --output-dir calib/usb
```

Per la CSI si usa `--csi --camera-num 0 --size 1280x720 --full-fov` (o la risoluzione scelta
per la linea); la calibrazione va rifatta a quella risoluzione e con lo stesso campo visivo.

## Sonar

Raccolte da 10 s con il firmware sicuro:

| Run | Campioni | Validi | Distanza min-max | Media | Mediana | Dev. std | Salto max | Esito |
|---|---:|---:|---|---:|---:|---:|---:|---|
| diag-sonar-001 | 100 | 99 | 871-1597 mm | 1000,1 mm | 996 mm | 129,1 mm | 695 mm | FAIL |
| diag-sonar-002 | 101 | 101 | 867-1595 mm | 1009,5 mm | 997 mm | 147,9 mm | 697 mm | FAIL |
| sonar-500-001 | 100 | 100 | 400-1202 mm | 597,6 mm | 598 mm | 112,2 mm | 703 mm | FAIL |
| sonar-500-002 | 100 | 100 | 397-1154 mm | 487,5 mm | 404 mm | 138,5 mm | 754 mm | FAIL |
| sonar-500-003 | 100 | 99 | 382-1095 mm | 483,7 mm | 414 mm | 121,0 mm | 694 mm | FAIL |
| sonar-500-004 | 100 | 99 | 406-1197 mm | 619,5 mm | 598 mm | 142,2 mm | 694 mm | FAIL |

I test a 500 mm hanno mostrato un problema di riferimento: la media di sonar-500-002 passava
(487,5 mm) ma la mediana era 404 mm, quindi la media era trascinata dagli outlier a 1100 mm. Il
test usa ora la **mediana**. Il risultato 003 era 414 mm; dopo lo spostamento del target il 004
ha dato 598 mm. Il target appare quindi a circa **400 mm** prima e **600 mm** dopo: la distanza
fisica e' cambiata di circa 200 mm, oppure la misura e' presa dal telaio e il sensore e' arretrato
di circa 100 mm. I picchi a 1095-1197 mm indicano riflessioni o un oggetto dietro il target. Il
test resta FAIL: non va abbassata la tolleranza.

### Criterio robusto e stabilita' del target

Il salto massimo su un singolo campione e' troppo fragile per un sensore a ultrasuoni: un solo
eco spurio non deve invalidare 99 campioni buoni. Il test ora usa la **percentuale di outlier**
(oltre ±200 mm dalla mediana, massimo 5%) e continua a riportare il salto massimo.

| Run | Mediana | Outlier | Salto max | Riferimento 500 mm | Esito |
|---|---:|---:|---:|---|---|
| sonar-500-005 | 522 mm | 3/101 (3,0%) | 699 mm | +22 mm, PASS | PASS col criterio robusto |
| sonar-500-006 | 507,5 mm | 1/100 (1,0%) | 600 mm | +7,5 mm, PASS | PASS col criterio robusto |
| sonar-500-007 | 597 mm | 9/98 (9,2%) | 602 mm | +97 mm, FAIL | FAIL |

Le run 005 e 006, con il target fermo intorno a 500 mm, passano il criterio robusto. La 007 ha
mediana 597 mm e 9,2% di outlier: il target si e' spostato verso 600 mm durante la prova. Il
problema non e' il codice: il target deve restare fermo e supportato per tutti i 10 secondi.

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

- USB 5MP acquisisce frame validi e passa le soglie di luminosita'/contrasto/nitidezza;
- calibrazione USB accettata: 15/15 viste, RMS 0,523 px, copertura 22,7%;
- CSI IMX708 viene enumerata da libcamera/Picamera2 e acquisisce un frame;
- sonar e IMU producono status con bit di validita' coerenti;
- IMU stabile a riposo e sensibile alle rotazioni yaw, pitch e roll;
- pitch/roll scambiati sul montaggio corretti nel firmware;
- analisi e calibrazione sono coperte da test host.

## Cosa non e' verificato

- sonar a 1000 mm e stabilita' con target in movimento; il test a 500 mm con target fermo e'
  accettato per ostacoli piu' vicini di 0,5 m;
- calibrazione della CSI alla risoluzione di linea e verifica del montaggio definitivo;
- calibrazione reale della CSI e miglioramento della copertura USB;
- convenzione dei segni pitch/roll e comportamento dopo un rimontaggio del BNO085;
- luminosita' in condizioni di gara (luce bassa, riflessi, ombre).

## Note

- I log completi sono in `/tmp` o `software/logs/` e non vengono versionati.
- Ogni telecamera e' esclusiva: non eseguire due probe in parallelo sulla stessa sorgente.
  USB e CSI sono sorgenti distinte, ma Picamera2 elenca anche la USB: non aprirla due volte.
- Il test sonar fallito e' un dato da correggere, non un motivo per abbassare la soglia senza
  una prova con bersaglio stabile.
