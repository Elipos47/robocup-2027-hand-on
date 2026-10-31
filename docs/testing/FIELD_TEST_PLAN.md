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

- [ ] raccolta dei dati minimi per il software;
- [ ] test freno e direzione motori;
- [ ] test comunicazione e watchdog;
- [ ] calibrazione manuale camere;
- [ ] linea sul campo;
- [ ] elementi missione;
- [ ] percorso completo;
- [ ] misure estese di batterie, masse, cablaggi e tarature.
