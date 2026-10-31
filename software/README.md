# Software Raspberry Pi

Python per percezione, stato, logging, interfaccia operatore e comunicazione con l'Arduino.

## Stato

Fase di avvio: struttura del package e primi moduli (parser del protocollo, logger, trasporto
finto) da scrivere. Nessun codice applicativo del progetto precedente viene importato.

## Layout previsto

- `software/`: package Python e moduli applicativi.
- `software/tests/`: test host.
- Il trasporto finto serve a testare il protocollo senza robot; non e' un simulatore del
  percorso.

## Regole

- Il movimento reale resta disabilitato finche i dati di sicurezza non sono confermati.
- Ogni funzione ha un test ripetibile e un log associato.
- Le dipendenze stanno in un venv locale, non nel repository.
