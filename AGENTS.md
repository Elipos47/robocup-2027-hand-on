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
# install:  arduino-cli core install arduino:avr; dipendenze Python in software/
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
- Layout del codice: `firmware/` per gli sketch Arduino, `software/` per il Python del
  Raspberry, `firmware/test/<nome>/<nome>.ino` per gli sketch di banco. Ogni sketch di test ha
  un `README.md` con cablaggio, comandi e risultato atteso.
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
  piano hardware-first, architettura e protocollo seriale come proposta.
- Fatto: contratto minimo ridotto ai tre dati che il software non puo' dedurre: tensione,
  asse e verso dei motori. Batteria 11.1 V da etichetta (2 pacchi Li-Ion 3S in parallelo).
- Fatto: mappa pin L298N (ENA/ENB 12/13, IN1..IN4 22..25), HC-SR04 (TRIG 27, ECHO 26) e
  BNO085 (SDA 20, SCL 21); breakout Adafruit BNO085 confermato compatibile con I2C a 5 V.
- Fatto: primo sketch di banco in `firmware/test/motor_direction_test/`, compilato con
  `bash scripts/build.sh`. Prova a banco in corso: la polarita' di entrambi i canali e'
  invertita, corretta nel software e riverificata (`1`/`3` avanti); manca la mappa
  sinistra/destra.
- In corso: fase di sviluppo codice; determinare lati e velocita' dei motori, poi seriale e
  logger.
- Prossimi passi: confermare la mappa sinistra/destra e la velocita' reale, completare il
  contratto minimo, scrivere parser e logger con movimento disabilitato, poi collaudare
  freni/arresto e comunicazione Raspberry-Arduino.
- Differito: masse, baricentro, cablaggi completi, tarature ottiche, capacita' batteria,
  ruote/cinghie, servo e prove termiche esaurienti.
- Blocchi / decisioni aperte: regolamento 2027, ruote/cinghie, RPM, massa, servo, BNO085,
  ruolo della UI e criteri di raccolta vittime.

## Note

- Il PDF regolamentare e il riferimento CAD sono indicati in `README.md` e `docs/`.
- Il file CAD resta un riferimento esterno read-only e non viene incluso nel repository.
- La provenienza dei documenti e le parti deliberatamente non importate sono in
  `docs/SOURCE_MAP.md`.
