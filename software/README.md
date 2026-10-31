# Software Raspberry Pi

Python per percezione, stato, logging, interfaccia operatore e comunicazione con l'Arduino.

## Struttura

```text
software/
  rcj2027/
    protocol.py    codifica/decodifica del protocollo seriale v1.1
    transport.py   trasporto pyserial e trasporto finto per i test
    logger.py      log JSONL con run_id e timestamp UTC
    safety.py      gate di movimento e configurazione hardware
    __main__.py    demo del livello di comunicazione
  tests/           test host con unittest
  requirements.txt pyserial per il trasporto reale
```

## Comandi

```sh
cd software
python3 -m rcj2027 --run-id demo-001
python3 -m unittest discover -s tests -t . -v
```

La demo usa il trasporto finto: non apre la porta seriale e non muove il robot. I log finiscono
in `logs/` (ignorata da git) oppure nella directory indicata con `--log-dir`.

Per usare la porta reale, dopo aver scritto il firmware del protocollo:

```sh
python3 -m rcj2027 --port /dev/ttyACM0 --baud 115200 --run-id prova-001
```

## Configurazione

`DEFAULT_CONFIG` in `safety.py` contiene i dati verificati a banco:

- batteria 11.1 V;
- canale A = ruota destra, canale B = ruota sinistra;
- polarita' di entrambi i canali invertita.

`pwm_max` e `watchdog_timeout_s` sono ancora vuoti: finche' mancano, `motion_enabled` e' falso e
il gate rifiuta il movimento. Non sono valori di fallback.

## Regole

- Il movimento reale resta disabilitato finche' i parametri di sicurezza non sono completi.
- Ogni funzione ha un test ripetibile e un log associato.
- Il trasporto finto serve a testare il protocollo senza robot; non e' un simulatore del
  percorso.
- Le dipendenze stanno in un venv locale, non nel repository.
