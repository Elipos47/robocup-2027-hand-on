# Test di banco del protocollo v1.1

**ID:** P1
**Data:** 2026-10-31
**Firmware:** `firmware/rcj2027/rcj2027.ino`, configurazione di default
(`BENCH_MOTION_ENABLED=false`, `PWM_MAX=0`, `WATCHDOG_TIMEOUT_MS=0`)
**Hardware:** Arduino Mega 2560 + L298N, USB `/dev/ttyACM0`, 115200 8N1
**Operatore:** agente, script seriale su richiesta dell'utente
**Condizioni:** movimento disabilitato; nessun comando motore accettato; sensori e servo non
implementati.

## Comandi e risposte

| # | Tx | Rx | Esito |
|---:|---|---|---|
| 1 | `V,1*4B` | `V,1,ARDUINO_MEGA,1*61`, poi `A,0,-1,0,0,0,0*6D` e successivi | PASS |
| 2 | `H,1*55` | nessun ack; status `A,11...` e successivi | PASS |
| 3 | `X,2*46` | `K,2*55`, poi status `A,17...` | PASS |
| 4 | `D,1,100,100*59` | `E,MOTION_DISABLED*38` | PASS |

Lo status viene inviato ogni circa 100 ms. I frame osservati hanno distanza `-1`, angoli `0` e
status `0`: nessun motore attivo, watchdog non scattato, sensori non validi.

## Cosa e' verificato

- framing ASCII e checksum XOR;
- handshake `V` e versione firmware;
- status periodico `A` con sequenza crescente;
- heartbeat `H` senza ack;
- stop `X` con ack immediato;
- gate di movimento: `D` rifiutato con `E,MOTION_DISABLED` a movimento disabilitato.

## Cosa non e' verificato

- watchdog con motori attivi e tempo reale di arresto;
- `D` accettato con movimento abilitato;
- perdita del cavo e riconnessione;
- lettura HC-SR04, BNO085 e comando servo.

## Riproduzione

Caricare il firmware con la configurazione di default, poi inviare i frame della tabella dal
Serial Monitor a 115200 con line ending Newline, oppure usare la console interattiva:

```sh
cd software
python3 -m rcj2027 --port /dev/ttyACM0 --interactive --run-id p1-ripetizione
```

Il prossimo test e' B0 con i motori attivi: configurazione di banco, ruote sollevate e misura
del tempo di watchdog.
