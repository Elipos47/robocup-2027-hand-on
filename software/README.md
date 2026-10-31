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
    __main__.py    demo, sessione reale e console manuale
  tests/           test host con unittest
  requirements.txt pyserial per il trasporto reale
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
