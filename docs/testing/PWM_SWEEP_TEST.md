# Test PWM - sweep di banco

**ID:** F0-5 / PWM-1
**Data:** 2026-11-03
**Software:** `software/pwm_sweep.py`, `RobotSession.drive`, firmware `rcj2027`
**Hardware:** Raspberry Pi 5 + Arduino Mega 2560 + L298N, ruote sollevate
**Firmware di prova:** `BENCH_MOTION_ENABLED=true`, `PWM_MAX=255`, watchdog 1000 ms

## Sequenza

Conferma esplicita dell'operatore: ruote sollevate e robot fissato.

| Gradino | PWM | Durata | Esito comando |
|---:|---:|---:|---|
| 1 | 150 | 4,003 s | `D` accettato |
| 2 | 175 | 4,015 s | `D` accettato |
| 3 | 200 | 4,020 s | `D` accettato |
| 4 | 225 | 4,014 s | `D` accettato |
| 5 | 255 | 4,017 s | `D` accettato |

Tra i gradini: stop `X` e pausa di 2 s. Log:
`software/logs/pwm-sweep-001.jsonl`.

## Esito software

- 5 comandi `D` accettati, nessun `drive_rejected` o timeout.
- `motors_active=true` durante ogni gradino.
- 0 errori, 0 frame invalidi, 0 frame scartati.
- `stop_ack=true` alla chiusura; watchdog non scattato.
- Il firmware e' stato riportato alla configurazione sicura
  (`BENCH_MOTION_ENABLED=false`, `PWM_MAX=0`, watchdog 0).

Il percorso software quindi arriva a `setMotors` e imposta i pin. Il codice di
`setChannelA/B` usa gli stessi pin e `analogWrite` del test
`firmware/test/motor_direction_test`, che in B0 aveva fatto girare le ruote.

## Esito meccanico

**Nessuna rotazione** a 150, 175, 200, 225 o 255. L'operatore riferisce un suono
sempre alla stessa frequenza. Nota: la frequenza PWM e' fissa (circa 490 Hz);
cambiare duty cambia il valore medio, non la frequenza del ronzio. Il dato
critico e' che a 255, con `motors_active=true`, le ruote non girano.

## Interpretazione

Non c'e' evidenza di un errore nel percorso software. Le cause da isolare sono
alimentazione/enable/L298N o corrente di spunto con entrambi i motori:

1. tensione batteria ai morsetti +12/GND del L298N sotto comando;
2. tensione ENA/ENB (pin 12/13) a 150 e 255;
3. uscita motore del L298N a 255;
4. GND comune Arduino/L298N;
5. jumper ENA/ENB e collegamento dei pin;
6. prova di un solo canale a 255 con `motor_direction_test`.

La prova a un canale e' il passo successivo: se un motore gira da solo, il
problema e' di alimentazione/corrente con entrambi i canali; se non gira
neanche da solo, e' nel cablaggio/alimentazione del L298N.

## Esito finale della sessione

Dopo il controllo dei collegamenti, **entrambi i motori funzionano sia singolarmente sia in
coppia a 255**. Il guasto precedente non si e' ripetuto e la causa non e' stata identificata:
il sospetto resta un connettore o un contatto instabile su ENA/ENB, IN o uscite motore.

Questo e' un rischio di affidabilita': prima della gara vanno ripetuti piu' cicli a coppia e
controllati i serraggi. La velocita' massima non e' ancora misurata.

## Prossimo passo

1. Diagnosi del guasto sotto carico del 2026-11-04
   (`docs/testing/MOTOR_POWER_DIAGNOSTIC.md`): batteria/BMS, L298N, connettori, canale A.
2. Ripetere il test a coppia 3 volte a ruote sollevate solo dopo la diagnosi.
3. Misurare PWM minimo e cm/s a PWM noto, con ruote sollevate/prima a bassa velocita'.
4. Tarare `cruise` e guadagni del controller dry-run.
5. Ripetere la prova del controller prima di collegare i motori al firmware operativo.
6. Implementare `GAP_CROSS` F1 solo dopo la misura di velocita' e i test di ripresa.

## Test entrambi i canali a 255

E' pronto lo sketch `firmware/test/pwm_both_test/`:

- attende 3 s dal reset;
- avanti entrambi a 255 per 4 s, stop 2 s;
- indietro entrambi a 255 per 4 s, stop 2 s;
- due cicli e stop finale.

Risultato della prova: **la ruota sinistra gira, la destra no**. La velocita'
osservata e' lenta, ma con un solo motore attivo non e' una misura valida di
velocita' massima.

## Test canali separati

Per isolare il guasto e' pronto `firmware/test/pwm_channel_test/`:

- A avanti 255, stop;
- B avanti 255, stop;
- A indietro 255, stop;
- B indietro 255, stop.

Risultato: **entrambi i canali funzionano separatamente**. Quindi motori e
canali A/B sono singolarmente ok; il problema compare quando sono attivi
insieme. La velocita' massima non e' ancora misurabile in modo valido.

## Test avvio scaglionato

E' pronto `firmware/test/pwm_staggered_test/`:

- A da solo per 2 s, poi aggiungo B per 4 s;
- stop 2 s;
- B da solo per 2 s, poi aggiungo A per 4 s;
- stop finale.

Serve a distinguere un limite di alimentazione/corrente (fallisce il secondo
motore aggiunto) da un canale/motore che fallisce sempre. Il file e' compilato
ma non caricato.

## Test a coppia 255 - 2026-11-04 (F0-5 / PWM-2)

**Scopo:** ripetere 3 volte la coppia a 255 per verificare l'affidabilita' dopo il guasto
intermittente del 2026-11-03.

**Software:** `pwm_sweep.py` esteso ai PWM negativi (positivo = avanti, negativo = indietro);
firmware `rcj2027` con `BENCH_MOTION_ENABLED=true`, `PWM_MAX=255`,
`WATCHDOG_TIMEOUT_MS=1000`.
**Sequenza:** 3 x (avanti 255 per 3 s, stop 2 s, indietro -255 per 3 s, stop 2 s).
**Log:** `software/logs/pwm-pair-repeat-001.jsonl`.

**Deviazione:** il robot e' stato appoggiato sul tavolo invece di essere lasciato con le ruote
sollevate. La prova e' quindi un test **sotto carico**, non la ripetizione a ruote sollevate
prevista. Non chiude il criterio "ruote sollevate", ma e' un dato utile per il comportamento
reale.

### Esito software

| Fase | Comando | Ack | Status con motori attivi | Stop |
|---|---|---:|---:|---|
| 1 avanti | 255,255 | 7 ms | 30 campioni, ~2,9 s | ack |
| 2 indietro | -255,-255 | 6 ms | 30 campioni, ~2,9 s | ack |
| 3 avanti | 255,255 | 7 ms | 31 campioni, ~3,0 s | ack |
| 4 indietro | -255,-255 | 6 ms | 31 campioni, ~3,0 s | ack |
| 5 avanti | 255,255 | 7 ms | 31 campioni, ~3,0 s | ack |
| 6 indietro | -255,-255 | 6 ms | 30 campioni, ~2,9 s | ack |

6/6 comandi `D` accettati, 6/6 stop con ack, 0 errori, 0 frame invalidi, `motors_active`
coerente. Il firmware sicuro e' stato ripristinato e `D` risponde `E,MOTION_DISABLED`.

### Esito fisico

- prima fase avanti: entrambe le ruote girano;
- prima fase indietro: la ruota destra non gira;
- fasi successive: entrambe le ruote fanno uno scatto iniziale e poi si fermano.

**Esito: FAIL sotto carico.** Il percorso software e' sano; il guasto e' a valle dei pin
(alimentazione, L298N, connettori o motore). Le ipotesi e la procedura di diagnosi sono in
`docs/testing/MOTOR_POWER_DIAGNOSTIC.md`.

Il test a coppia resta aperto: non e' stata ottenuta una ripetizione consecutiva valida a
ruote sollevate. PWM minimo, cm/s e taratura del controller sono sospesi fino alla diagnosi.

### Seconda run con multimetro (F0-5 / PWM-2b, 2026-11-04)

**Scopo:** ripetere la stessa sequenza con il multimetro in DC su `+12`/`GND` del L298N per
distinguere un problema di batteria/BMS da un problema del ponte o dei motori.
**Log:** `software/logs/pwm-pair-repeat-002.jsonl`.
**Condizione:** ruote sollevate e robot fissato, confermati dall'operatore.

| Fase | Comando | Ack | Status con motori attivi |
|---|---|---:|---:|
| 1 avanti | 255,255 | 7 ms | 30 campioni, ~2,9 s |
| 2 indietro | -255,-255 | 7 ms | 30 campioni, ~2,9 s |
| 3 avanti | 255,255 | 8 ms | 30 campioni, ~2,9 s |
| 4 indietro | -255,-255 | 7 ms | 31 campioni, ~3,0 s |
| 5 avanti | 255,255 | 5 ms | 30 campioni, ~2,9 s |
| 6 indietro | -255,-255 | 7 ms | 30 campioni, ~2,9 s |

6/6 comandi accettati, 0 errori, 6/6 stop con ack.

**Esito fisico:** stesso comportamento della prima run: prima avanti con entrambe le ruote,
poi ruota destra ferma in retromarcia e fasi successive con solo uno scatto iniziale.

**Tensione `+12`/`GND` del L298N:** stabile **10-12 V** per tutta la prova (multimetro in DC,
lettura a display non campionata).

**Conseguenza:** batteria, BMS e caduta di tensione sul collegamento di alimentazione sono
esclusi come causa primaria. Il guasto e' nel L298N (canale A o protezione termica), nel motore
destro o nei connettori. Il passo successivo e' il test dei canali separati con misura di
`OUT1`/`OUT2` e `OUT3`/`OUT4` e della temperatura del L298N
(`docs/testing/MOTOR_POWER_DIAGNOSTIC.md`).
