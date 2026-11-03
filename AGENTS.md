# Robocup2027HandOn

## Obiettivo

Progetto hardware-first per RoboCupJunior Rescue Line 2027. Il software viene sviluppato in
coordinamento con misure, collaudo a banco e prove sul campo. Il repository contiene il codice
nuovo del robot (Python sul Raspberry, C++/Arduino sul Mega); non dipende da un simulatore e non
contiene il codice applicativo del progetto precedente.

## Stack

- Documentazione Markdown e PDF ufficiali.
- Raspberry Pi 5 4GB e Arduino Mega 2560 come piattaforma hardware.
- Python sul Raspberry per percezione, stato, logging e UI.
- C++/Arduino sul Mega per motori, sensori, servo e watchdog.
- OpenCV e sensori fisici; nessun simulatore.
- Prove su banco e sul campo: il test sul campo e' il criterio di avanzamento principale.

## Comandi

```sh
# install:  arduino-cli core install arduino:avr; arduino-cli lib install "Adafruit BNO08x"; python3 -m pip install -r software/requirements.txt
# validate: bash scripts/check_context.sh
# build:    bash scripts/build.sh
# test:     bash scripts/test.sh
# lint:     git diff --check
# upload:   arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:avr:mega firmware/test/motor_direction_test
```

<Esegui questi comandi con cwd in questa cartella.>

## Convenzioni

- Git: repository inizializzato su `main`; i checkpoint sono automatici. Il push e' regolato
  dalla sezione «Remoto e push»; `reset --hard`, rebase e riscritture di storia restano vietati.
- Layout del codice: `firmware/` per gli sketch Arduino, `software/rcj2027/` per il Python del
  Raspberry, `firmware/test/<nome>/<nome>.ino` per gli sketch di banco. Ogni sketch di test ha
  un `README.md` con cablaggio, comandi e risultato atteso.
- Il software Python si testa con `bash scripts/test.sh` (check, build e unittest). Il movimento
  resta disabilitato se `pwm_max` o il timeout watchdog mancano.
- La fonte di verita' hardware e' `docs/hardware/`; ogni misura reale va registrata con data,
  strumento, condizione e incertezza in `docs/MEASUREMENT_LOG.md`.
- Per il software si usa il contratto minimo in
  `docs/hardware/MINIMUM_HARDWARE_DATA.md`: non richiedere un inventario completo di schede,
  masse, cavi o CAD se non e' necessario al codice richiesto.
- I parametri non critici possono restare `TODO`; quelli di sicurezza mancanti devono
  disabilitare il movimento reale e non diventare valori di fallback.
- Il regolamento 2026 e' provvisorio fino alla disposizione del regolamento ufficiale 2027.
- Non modificare hardware, cablaggi o collegamenti senza approvazione esplicita. Il firmware
  si modifica nel repository, si compila con `bash scripts/build.sh` e si carica sul robot solo
  dopo la compilazione; i test di movimento si eseguono con ruote sollevate e alimentazione
  controllata.
- Non introdurre simulatori o log di simulazione. Il codice del progetto precedente non viene
  importato.
- I TODO sono parte del contesto: non riempirli con valori inventati o inferenze non verificate.
- I segreti stanno in `.env`, mai nel repository; non salvare credenziali, token o porte seriali
  reali con password.
- La lingua dei documenti e' italiano; nomi di file e simboli tecnici restano in inglese quando
  sono standard o servono per la compatibilita' con l'hardware.

## Remoto e push

- Il remoto e' `origin` (GitHub `Elipos47/robocup-2027-hand-on`), branch `main`.
- **Deroga dichiarata alla regola globale «mai push senza richiesta esplicita»**: l'autore ha
  chiesto che il remoto resti aggiornato, quindi `git push origin main` fa parte del lavoro
  ordinario di questo progetto. La deroga vale solo qui, non negli altri progetti del workspace.
- A fine turno, se hai modificato file: verifica `bash scripts/test.sh` verde, nessun segreto
  (`git grep -nEi 'password|api[_-]?key|secret|token|BEGIN (RSA|OPENSSH)|192\.168\.'`) e
  `git status --short`; se il checkpoint automatico non e' avvenuto, crea un commit
  descrittivo, poi esegui `git push origin main`.
- Mai `push --force`, `reset --hard`, rebase o riscritture di storia. Se il remoto e'
  divergente, fermati e chiedi.
- Se il push fallisce per autenticazione, non inventare token o credenziali: fermati e
  segnalalo all'utente.
- I PDF in `docs/rules/` e `docs/hardware/Misure Robotica.pdf` sono ridistribuiti nel repo:
  con un repo pubblico verifica che la ridistribuzione sia ammessa prima di pushare.

## Stato attuale

- Fatto: struttura documentale, inventario hardware, riferimento CAD, regolamento provvisorio,
  piano hardware-first, architettura e protocollo seriale v1.1.
- Fatto: contratto minimo ridotto ai tre dati che il software non puo' dedurre: tensione,
  asse e verso dei motori. Batteria 11.1 V da etichetta (2 pacchi Li-Ion 3S in parallelo).
- Fatto: mappa pin L298N (ENA/ENB 12/13, IN1..IN4 22..25), HC-SR04 (TRIG 27, ECHO 26) e
  BNO085 (SDA 20, SCL 21); breakout Adafruit BNO085 confermato compatibile con I2C a 5 V.
- Fatto: primo sketch di banco in `firmware/test/motor_direction_test/`, compilato con
  `bash scripts/build.sh`. Prova a banco completata: polarita' di entrambi i canali invertita e
  corretta nel software (`1`/`3` avanti); mappa lati verificata: A = ruota destra, B = ruota
  sinistra.
- Fatto: package `software/rcj2027/` con protocollo v1.1, trasporto finto, logger, gate di
  sicurezza e test unittest; la demo fake funziona e il movimento resta disabilitato.
- Fatto: console interattiva `python3 -m rcj2027 --port ... --interactive`, che accetta
  payload in minuscolo e calcola il checksum.
- Fatto: B1-1, sessione reale Raspberry Pi 5 - Arduino Mega con firmware sicuro
  (`docs/testing/B1_INTEGRATION_TEST.md`): handshake, heartbeat 200 ms, status a circa 100 ms,
  log JSONL, stop `X` con ack 3-5 ms, 0 errori e 0 frame invalidi su tre run da 5 s. Nessun
  comando `D` e nessun movimento.
- Fatto: gate software per i comandi motori (`RobotSession.drive`) con limite `pwm_max`,
  attesa ack, heartbeat durante l'attesa e stop di sicurezza su rifiuto/timeout; coperto da test
  host con trasporto finto.
- Fatto: B1-2 con ruote sollevate e conferma dell'operatore: `D` a 255 su entrambe le ruote e
  sui canali separati, ack 5-6 ms, stop 2-5 ms, bit 2 `4` -> `0`, 0 errori e rotazione osservata.
  Un tentativo intermedio ha esposto un `ACK_TIMEOUT` da backlog di status, corretto drenando
  fino alla deadline. Firmware sicuro ripristinato e `D` di nuovo `MOTION_DISABLED`.
- Fatto: valori operativi scelti in `OPERATIONAL_CONFIG`: `pwm_max=255` (decisione
  dell'operatore) e watchdog `1.0 s` (unico timeout misurato a banco). `DEFAULT_CONFIG` resta
  incompleto e il gate predefinito resta chiuso.
- Fatto: B1-3, HC-SR04 e BNO085 letti sul robot con movimento disabilitato
  (`docs/testing/B1_SENSORS_TEST.md`): sonar valido 50/51 status, distanze ~0,9-1,2 m; BNO085
  su I2C `0x4A`, IMU valido 49/51, status bit 0+1. Assi IMU e distanza di riferimento restano
  da calibrare.
- Fatto: B1-4, suite software di diagnostica per camera, sonar e IMU
  (`docs/testing/B1_SOFTWARE_DIAGNOSTICS.md`): probe camera USB (OpenCV) e CSI (Picamera2),
  metriche, target checkerboard PDF, calibrazione, analisi statistica sonar/IMU, test IMU
  stazionario e in movimento. USB e IMU passano; pitch/roll erano scambiati sul montaggio e sono
  stati corretti nel firmware con test pitch/roll PASS; CSI acquisisce ma il frame e' sfocato;
  il sonar e' valido ma instabile e il test fallisce se il target si muove. Con target fermo a
  ~500 mm, 005/006 passano col criterio robusto (mediane 522/507,5 mm, outlier 3,0%/1,0%); la
  007 con target spostato a ~600 mm ha mediana 597 mm e 9,2% outlier, FAIL. L'operatore accetta
  il test a 500 mm per ostacoli piu' vicini di 0,5 m.
- Fatto: target checkerboard A4 pronto in `docs/hardware/checkerboard-a4.pdf` e comando
  `camera-capture` per acquisire 12-20 frame di calibrazione. Le prime 15 foto USB sono state
  rifiutate: RMS 0,896 px ma copertura media 7,2%, sotto il minimo 20%; rifare piu' vicino. Un
  secondo set ha rilevato 8/15 frame con copertura media 11,0% e solo 3 viste >=20%: distanza
  incoerente. Il terzo set ha 15/15 viste, RMS 0,523 px e copertura 22,7%: accettato e salvato in
  `software/rcj2027/calibrations/usb_640x480.json`.
- Fatto: la CLI camera usa `--device auto`: dopo il riavvio la USB e' passata a `/dev/video8`
  e `/dev/video0` e' diventato un nodo CSI; la numerazione non e' piu' stabile.
- Fatto: firmware Arduino del protocollo v1.1 in `firmware/rcj2027/`, compilato; movimento
  disabilitato di default.
- Fatto: protocollo verificato a banco senza movimento (test P1 in
  `docs/testing/PROTOCOL_BENCH_TEST.md`): V, H, status, X e `D` rifiutato con
  `MOTION_DISABLED`.
- Fatto: B0 parziale con motori attivi (test B0-1 in `docs/testing/B0_BENCH_TEST.md`): stop X
  con ack 3,7-3,9 ms e watchdog a 1004,9-1008,3 ms con PWM 150/255 e timeout 1000 ms. A 150 i
  motori ronzavano senza ruotare; a 255 hanno girato (conferma dell'operatore). Firmware
  riportato a movimento disabilitato.
- Fatto: ruoli telecamere confermati: USB 5MP = stanza/vittime/palline, CSI IMX708 = linea.
  La CSI con autofocus e checkerboard e' nitida a 640x480-2304x1296; a 1280x720 la probe passa
  con nitidezza normalizzata 149,3. La nitidezza e' normalizzata a 640 px per confrontare
  risoluzioni diverse. `--full-fov` forza il sensore intero 2304x1296: con checkerboard completo
  la probe da' 54 corner e `passed=true`; senza, 1280x720 usa un crop 1536x864.
- Nota: il set CSI da 15 frame aveva copertura 14,0% ma pose identiche (spread 0,6 px, size
  ratio 1,00); il calibratore lo rifiuta. Servono 8-10 pose diverse, non 15 copie.
- Fatto: il set CSI successivo ha 14/15 viste, copertura 16,3%, pose spread 423,6 px, size
  ratio 1,93 e RMS 0,542 px; calibrazione accettata e salvata in
  `software/rcj2027/calibrations/csi_1280x720.json` (1280x720 full-fov).
- Fatto: F0-1, primo pipeline visione linea in `software/rcj2027/line_vision.py`
  (`docs/testing/F0_LINE_VISION.md`): undistort CSI, ROI, adaptive threshold, scanline
  top-down, fit parabolico robusto, confidenza, tracker e CLI `line`/`line-undistort`. La
  verifica undistort sulle 14 viste checkerboard passa (errore omografia 0,4392 -> 0,4287 px).
  Prova reale su linea nera retta con robot fermo: 30/30 frame trovati, offset stabile
  -46,0 px, heading ~3,95 deg, confidenza ~0,95, 0 perdite; report in
  `software/logs/f0-linea-001/report.json`. Il primo tentativo dava 0/30 per bordo tavolo e
  pavimento, corretto con scansione top-down, stop sui gap e continuita' di larghezza.
  Aggiunto `line-live`: 100 frame in 5,04 s (19,8 FPS), 100/100 trovati, offset -46,5 px,
  heading 4,14 deg, confidenza 0,95, nessun comando ai motori. Vista live con `--preview` o
  stream MJPEG `--http-port`; `--debug-overlay` mostra la maschera, `--duration 0` va fino a
  q/ESC, il browser ha un pulsante di stop e `software/line_live.py` e' l'avvio rapido da
  Thonny.
  Test host: 199 verdi. Disturbi e movimento reale non sono ancora provati, quindi
  il gate F0 resta aperto.
- Fatto: F0-2 tentativo 1 su curva reale (`docs/testing/F0_CURVE_TEST.md`): 1584 frame,
  89,29 s, 17,7 FPS; 899/1584 trovati (56,8%) ma con 317 frame iniziali vuoti e 223 di
  riposizionamento. Nei tratti in ROI la curva e' seguita con confidenza 0,86-0,965 e 6
  riprese; il nastro e' piu' largo di 1-2 cm, quindi e' un proxy di banco. La telecamera e'
  volutamente vicina e la curva puo' uscire dalla ROI: **F0-2 e' coperto sul banco**, senza
  richiedere raggio o linea regolamentare. Resta la compatibilita' con la linea 1-2 cm.
- Fatto: strumentazione avvio `line-live`: `camera_start_s`, `warmup_s`, `first_frame_s` nel
  report. Due run di prova danno primo frame a 2,08-2,19 s; il ritardo di 18,73 s della run
  curva e' anomalo, non il comportamento atteso.
- Fatto: F0-3 ombra parziale, tentativo 1: 608/608 frame trovati, 606 confermati, 0 perdite,
  confidenza 0,663-0,978, startup 5,6 s. L'ombra era probabilmente leggera: ripetere con
  un'ombra netta su 1/3 e 2/3 della linea; l'occlusione totale non e' ancora provata.
- Fatto: F0-3 ombra totale/bassa luce, tentativo 1 (`docs/testing/F0_SHADOW_TEST.md`): nella
  fase buia il rilevatore agganciava un bordo sottile (10-31 px contro 188-190 px) con offset
  sbagliato di circa +48 px. Aggiunto il guard di continuita' di larghezza: replay della run
  765 trovati -> 433 accettati, 332 rifiutati, 426 confermati, `control_passed=false`. Serve
  una run live con il nuovo guard e una vera occlusione opaca.
- Fatto: F0-4 gap da 7 cm, tentativo 1 (`docs/testing/F0_GAP_TEST.md`): 513 frame, 28,47 s,
  251/513 trovati, 266 confermati, 6 riprese, nessun falso evidente. FOUND sui segmenti,
  LOST nel vuoto, ripresa dopo. Al frame 150 la linea era visibile ma veniva persa per un
  seme isolato e per il filtro di larghezza; corretti stop sul gap e aumento di larghezza,
  con test sintetico. Seconda run 181848: 479 frame, 288/479 trovati, 320 confermati, 6
  riprese; al frame 120 un seme lontano bloccava la linea. Aggiunto reset del tratto corto e
  test `far_speck`. Terza run 182854: 487 frame, 284/487 trovati, 304 confermati, 6 riprese,
  frame 120 FOUND; **F0-4 chiuso sul banco**. L'attraversamento resta F1.
- Fatto: F0-5 controller dry-run (`docs/testing/F0_DRY_RUN.md`): `line_control.py` con stati
  `FOLLOW`/`STOP`, nessuna seriale. Replay: retta 98/100 follow, curva 872/1584, gap 270/487,
  ombra parziale 578/608, ombra totale 416/900; comandi entro 0..255 e `motor_output=false`.
  Configurazione provvisoria: cruise 200, k_offset 0.35, k_heading 1.5, max correction 80.
- In corso: F0-5 movimento a bassa velocita': misurare PWM minimo e cm/s, poi collegare i
  motori solo dopo gate di sicurezza. Completare i segni IMU e chiudere i punti aperti di B0.
- Prossimi passi: misurare cm/s a PWM noto, tarare `cruise`/guadagni, implementare
  `GAP_CROSS` F1 con timeout e riacquisizione, poi prova a ruote sollevate e bassa velocita'.
- Differito: masse, baricentro, cablaggi completi, tarature ottiche, capacita' batteria,
  ruote/cinghie, servo e prove termiche esaurienti.
- Blocchi / decisioni aperte: regolamento 2027, ruote/cinghie, RPM, massa, servo, calibrazione
  BNO085, ruolo della UI e criteri di raccolta vittime.

## Note

- Il PDF regolamentare e il riferimento CAD sono indicati in `README.md` e `docs/`.
- Il file CAD resta un riferimento esterno read-only e non viene incluso nel repository.
- La provenienza dei documenti e le parti deliberatamente non importate sono in
  `docs/SOURCE_MAP.md`.
