# Test B0 - sicurezza sul banco

**ID:** B0-1
**Data:** 2026-10-31
**Firmware:** `firmware/rcj2027/rcj2027.ino` con configurazione di banco:
`BENCH_MOTION_ENABLED=true`, `PWM_MAX=150`, `WATCHDOG_TIMEOUT_MS=1000`
**Hardware:** Arduino Mega 2560 + L298N, USB `/dev/ttyACM0`, 115200 8N1
**Operatore:** agente su richiesta dell'utente; robot sollevato confermato dall'utente
**Condizioni:** ruote sollevate, alimentazione motori inserita, nessun sensore/servo.

## Sequenza e risultati

| # | Azione | Risposta | Esito |
|---:|---|---|---|
| 1 | `V,1*4B` | `V,1,ARDUINO_MEGA,1*61` + status `A,...` | PASS |
| 2 | `D,2,150,150*5A` | `K,2*55`; status con bit 2 = `4` | PASS |
| 3 | `X,3*47` mentre i motori girano | `K,3*54`; status successivo con bit 2 = `0` | PASS |
| 4 | `D,4,150,150*5C` | `K,4*53`; status con bit 2 = `4` | PASS |
| 5 | stop heartbeat | `E,WATCHDOG_STOP*2B`; status `8` | PASS |
| 6 | `X,5*41` | `K,5*52`; status `0` | PASS |

## Misure

- **Stop manuale `X`**: ack ricevuto dopo **3,9 ms**; il primo status con motori fermi e'
  arrivato dopo **98 ms** (il periodo dello status e' 100 ms, quindi il comando e' stato
  applicato subito).
- **Watchdog**: dall'ultimo `H` a `E,WATCHDOG_STOP`:
  - prova 1: **1007,3 ms**
  - prova 2: **1008,3 ms**
  con `WATCHDOG_TIMEOUT_MS=1000`.
- **Status dopo watchdog**: valore `8` = bit 3 (`WATCHDOG_TRIPPED`) attivo, bit 2
  (`MOTORS_ACTIVE`) spento. I motori risultano fermi.

## Cosa e' verificato

- handshake e status con motori attivi;
- comando `D` accettato con PWM 150 e ack;
- stop `X` con motori in movimento;
- perdita di heartbeat con arresto watchdog;
- status coerente prima e dopo l'arresto;
- firmware riportato alla configurazione sicura dopo il test: `BENCH_MOTION_ENABLED=false`,
  `PWM_MAX=0`, `WATCHDOG_TIMEOUT_MS=0`; `D` torna a rispondere `E,MOTION_DISABLED`.

## Cosa non e' ancora verificato

- conferma visiva del movimento e dell'arresto fisico delle ruote;
- comportamento freno/coast e spazio di arresto: il firmware usa coast (`EN=0`, `IN` bassi);
- ripetizione B0 su piu' run e con batteria a tensioni diverse;
- corrente e temperatura del L298N sotto carico;
- timeout watchdog definitivo: 1000 ms e' un valore di banco, non la scelta finale.

## Nota

`PWM_MAX=150` e' un valore di banco, non il `pwm_max` definitivo. Il test e' stato eseguito con
le ruote sollevate; nessun comando e' stato eseguito a terra.
