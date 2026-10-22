# Robocup2027HandOn

## Obiettivo

Progetto documentale hardware-first per RoboCupJunior Rescue Line 2027. Il software viene
sviluppato in coordinamento con misure, collaudo a banco e prove sul campo; il progetto non
dipende da un simulatore e non contiene il codice applicativo sviluppato nel progetto precedente.

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

- Git: repository inizializzato su `main`; i checkpoint sono automatici. Il push e' regolato
  dalla sezione «Remoto e push»; `reset --hard`, rebase e riscritture di storia restano vietati.
- La fonte di verita' hardware e' `docs/hardware/`; ogni misura reale va registrata con data,
  strumento, condizione e incertezza in `docs/MEASUREMENT_LOG.md`.
- Per iniziare il software si usa il contratto minimo in
  `docs/hardware/MINIMUM_HARDWARE_DATA.md`: non richiedere un inventario completo di schede,
  masse, cavi o CAD se non e' necessario al codice richiesto.
- I parametri non critici possono restare `TODO`; quelli di sicurezza mancanti devono
  disabilitare il movimento reale e non diventare valori di fallback.
- Il regolamento 2026 e' provvisorio fino a disposizione del regolamento ufficiale 2027.
- Non modificare hardware, cablaggi, firmware o collegamenti senza approvazione esplicita.
- Non introdurre simulatori, log di simulazione o codice applicativo copiato dal progetto
  precedente senza una decisione documentata e una prova hardware che lo giustifichi.
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
- A fine turno, se hai modificato file e il checkpoint automatico e' gia' avvenuto: verifica
  `bash scripts/check_context.sh` verde, `git status --short` vuoto e nessun segreto
  (`git grep -nEi 'password|api[_-]?key|secret|token|BEGIN (RSA|OPENSSH)|192\.168\.'`),
  poi esegui `git push origin main`.
- Mai `push --force`, `reset --hard`, rebase o riscritture di storia. Se il remoto e'
  divergente, fermati e chiedi.
- Se il push fallisce per autenticazione, non inventare token o credenziali: fermati e
  segnalalo all'utente.
- I PDF in `docs/rules/` e `docs/hardware/Misure Robotica.pdf` sono ridistribuiti nel repo:
  con un repo pubblico verifica che la ridistribuzione sia ammessa prima di pushare.

## Stato attuale

- Fatto: struttura documentale iniziale, inventario hardware, riferimento CAD, regolamento
  provvisorio, piano hardware-first, architettura e protocollo seriale come proposta.
- Fatto: `docs/hardware/Misure Robotica.pdf` raccoglie gli ingombri di molte schede; sono un
  input per il CAD, non ancora parametri operativi del controller.
- Fatto: definito `docs/hardware/MINIMUM_HARDWARE_DATA.md` come contratto minimo, ridotto ai
  tre dati che il software non puo' dedurre: tensione, asse e verso dei motori.
- Fatto: batteria acquisita il 2026-10-22 (etichetta): 2 pacchi Li-Ion 3S 11.1 V 2.6 Ah
  28.86 Wh in parallelo, cioe' 11.1 V, 5.2 Ah, 57.72 Wh dichiarati. `battery_nominal_v` e'
  compilato; il resto dell'etichetta non serve al contratto software.
- In corso: raccolta dei pochi dati minimi necessari e definizione dei test di banco.
- Prossimi passi: compilare i campi di Priorita 1 del registro, proporre la mappa dei pin,
  definire seriale e logger, poi collaudare freni/arresto e comunicazione Raspberry-Arduino.
- Differito: masse, baricentro, cablaggi completi, tarature ottiche, capacita' batteria,
  ruote/cinghie, servo e prove termiche esaurienti.
- Blocchi / decisioni aperte: regolamento 2027, ruote/cinghie, RPM, massa, servo, BNO085,
  ruolo della UI e criteri di raccolta vittime.

## Note

- Il PDF regolamentare e il riferimento CAD sono indicati in `README.md` e `docs/`.
- Il file CAD resta un riferimento esterno read-only e non viene incluso nel repository.
- La provenienza dei documenti e le parti deliberatamente non importate sono in
  `docs/SOURCE_MAP.md`.
