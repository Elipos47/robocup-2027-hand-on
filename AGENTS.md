# Robocup2027HandOn

## Obiettivo

Progetto documentale hardware-first per RoboCupJunior Rescue Line 2027. Il software viene
sviluppato in coordinamento con misure, collaudo a banco e prove sul campo; il progetto non
dipende da un simulatore e non contiene il codice sviluppato nel progetto precedente.

## Stack

- Documentazione Markdown e PDF ufficiali.
- Raspberry Pi 5 4GB e Arduino Mega 2560 come piattaforma hardware prevista.
- Python e C++/Arduino come possibili linguaggi futuri, solo dopo le verifiche hardware.
- OpenCV e sensori fisici per la percezione; nessun simulatore incluso nella baseline.
- Prove su banco e sul campo; il test sul campo e' il criterio di avanzamento principale.

## Comandi

```sh
# install:  nessuna dipendenza; clonare il repository
# validate: bash scripts/check_context.sh
# test:     bash scripts/check_context.sh
# build:    echo "documentation-only project"
# lint:     git diff --check
```

<Esegui questi comandi con cwd in questa cartella.>

## Convenzioni

- Git: repository inizializzato su `main`; i checkpoint sono automatici. Non usare `push`,
  `reset --hard`, rebase o riscritture di storia senza richiesta esplicita.
- La fonte di verita' hardware e' `docs/hardware/`; ogni misura reale va registrata con data,
  strumento, condizione e incertezza in `docs/MEASUREMENT_LOG.md`.
- Il regolamento 2026 e' provvisorio fino a disposizione del regolamento ufficiale 2027.
- Non modificare hardware, cablaggi, firmware o collegamenti senza approvazione esplicita.
- Non introdurre simulatori, log di simulazione o codice copiato dal progetto precedente senza
  una decisione documentata e una prova hardware che lo giustifichi.
- I TODO sono parte del contesto: non riempirli con valori inventati o inferenze non verificate.
- I segreti stanno in `.env`, mai nel repository; non salvare credenziali, token o porte seriali
  reali con password.
- La lingua dei documenti e' italiano; nomi di file e simboli tecnici restano in inglese quando
  sono standard o servono per la compatibilita' con l'hardware.

## Stato attuale

- Fatto: struttura documentale iniziale, inventario hardware, riferimento CAD, regolamento
  provvisorio, piano hardware-first, architettura e protocollo seriale come proposta.
- In corso: raccolta delle misure reali e definizione dei test di banco.
- Prossimi passi: verificare batterie, motori, ruote/cinghie, masse, sensori, IMU, servo e
  cablaggi; poi collaudare freni/arresto e comunicazione Raspberry↔Arduino.
- Blocchi / decisioni aperte: regolamento 2027, ruote/cinghie, batterie, RPM, massa, servo,
  BNO085, ruolo della UI e criteri di raccolta vittime.

## Note

- Il PDF regolamentare e il riferimento CAD sono indicati in `README.md` e `docs/`.
- Il file CAD resta un riferimento esterno read-only e non viene incluso nel repository.
- La provenienza dei documenti e le parti deliberatamente non importate sono in
  `docs/SOURCE_MAP.md`.
