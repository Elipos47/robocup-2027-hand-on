# Piano test hardware e campo

## Regola generale

Ogni test ha un identificativo, una data, una versione del software, una configurazione hardware,
un operatore e un risultato. Una prova non ripetibile non chiude un gate.

## Livelli

### L0 — sicurezza

- alimentazione e limiti;
- freno e direzione;
- stop di emergenza;
- comportamento con controller bloccato.

### L1 — comunicazione

- handshake e versione;
- heartbeat;
- comando e risposta;
- fuori range;
- perdita cavo e watchdog.

### L2 — sensori

- camera linea e camera vittime;
- HC-SR04;
- BNO085/IMU;
- eventuale servo;
- calibrazione manuale documentata.

### L3 — movimento

- linee reali;
- gap e disturbi;
- curvature;
- ostacolo;
- salite e discese;
- stanza, linea argentata, vittime e goal.

## Condizioni da registrare

- batteria e tensione;
- luminosita' e superficie;
- temperatura se rilevante;
- carico e ruote/cinghie montate;
- versione del firmware e del software;
- numero di prove e fallimenti.

## Criteri di superamento

- nessun movimento oltre il limite di sicurezza;
- stop entro il tempo misurato;
- comportamento ripetibile nella condizione dichiarata;
- log completo e associato alla run;
- discrepanze annotate, non nascoste.

## Log minimo

```text
run_id, data, operatore, hardware, firmware, software,
condizioni, test, esito, evento, azione, video/foto, note
```

## Dati minimi prima del test di movimento

Prima di eseguire qualsiasi comando con i motori collegati, devono essere confermati almeno:

- tensione nominale della batteria (acquisita: 11.1 V);
- asse e verso dei due motori;
- limite PWM prudente impostato nel codice e stop verificato a banco.

I campi sono definiti in `docs/hardware/MINIMUM_HARDWARE_DATA.md`. Un campo `TODO` non viene
sostituito con una stima: se riguarda la sicurezza, il movimento resta disabilitato.

## Test ancora da creare

- [x] sketch di banco per le direzioni dei motori (`firmware/test/motor_direction_test/`),
  polarita' e mappa lati verificate;
- [x] raccolta dei dati minimi: lati e verso dei motori;
- [x] comunicazione V/H/X/D con movimento disabilitato (P1,
  `docs/testing/PROTOCOL_BENCH_TEST.md`);
- [x] stop X con ponte abilitato (B0, `docs/testing/B0_BENCH_TEST.md`);
- [x] watchdog con ponte abilitato e perdita di heartbeat (B0, 1007-1008 ms);
- [x] rotazione visiva a 255 (confermata dall'operatore);
- [x] sessione seriale reale Raspberry-Mega con handshake, heartbeat, status a 10 Hz, logger
  JSONL e stop `X` (B1-1, `docs/testing/B1_INTEGRATION_TEST.md`);
- [x] comandi motori con gate, ack e stop durante il movimento (B1-2, ruote sollevate,
  rotazione confermata dall'operatore);
- [x] lettura HC-SR04 e BNO085 con bit di validita' (B1-3,
  `docs/testing/B1_SENSORS_TEST.md`);
- [ ] calibrazione distanza di riferimento del sonar e assi IMU;
- [ ] perdita fisica del cavo USB durante una sessione reale;
- [ ] freno/coast e arresto fisico misurato;
- [ ] ripetizione B0 su piu' run;
- [ ] calibrazione manuale camere;
- [ ] linea sul campo;
- [ ] elementi missione;
- [ ] percorso completo;
- [ ] misure estese di batterie, masse, cablaggi e tarature.
