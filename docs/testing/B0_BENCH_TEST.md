# Test B0 - sicurezza sul banco

**ID:** B0-1
**Data:** 2026-10-31
**Firmware:** `firmware/rcj2027/rcj2027.ino` con configurazione di banco:
`BENCH_MOTION_ENABLED=true`, `PWM_MAX=150` e poi `255`, `WATCHDOG_TIMEOUT_MS=1000`
**Hardware:** Arduino Mega 2560 + L298N, USB `/dev/ttyACM0`, 115200 8N1
**Operatore:** agente su richiesta dell'utente; robot sollevato confermato dall'utente
**Condizioni:** ruote sollevate, alimentazione motori inserita, nessun sensore/servo.

## Sequenza e risultati

| # | Azione | Risposta | Esito |
|---:|---|---|---|
| 1 | `V,1*4B` | `V,1,ARDUINO_MEGA,1*61` + status `A,...` | PASS |
| 2 | `D,2,150,150*5A` | `K,2*55`; status con bit 2 = `4` | PASS |
| 3 | `X,3*47` mentre il ponte e' abilitato | `K,3*54`; status successivo con bit 2 = `0` | PASS |
| 4 | `D,4,150,150*5C` | `K,4*53`; status con bit 2 = `4` | PASS |
| 5 | stop heartbeat | `E,WATCHDOG_STOP*2B`; status `8` | PASS |
| 6 | `X,5*41` | `K,5*52`; status `0` | PASS |

La prova a 150 ha prodotto solo ronzio: il firmware ha abilitato il ponte (status bit 2 = 4), ma
i motori non sono partiti. La prova a 255 ha ricevuto lo stesso comando e i motori hanno girato:
rotazione confermata dall'operatore il 2026-10-31.

## Prova a 255

La stessa sequenza e' stata ripetuta con `PWM_MAX=255`:

| # | Azione | Risposta | Esito |
|---:|---|---|---|
| 1 | `D,2,255,255*5A` | `K,2*55`; status bit 2 = `4` | PASS |
| 2 | `X,3*47` mentre i motori sono abilitati | `K,3*54`; status fermo al frame successivo | PASS |
| 3 | `D,4,255,255*5C` | `K,4*53`; status bit 2 = `4` | PASS |
| 4 | stop heartbeat | `E,WATCHDOG_STOP*2B`; status `8` | PASS |

- stop `X`: ack dopo **3,7 ms**, status fermo dopo **99,3 ms**;
- watchdog: **1007,3 ms** dall'ultimo `H`;
- **rotazione visiva a 255: confermata dall'operatore.**

### Test per canale a 255

| Fase | Tx | Rx | Esito |
|---|---|---|---|
| Solo sinistra (B) | `D,2,255,0*58` | `K,2*55`; status bit 2 = `4` | PASS |
| Solo destra (A) | `D,4,0,255*5E` | `K,4*53`; status bit 2 = `4` | PASS |
| Entrambi | `D,6,255,255*5E` | `K,6*51`; status bit 2 = `4` | PASS |
| Watchdog | `D,8,255,255*50` + stop `H` | `E,WATCHDOG_STOP*2B` dopo **1004,9 ms**; status `8` | PASS |

La rotazione e' stata osservata dall'operatore a 255, sia sui canali singoli sia con entrambi.

`PWM_MAX=255` e' un valore di banco, non il `pwm_max` definitivo.

## Misure

- **Stop manuale `X`**: ack ricevuto dopo **3,9 ms**; il primo status con motori fermi e'
  arrivato dopo **98 ms** (il periodo dello status e' 100 ms, quindi il comando e' stato
  applicato subito).
- **Watchdog**: dall'ultimo `H` a `E,WATCHDOG_STOP`:
  - prova 1: **1007,3 ms**
  - prova 2: **1008,3 ms**
  - prova per canale: **1004,9 ms**
  con `WATCHDOG_TIMEOUT_MS=1000`.
- **Status dopo watchdog**: valore `8` = bit 3 (`WATCHDOG_TRIPPED`) attivo, bit 2
  (`MOTORS_ACTIVE`) spento. I motori risultano fermi.

## Cosa e' verificato

- handshake e status con ponte abilitato;
- comando `D` accettato con PWM 150 e 255; a 150 i motori ronzavano senza ruotare, a 255 hanno
  girato (conferma dell'operatore);
- stop `X` con ponte abilitato;
- perdita di heartbeat con arresto watchdog;
- status coerente prima e dopo l'arresto;
- firmware riportato alla configurazione sicura dopo il test: `BENCH_MOTION_ENABLED=false`,
  `PWM_MAX=0`, `WATCHDOG_TIMEOUT_MS=0`; `D` torna a rispondere `E,MOTION_DISABLED`.

## Cosa non e' ancora verificato

- comportamento freno/coast e spazio di arresto: il firmware usa coast (`EN=0`, `IN` bassi);
- ripetizione B0 su piu' run e con batteria a tensioni diverse;
- corrente e temperatura del L298N sotto carico;
- timeout watchdog definitivo: 1000 ms e' un valore di banco, non la scelta finale.

## Nota

`PWM_MAX=150` e `PWM_MAX=255` sono valori di banco, non il `pwm_max` definitivo. Il test e'
stato eseguito con le ruote sollevate; nessun comando e' stato eseguito a terra.
