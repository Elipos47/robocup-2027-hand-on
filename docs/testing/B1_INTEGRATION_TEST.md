# Test B1-1/B1-2 - sessione seriale, logger e comandi motori

**ID:** B1-1 (link e logger), B1-2 (comandi motori)
**Data:** 2026-10-31
**Firmware:** B1-1 con configurazione sicura (`BENCH_MOTION_ENABLED=false`, `PWM_MAX=0`,
`WATCHDOG_TIMEOUT_MS=0`). B1-2 con configurazione di banco (`true`, `PWM_MAX=255`,
`WATCHDOG_TIMEOUT_MS=1000`), poi ripristinata la configurazione sicura.
**Software:** `software/rcj2027/session.py`, `transport.py`, `logger.py`, `__main__.py`
**Hardware:** Raspberry Pi 5 Model B + Arduino Mega 2560 + L298N, USB `/dev/ttyACM0`,
115200 8N1
**Ambiente:** Raspberry Pi OS, Linux 6.12 aarch64, Python 3.11.2, pyserial 3.5
**Condizioni:** B1-1 con robot fermo e movimento disabilitato, nessun comando `D`. B1-2 con
ruote sollevate confermate dall'operatore, alimentazione motori inserita e operatore presente.

## Obiettivo

Verificare sul link reale:

- B1-1, senza movimento: trasporto seriale, handshake `V`, heartbeat `H`, status `A`,
  stop `X`, log JSONL e ripetibilita';
- B1-2, con ruote sollevate: comandi motori `D`, ack, status `MOTORS_ACTIVE`, stop `X` e
  rotazione fisica.

## B1-1 - comando

```sh
cd software
python3 -m rcj2027 --port /dev/ttyACM0 --duration 5 --run-id b1-003
```

Il comando apre la porta, attende 2 s il boot del Mega, invia `V,1`, mantiene un heartbeat ogni
200 ms, legge gli status e alla chiusura invia `X`. Il movimento resta disabilitato dal firmware
e dal gate in `safety.py`.

## B1-1 - risultati

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

## B1-1 - cosa e' verificato

- trasporto seriale reale su Raspberry Pi 5 e Arduino Mega 2560;
- handshake e versione del firmware;
- heartbeat ogni 200 ms e status ogni circa 100 ms;
- status con bitmask a 16 bit e flag `motors_active`/`watchdog_tripped` a zero;
- stop `X` alla chiusura con ack in 3-5 ms;
- log JSONL con `run_id`, timestamp UTC e configurazione di sicurezza;
- ripetibilita' su tre sessioni consecutive;
- nessun movimento e nessun comando `D` durante la prova.

## Limiti dopo B1-1/B1-2

- perdita fisica del cavo USB durante la sessione: il caso e' coperto solo dal test host con
  trasporto finto, non da una prova con il cavo scollegato;
- calibrazione di HC-SR04 e BNO085: lettura e bitmask verificati in B1-3
  (`docs/testing/B1_SENSORS_TEST.md`), ma distanza di riferimento, orientamento assi e deriva
  yaw restano da misurare;
- verso di rotazione in B1-2: la rotazione e' stata confermata, non il verso avanti/indietro
  (gia' verificato in B0);
- watchdog e spazio di arresto durante il movimento: B0 ha verificato lo stop a 1000 ms, ma
  B1-2 non ha misurato lo spazio fisico di arresto;
- corrente e temperatura del L298N sotto carico;
- sessioni lunghe, riconnessione USB e stabilita' su piu' ore;
- integrazione con la percezione e la UI.

Il gate B1 resta aperto per calibrazione e misure. Comunicazione, logger, comandi motori e
lettura dei sensori sono verificati.

## Test B1-2 - comandi motori

**Stato:** eseguito il 2026-10-31 con ruote sollevate e conferma visiva dell'operatore.

### Configurazione di banco

| Parametro | Valore |
|---|---|
| Firmware | `BENCH_MOTION_ENABLED=true`, `PWM_MAX=255`, `WATCHDOG_TIMEOUT_MS=1000` |
| Configurazione Pi | `pwm_max=255`, `watchdog_timeout_s=1.0` |
| Ruote | sollevate, confermate dall'operatore |
| Alimentazione motori | inserita, operatore presente |
| Valori | di banco, non definitivi |

Al termine la configurazione sicura e' stata ricaricata e verificata: `drive(100, 100)` ha
risposto `E,MOTION_DISABLED`, status `0`, nessun movimento.

### Sequenza e risultati

La prima sequenza (run b1-2) ha inviato quattro comandi: `100,100` per 0,5 s, `255,255` per
1 s, `255,0` e `0,255` per 0,5 s. Tutti gli ack `D` sono arrivati in 6-7 ms, gli stop in 3-6 ms
e lo status e' passato da `4` (`MOTORS_ACTIVE`) a `0` dopo ogni stop; 0 errori e 0 frame
invalidi. L'operatore non ha pero' osservato la rotazione, quindi la run non e' stata accettata
come verifica visiva: il bit 2 indica il ponte abilitato, non il movimento fisico.

La seconda sequenza (run b1-2b) ha inserito un countdown di 3 s prima del comando. Gli status
accumulati hanno riempito la coda e il vecchio loop di attesa ack, fermo a dieci righe, ha
prodotto `ACK_TIMEOUT`; anche gli stop hanno inviato `X` ma non hanno letto l'ack
(`stop_ack_timeout`). I comandi `X` sono stati inviati e il firmware li applica subito, ma
l'ack non e' stato letto; la run e' un test fallito ed e' registrata come tale. La correzione ha
reso `_wait_for_ack` e `stop` dei cicli che drenano fino alla deadline, con test di regressione
su 20 status in coda.

La terza sequenza (run b1-2c) e' quella valida:

| Fase | Comando | Durata | Ack `D` | Status durante | Stop ack | Status dopo |
|---|---|---:|---:|---:|---:|---:|
| Entrambe | `D,255,255` | 2 s | 6 ms | 4 | 5 ms | 0 |
| Solo sinistra | `D,255,0` | 1 s | 5 ms | 4 | 2 ms | 0 |
| Solo destra | `D,0,255` | 1 s | 6 ms | 4 | 2 ms | 0 |

- 0 errori e 0 frame invalidi;
- 32 heartbeat e 133 status nella sessione (i countdown hanno accumulato telemetria, poi drenata);
- stop finale di chiusura con ack in 4 ms;
- **rotazione osservata dall'operatore a 255 su entrambe le ruote e sui due canali separati.**

### Cosa e' verificato in B1-2

- `RobotSession.drive()` invia `D` reali solo con gate completo e valori entro `pwm_max`;
- ack `D` e stop `X` con latenze di pochi ms;
- status `MOTORS_ACTIVE` coerente prima e dopo ogni comando;
- rotazione fisica a 255 su entrambe le ruote e sui canali separati;
- stop di sicurezza su rifiuto/timeout e ripristino del firmware sicuro;
- `D` torna `MOTION_DISABLED` con la configurazione sicura.

### Cosa non e' verificato in B1-2

- verso avanti/indietro: B1-2 ha confermato la rotazione, non il verso; la verifica del verso
  resta quella di B0;
- corrente, temperatura e spazio di arresto sotto carico;
- `pwm_max` e timeout watchdog definitivi;
- comportamento del watchdog durante il movimento in questa sessione: B0 lo copre con valori di
  banco;
- ripetizione su batteria piu' scarica e su piu' run.

## Note

- B1-1 e' stata eseguita con il firmware sicuro gia' caricato; B1-2 ha richiesto tre cicli di
  upload di banco e altrettanti ripristini della configurazione sicura.
- `D` resta rifiutato con `E,MOTION_DISABLED` finche' `pwm_max` e timeout watchdog non sono
  scelti e il gate di `safety.py` non viene completato.
- Nessuna misura di corrente o temperatura e' stata eseguita in B1.
