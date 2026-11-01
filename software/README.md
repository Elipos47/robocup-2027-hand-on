# Software Raspberry Pi

Python per percezione, stato, logging, interfaccia operatore e comunicazione con l'Arduino.

## Struttura

```text
software/
  rcj2027/
    protocol.py    codifica/decodifica del protocollo seriale v1.1
    transport.py   trasporto pyserial bufferizzato e trasporto finto per i test
    logger.py      log JSONL con run_id e timestamp UTC
    safety.py      gate di movimento e configurazione hardware
    session.py     handshake, heartbeat, status, stop e log della sessione
    sensor_checks.py      analisi sonar/IMU
    camera_checks.py      probe e metriche frame
    camera_calibration.py calibrazione checkerboard
    checkerboard.py       target PDF a dimensione reale
    line_vision.py        undistort, rilevamento linea e tracker F0
    diagnostics.py        CLI di diagnostica camera/sonar/IMU/linea
    calibrations/         JSON delle calibrazioni telecamere
    __main__.py    demo, sessione reale e console manuale
  tests/           test host con unittest
  requirements.txt pyserial, OpenCV e numpy
```

## Comandi

```sh
cd software
python3 -m rcj2027 --run-id demo-001
python3 -m unittest discover -s tests -t . -v
```

Sessione reale senza movimento: handshake, heartbeat ogni 200 ms, status e stop `X` alla
chiusura.

```sh
cd software
python3 -m rcj2027 --port /dev/ttyACM0 --duration 5 --run-id b1-001
```

Il comando attende 2 s il boot del Mega, invia `V,1`, registra gli status in JSONL e termina con
`X`. Non invia comandi motori: il movimento resta disabilitato dal firmware e dal gate di
`safety.py`. Il report della prova e' in `docs/testing/B1_INTEGRATION_TEST.md`.

## Diagnostica software

La CLI `diagnostics` verifica i dati di camera, sonar e IMU senza abilitare il movimento:

```sh
cd software
python3 -m rcj2027.diagnostics camera --list
python3 -m rcj2027.diagnostics camera --device auto --save /tmp/camera0.jpg
python3 -m rcj2027.diagnostics camera --csi --camera-num 0 --size 1280x720 \
  --full-fov --warmup 2 --save /tmp/csi0.jpg
python3 -m rcj2027.diagnostics sonar --port /dev/ttyACM0 --duration 10
python3 -m rcj2027.diagnostics sonar --port /dev/ttyACM0 --duration 10 \
  --reference-mm 500 --reference-tolerance 50
python3 -m rcj2027.diagnostics imu --port /dev/ttyACM0 --duration 10 \
  --imu-mode stationary
python3 -m rcj2027.diagnostics imu --port /dev/ttyACM0 --duration 10 \
  --imu-mode motion --expected-axis yaw --countdown 5
python3 -m rcj2027.diagnostics camera-calibrate \
  --images "calib/*.jpg" --pattern 9x6 --square-mm 25 --output calib.json
python3 -m rcj2027.diagnostics camera-capture --device auto \
  --count 15 --interval 2 --output-dir calib/usb
python3 -m rcj2027.diagnostics camera-capture --csi --camera-num 0 \
  --size 1280x720 --full-fov --count 15 --interval 2 --output-dir calib/csi
python3 -m rcj2027.diagnostics checkerboard \
  --pattern 9x6 --square-mm 25 --output checkerboard.pdf
```

Exit code `0` = test superato, `1` = test fallito, `2` = errore di configurazione o dispositivo.
I report si salvano con `--json-out`. La numerazione `/dev/videoN` cambia al riavvio:
`--device auto` trova la USB tramite sysfs, mentre `--csi` usa Picamera2 per la CSI. Il target
`checkerboard` e' pronto in `docs/hardware/checkerboard-a4.pdf`: PDF A4 con quadrati da 25 mm e
barra da 100 mm, da stampare al 100%. Se la barra misura 95 mm, usa `--square-mm 23.75` o
ristampa. `camera-capture` salva una sequenza di frame mentre sposti il target; `camera-calibrate`
rifiuta una copertura media del pattern sotto il 20% (puntare al 50-80%). La calibrazione USB
accettata (15 viste, RMS 0,523 px, copertura 22,7%) e' in
`rcj2027/calibrations/usb_640x480.json`; la linea usa
`rcj2027/calibrations/csi_1280x720.json` (14/15 viste, RMS 0,542 px, 1280x720 full-fov). Le
immagini sorgente restano in `calib/` e non sono versionate. Ruoli: USB = stanza/vittime/palline,
CSI = linea; la CSI va usata con `--size 1280x720 --full-fov`, non a 640x480. `--full-fov`
forza il sensore intero 2304x1296: senza, 1280x720 usa un crop 1536x864 e la preview puo'
mostrare piu' campo dello still. `camera-calibrate` rifiuta copertura media sotto il 20% e viste
quasi identiche; con pose varie si puo' usare `--min-coverage 0.14`. Il test sonar usa la mediana
e ammette al massimo il 5% di outlier oltre `--outlier-mm`; il test IMU `motion` richiede che si
muova l'asse indicato. Ogni telecamera e' esclusiva: non eseguire due probe in parallelo.

Risultati e limiti sono in `docs/testing/B1_SOFTWARE_DIAGNOSTICS.md`.

## Visione linea F0

`line_vision.py` implementa il primo pipeline della linea: undistort con
`calibrations/csi_1280x720.json`, ROI inferiore, adaptive threshold, scanline, fit
parabolico robusto e tracker. Non invia comandi ai motori.

```sh
cd software

# Verifica l'undistort sulle viste checkerboard della calibrazione
python3 -m rcj2027.diagnostics line-undistort \
  --images "calib/csi/*.jpg" --json-out logs/f0-undistort.json

# Acquisisce una sequenza con la CSI linea
python3 -m rcj2027.diagnostics camera-capture --csi --camera-num 0 \
  --size 1280x720 --full-fov --warmup 2 \
  --count 30 --interval 0.3 --output-dir calib/linea-f0-001

# Analizza la sequenza e salva report, frame annotati e maschere
python3 -m rcj2027.diagnostics line \
  --images "calib/linea-f0-001/*.jpg" \
  --annotated-dir logs/f0-linea-001/annotated \
  --mask-dir logs/f0-linea-001/mask \
  --json-out logs/f0-linea-001/report.json

# Loop live dalla CSI, senza comandi ai motori
python3 -m rcj2027.diagnostics line-live --camera-num 0 \
  --size 1280x720 --warmup 2 --duration 10 \
  --annotated-dir logs/f0-live/annotated --save-every 15 \
  --json-out logs/f0-live/report.json
```

`offset_px` positivo significa linea a destra dell'asse ottico; `heading_deg` positivo
significa linea che piega a destra. I valori restano validi solo con `found=true`. La
calibrazione e' legata a 1280x720 full-fov: un frame di risoluzione diversa viene rifiutato.
Exit code del comando `line`: `0` se la frazione di frame con linea raggiunge
`--min-found-ratio` (default 0.8), `1` se sotto soglia, `2` per errore. La sequenza reale
F0-1 (`calib/linea-f0-001`, 30 frame) ha dato 30/30 frame trovati, offset -46,0 px,
heading 3,95 deg e confidenza 0,95. Il loop `line-live` ha elaborato 100 frame in 5,03 s
(19,9 FPS) con 100/100 frame trovati. Il report e' in `logs/f0-linea-001/report.json`; dettagli
e limiti in `docs/testing/F0_LINE_VISION.md`.

Per una console manuale sulla porta reale, che accetta comandi in minuscolo e calcola il
checksum:

```sh
cd software
python3 -m rcj2027 --port /dev/ttyACM0 --interactive --run-id prova-001
```

Esempi di payload: `v,1`, `h,1`, `x,2`, `d,1,100,100`. Scrivi `quit` per uscire.

La demo usa il trasporto finto: non apre la porta seriale e non muove il robot. I log finiscono
in `logs/` (ignorata da git) oppure nella directory indicata con `--log-dir`.

## Comandi motori

`RobotSession.drive(left, right)` e' il livello software per `D`: applica il gate di
`safety.py`, rifiuta i valori oltre `pwm_max`, invia il comando e attende l'ack continuando gli
heartbeat. Non e' esposto dalla CLI e non viene chiamato dalle sessioni di logging. Il gate usa
`DEFAULT_CONFIG`, che resta volutamente incompleto (gate chiuso); per abilitare il movimento va
passata esplicitamente `OPERATIONAL_CONFIG`.

La prova B1-2 e' stata eseguita con ruote sollevate e conferma dell'operatore: comandi a 255
su entrambe le ruote e sui canali separati, ack, stop e rotazione osservata. Il firmware sicuro
e' stato ripristinato; il report e' in `docs/testing/B1_INTEGRATION_TEST.md`.

## Configurazione

`safety.py` espone due configurazioni:

- `DEFAULT_CONFIG`: batteria 11.1 V, A = ruota destra, B = ruota sinistra, polarita' invertita;
  `pwm_max` e `watchdog_timeout_s` restano vuoti, quindi il gate e' chiuso. E' il default delle
  sessioni di logging e non e' un valore di fallback.
- `OPERATIONAL_CONFIG`: stessi dati piu' `pwm_max=255` e `watchdog_timeout_s=1.0`. Sono i valori
  operativi scelti il 2026-10-31; vanno usati solo esplicitamente e con il firmware di banco o
  operativo corrispondente. Il firmware sicuro continua a rifiutare `D` con
  `MOTION_DISABLED`.

`pwm_max=255` e' la scelta dell'operatore dopo B1-2. Il watchdog di 1.0 s e' l'unico valore
misurato a banco (stop a 1004-1008 ms, B0).

## Regole

- Il movimento reale resta disabilitato di default: `DEFAULT_CONFIG` ha il gate chiuso e il
  firmware sicuro rifiuta `D`. Per muoversi servono `OPERATIONAL_CONFIG` esplicito e firmware di
  banco/operativo.
- Ogni funzione ha un test ripetibile e un log associato.
- Il trasporto finto serve a testare il protocollo senza robot; non e' un simulatore del
  percorso.
- Le dipendenze stanno in un venv locale, non nel repository.
