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
  007 con target spostato a ~600 mm ha mediana 597 mm e 9,2% outlier, FAIL.
- Fatto: firmware Arduino del protocollo v1.1 in `firmware/rcj2027/`, compilato; movimento
  disabilitato di default.
- Fatto: protocollo verificato a banco senza movimento (test P1 in
  `docs/testing/PROTOCOL_BENCH_TEST.md`): V, H, status, X e `D` rifiutato con
  `MOTION_DISABLED`.
- Fatto: B0 parziale con motori attivi (test B0-1 in `docs/testing/B0_BENCH_TEST.md`): stop X
  con ack 3,7-3,9 ms e watchdog a 1004,9-1008,3 ms con PWM 150/255 e timeout 1000 ms. A 150 i
  motori ronzavano senza ruotare; a 255 hanno girato (conferma dell'operatore). Firmware
  riportato a movimento disabilitato.
- In corso: ripetere il sonar con bersaglio stabile e riferimento metrico, verificare messa a
  fuoco/montaggio della CSI e calibrare le camere con checkerboard; validare i segni IMU e
  chiudere i punti aperti di B0.
- Prossimi passi: usare `python3 -m rcj2027.diagnostics` per sonar/camera/IMU, definire la
  convenzione dei segni pitch/roll, sistemare la messa a fuoco della CSI, poi passare a F0.
- Differito: masse, baricentro, cablaggi completi, tarature ottiche, capacita' batteria,
  ruote/cinghie, servo e prove termiche esaurienti.
- Blocchi / decisioni aperte: regolamento 2027, ruote/cinghie, RPM, massa, servo, calibrazione
  BNO085, ruolo della UI e criteri di raccolta vittime.

## Note

- Il PDF regolamentare e il riferimento CAD sono indicati in `README.md` e `docs/`.
- Il file CAD resta un riferimento esterno read-only e non viene incluso nel repository.
- La provenienza dei documenti e le parti deliberatamente non importate sono in
  `docs/SOURCE_MAP.md`.
