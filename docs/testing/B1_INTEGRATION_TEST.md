# Test B1-1 - integrazione seriale e logger

**ID:** B1-1
**Data:** 2026-10-31
**Firmware:** `firmware/rcj2027/rcj2027.ino` con configurazione sicura:
`BENCH_MOTION_ENABLED=false`, `PWM_MAX=0`, `WATCHDOG_TIMEOUT_MS=0`
**Software:** `software/rcj2027/session.py`, `transport.py`, `logger.py`, `__main__.py`
**Hardware:** Raspberry Pi 5 Model B + Arduino Mega 2560 + L298N, USB `/dev/ttyACM0`,
115200 8N1
**Ambiente:** Raspberry Pi OS, Linux 6.12 aarch64, Python 3.11.2, pyserial 3.5
**Condizioni:** robot fermo, movimento disabilitato, nessun comando `D` inviato, nessuna
modifica a hardware o cablaggi.

## Obiettivo

Verificare sul link reale, senza movimento:

- apertura del trasporto seriale e handshake `V`;
- heartbeat `H` periodico;
- ricezione degli status `A` con bitmask;
- stop `X` alla chiusura con ack;
- log JSONL associato a una run;
- comportamento ripetibile su piu' sessioni.

## Comando

```sh
cd software
python3 -m rcj2027 --port /dev/ttyACM0 --duration 5 --run-id b1-003
```

Il comando apre la porta, attende 2 s il boot del Mega, invia `V,1`, mantiene un heartbeat ogni
200 ms, legge gli status e alla chiusura invia `X`. Il movimento resta disabilitato dal firmware
e dal gate in `safety.py`.

## Risultati

Tre sessioni consecutive da 5 s con lo stesso firmware sicuro:

| Run | Risposta handshake | Frame pre-handshake scartati | Status | Sequenza status | Periodo medio | Heartbeat | Errori | Frame invalidi | Ack stop |
|---|---:|---:|---:|---|---:|---:|---:|---:|---:|
| b1-003 | 6,9 ms | 1 | 51 | 0 -> 50 | 100,2 ms (98-103) | 23 | 0 | 0 | 5 ms |
| b1-004 | 5,8 ms | 9 | 51 | 0 -> 50 | 100,2 ms (98-103) | 24 | 0 | 0 | 4 ms |
| b1-005 | 3,7 ms | 0 | 51 | 0 -> 50 | 100,1 ms (98-103) | 25 | 0 | 0 | 3 ms |

In tutte le run:

- handshake al primo tentativo, risposta `V,1,ARDUINO_MEGA,1`;
- 51 frame `A`, tutti con `status = 0`: nessun motore attivo, nessun watchdog scattato;
- `session_end.stop_ack = true`, `errors = 0`, `invalid_frames = 0`;
- nessun frame `D` inviato e nessun movimento osservato;
- il log contiene `session_start`, `handshake_ok`, `heartbeat`, `status`, `stop_sent`,
  `stop_ack` e `session_end`, tutti con lo stesso `run_id`.

La risposta dell'handshake e' misurata dal timestamp della richiesta `V` alla ricezione della
versione; il valore `elapsed_ms` nel log (circa 2007 ms) comprende invece i 2 s di attesa del
boot e non va usato come latenza del link.

## Anomalia osservata e correzione

La prima versione dell'handshake leggeva un numero fisso di dieci righe per tentativo. In una
run precedente (b1-002) il Mega stava gia' inviando status prima della risposta `V`: il buffer
conteneva molti frame `A` e alcuni frammenti dovuti all'apertura della porta a meta' frame. Il
risultato era 68 status, 3 frame invalidi e un handshake riuscito solo al terzo tentativo.

Correzione applicata prima delle run b1-003/004/005:

- l'handshake drena i frame in arrivo fino alla risposta `V`, entro un timeout, invece di
  fermarsi a un numero fisso di righe;
- i frame di status e i frammenti invalidi ricevuti prima dell'handshake vengono scartati e
  contati in `handshake_ok.discarded_frames`; non entrano nelle statistiche della sessione;
- `SerialTransport` accumula le righe parziali tra una lettura e l'altra, cosi' un timeout non
  produce un frame troncato.

Le tre run pulite confermano la correzione. L'anomalia e' registrata qui perche' fa parte
dell'evidenza reale, non e' un log di simulazione.

## Estratto del log b1-003

Estratto con campi non essenziali omessi; i valori citati sono quelli del log reale.

```json
{"event": "session_start", "mode": "real", "port": "/dev/ttyACM0", "baud": 115200, "safety": {"motion_enabled": false, "missing_for_motion": ["pwm_max", "watchdog_timeout_s"]}}
{"event": "handshake_request", "attempt": 1}
{"event": "version", "protocol": "1", "board": "ARDUINO_MEGA", "firmware": "1"}
{"event": "handshake_ok", "attempt": 1, "elapsed_ms": 2007.1, "response_ms": 6.9, "discarded_frames": 1}
{"event": "status", "sequence": 0, "distance_mm": -1, "yaw_mdeg": 0, "pitch_mdeg": 0, "roll_mdeg": 0, "status": 0, "flags": {"motors_active": false, "watchdog_tripped": false}}
{"event": "stop_sent", "sequence": 23}
{"event": "ack", "sequence": 23}
{"event": "stop_ack", "sequence": 23}
{"event": "session_end", "heartbeats": 23, "statuses": 51, "errors": 0, "invalid_frames": 0, "stop_ack": true}
```

I log completi restano in `software/logs/` (directory ignorata da git) o nella directory indicata
con `--log-dir`; non vengono versionati.

## Cosa e' verificato

- trasporto seriale reale su Raspberry Pi 5 e Arduino Mega 2560;
- handshake e versione del firmware;
- heartbeat ogni 200 ms e status ogni circa 100 ms;
- status con bitmask a 16 bit e flag `motors_active`/`watchdog_tripped` a zero;
- stop `X` alla chiusura con ack in 3-5 ms;
- log JSONL con `run_id`, timestamp UTC e configurazione di sicurezza;
- ripetibilita' su tre sessioni consecutive;
- nessun movimento e nessun comando `D` durante la prova.

## Cosa non e' ancora verificato

- perdita fisica del cavo USB durante la sessione: il caso e' coperto solo dal test host con
  trasporto finto, non da una prova con il cavo scollegato;
- valori reali di HC-SR04 e BNO085: il firmware invia ancora `distance_mm = -1` e angoli a zero;
- comandi motori e risposta `D`: non inviati in B1, restano coperti da B0/P1; il gate software
  `RobotSession.drive()` e' pronto e testato con trasporto finto, ma la prova B1-2 sul robot
  non e' stata eseguita;
- watchdog con timeout maggiore di zero e firmware di banco: la configurazione attuale ha
  `WATCHDOG_TIMEOUT_MS = 0`;
- sessioni lunghe, riconnessione USB e stabilita' su piu' ore;
- integrazione con la percezione e la UI.

Il gate B1 non e' chiuso: comunicazione e logger sono verificati, mentre motori e sensori
ripetibili restano da completare.

## Prossimo test B1-2 - comandi motori (non eseguito)

**Stato:** pianificato. `RobotSession.drive(left, right)` applica il gate di `safety.py`, limita
i valori a `pwm_max`, invia `D` e attende l'ack continuando gli heartbeat. La funzione e'
coperta dai test host, ma nessun comando `D` e' stato inviato al robot.

Prerequisiti obbligatori:

- ruote sollevate, confermate dall'operatore prima di iniziare;
- firmware di banco con `BENCH_MOTION_ENABLED=true`, `PWM_MAX` e `WATCHDOG_TIMEOUT_MS=1000`;
- configurazione Pi allineata allo stesso `pwm_max` e allo stesso timeout;
- operatore presente con alimentazione motori controllabile;
- valori di banco espliciti, non definitivi.

Sequenza prevista:

1. handshake e status con motori fermi;
2. `drive(100, 100)` e attesa `K`;
3. `run(1.0)` per mantenere heartbeat e status con bit 2 attivo;
4. `stop()` e verifica `K` e bit 2 a zero;
5. ripetizione con canali separati e verso opposto;
6. registrazione di latenze, corrente e temperatura.

Esempio di sessione, da usare solo con ruote sollevate:

```python
from rcj2027.logger import JsonlLogger
from rcj2027.safety import HardwareConfig
from rcj2027.session import RobotSession
from rcj2027.transport import SerialTransport

config = HardwareConfig(
    battery_nominal_v=11.1,
    motor_side_map={"A": "right", "B": "left"},
    motor_direction_polarity={"A": "inverted", "B": "inverted"},
    pwm_max=150,
    watchdog_timeout_s=1.0,
)

with JsonlLogger("logs/b1-2.jsonl", "b1-2") as logger:
    with SerialTransport("/dev/ttyACM0", 115200) as transport:
        with RobotSession(transport, logger, config=config) as session:
            session.handshake(boot_delay_s=2.0)
            session.drive(100, 100)
            session.run(1.0)
            session.stop()
```

I valori `pwm_max=150` e `watchdog=1.0 s` sono di banco. Il test va eseguito solo dopo la
conferma delle ruote sollevate; l'esito e le misure andranno aggiunti a questo documento e a
`docs/MEASUREMENT_LOG.md`. Non eseguire la sessione con il robot a terra.

## Note

- La prova e' stata eseguita con il firmware sicuro gia' caricato; non e' stato necessario
  riprogrammare il Mega.
- `D` resta rifiutato con `E,MOTION_DISABLED` finche' `pwm_max` e timeout watchdog non sono
  scelti e il gate di `safety.py` non viene completato.
- Nessuna misura di corrente, temperatura o movimento e' stata eseguita in B1.
