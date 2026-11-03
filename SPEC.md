# SPEC — Robocup2027HandOn

**Versione:** 0.12
**Data:** 01/11/2026
**Stato:** sviluppo attivo; protocollo v1.1 implementato e verificato a banco. B0 parziale:
rotazione a 255, stop e watchdog verificati; freno/coast e ripetizione da completare. B1-1:
sessione reale con handshake, heartbeat, status, logger e stop. B1-2: comandi motori a 255 con
gate, ack, stop e rotazione confermata. B1-3: HC-SR04 e BNO085 letti nello status. B1-4:
diagnostica software per camera, sonar e IMU; camera e IMU passano, sonar valido ma instabile.
Calibrazioni USB e CSI accettate; F0-1: primo pipeline linea con undistort, rilevamento,
tracker e CLI, verificato sui test host, su 30 frame reali di una linea retta (30/30) e in
live a 19,8 FPS, con vista locale o stream MJPEG, debug mask e durata fino a q/ESC. F0-2
coperto sul banco con curva e nastro proxy piu' largo di 1-2 cm, senza richiedere raggio o
linea regolamentare. Gap, ombre e movimento restano da provare. Valori operativi
`pwm_max=255` e watchdog 1.0 s in `OPERATIONAL_CONFIG`; gate predefinito chiuso. Movimento
reale disabilitato di default.

## 1. Obiettivo

Costruire il software del robot Rescue Line 2027 in modo coordinato con i progressi reali
dell'hardware. Ogni decisione software deve partire da una misura o da un comportamento
osservato sul banco/sul campo; il progetto non usa un simulatore come criterio di accettazione.

Il risultato finale deve permettere al robot di:

- seguire la linea nera e gestire i tratti speciali previsti dal regolamento;
- reagire a marker, terreni, ostacoli e cambi di direzione con azioni sicure;
- entrare nella zona di evacuazione, riconoscere vittime e linea argentata secondo le prove
  validate sul campo;
- completare il percorso e registrare telemetria e risultati riproducibili.

## 2. Hardware di riferimento

| Componente | Ruolo previsto | Stato |
|---|---|---|
| Raspberry Pi 5 4GB | elaborazione, visione, logica, UI | presente |
| Arduino Mega 2560 | motori, PWM, sensori, servo, watchdog | presente |
| Camera linea | visione della linea | presente, montaggio da verificare |
| Camera stanza/vittime | visione vittime | presente, montaggio da verificare |
| HC-SR04 | distanza frontale | presente, range da verificare |
| BNO085 | IMU | modello/ruolo da confermare |
| L298N | pilotaggio motori | presente, dropout da considerare |
| Batterie | alimentazione | 11.1 V Li-Ion 3S da etichetta, 2 pacchi in parallelo |
| UPS | continuità alimentazione Raspberry | presente |
| Servo | meccanismo ausiliario | modello e funzione da verificare |
| Ruote/cinghie | locomozione | modello e dimensioni mancanti |
| Schermo | diagnostica operatore | presente, interfaccia da definire |

## 2.1 Dati minimi per il software

Il progetto non richiede un inventario hardware completo prima di iniziare a scrivere il
software. Il contratto minimo e' definito in `docs/hardware/MINIMUM_HARDWARE_DATA.md` e comprende:

- tensione nominale della batteria (11.1 V da etichetta);
- asse e verso dei motori: A = ruota destra, B = ruota sinistra; entrambi invertiti e corretti
  nel software.

Le quote degli ingombri raccolte in `docs/hardware/Misure Robotica.pdf` sono risorse per il CAD e
non sostituiscono questi parametri. I valori mancanti restano `TODO` e bloccano solo la funzione
che ne dipende.

Il codice vive in `firmware/` (Arduino Mega) e `software/` (Raspberry Pi); gli sketch di banco
stanno in `firmware/test/<nome>/<nome>.ino` con un `README.md` che descrive cablaggio, comandi e
risultato atteso.

## 3. Architettura

- Il Raspberry gestisce percezione, decisione di alto livello, logging e interfaccia.
- Arduino gestisce attuatori e sensori a bassa latenza, con heartbeat e stop sicuro.
- La comunicazione seriale e' versionata, leggibile e protetta da una scadenza di sicurezza.
- Il protocollo v1.1 usa checksum XOR, ack e status bitmask; il lato Raspberry e' implementato
  in `software/rcj2027/` e il lato Arduino in `firmware/rcj2027/`.
- Il controller non usa coordinate di percorso al posto di sensori e IMU.
- La telemetria deve distinguere stato, sensori, attuatori, errori e prove.

## 4. Regole di sviluppo

1. Nessuna modifica hardware senza approvazione esplicita.
2. Ogni misura usata dal software ha provenienza, data, strumento e incertezza; un dato non
   confermato resta `TODO` e non viene ricostruito da stime o CAD.
3. I parametri non critici possono mancare durante lo scaffolding; i parametri di sicurezza
   mancanti disabilitano il movimento reale.
4. Ogni funzione software ha un test ripetibile e un log.
5. I test statici non sostituiscono una prova sul campo.
6. I fallimenti di sicurezza hanno precedenza sulla missione.
7. Il regolamento Rescue Line 2026 e' provvisorio; le differenze 2027 devono essere registrate
   prima di modificarne l'implementazione.
8. Il progetto non contiene codice o log importati dal precedente repository.
9. Ogni sketch di banco ha un `README.md` con cablaggio, comandi e risultato atteso.
10. Il firmware si compila con `scripts/build.sh` prima dell'upload; i test di movimento si
    eseguono con ruote sollevate e alimentazione controllata.
11. Il software Pi si testa con `bash scripts/test.sh`; il gate di movimento rifiuta i comandi
    se `pwm_max` o il timeout watchdog mancano.

## 5. Gate di avanzamento

### Gate H0 — contratto hardware minimo

I dati minimi sono tensione della batteria, asse e verso dei motori, in
`docs/hardware/MINIMUM_HARDWARE_DATA.md`. La mappa dei pin e' una decisione di progetto
registrata nello stesso documento; l'inventario esteso non e' un prerequisito per scrivere il
codice.

### Gate D0 — codice di banco

Build riproducibile e sketch di test con README. Non abilita ancora il movimento autonomo.

### Gate B0 — bench safety

Freni, verso motori, stop di emergenza, watchdog e perdita seriale verificati a robot sollevato.

Stato 2026-10-31: rotazione a 255, stop e watchdog verificati con ponte abilitato (B0-1); a 150
i motori ronzavano senza ruotare. Freno/coast e ripetizione da completare.

### Gate B1 — primitive

Comunicazione, heartbeat, logger, motori e sensori ripetibili su banco.

Stato 2026-10-31: B1-1 verificata su Raspberry Pi 5 con firmware sicuro (handshake, heartbeat
a 200 ms, status a circa 100 ms, log JSONL, stop `X` con ack, nessun movimento). B1-2 verificata
con ruote sollevate e conferma dell'operatore: comandi a 255 su entrambe le ruote e sui canali
separati, ack e stop in pochi ms, rotazione osservata; firmware sicuro ripristinato. B1-3:
HC-SR04 e BNO085 letti nello status, bit 0+1. B1-4: diagnostica software con probe camera
USB/CSI, calibrazione checkerboard e analisi sonar/IMU; USB e IMU passano, pitch/roll scambiati
sul montaggio e corretti, calibrazione USB accettata (RMS 0,523 px, copertura 22,7%). Ruoli:
USB = stanza/vittime/palline, CSI = linea; la CSI e' nitida con autofocus, 1280x720 full-fov
verificata e calibrazione accettata (RMS 0,542 px, copertura 16,3%). Il sonar a 500 mm e'
accettato per ostacoli piu' vicini di 0,5 m (run 005/006 con target fermo). Verifica undistort,
segni IMU e misure termiche restano da completare; il gate B1 non e' ancora chiuso.

### Gate F0 — line

Tracking della linea con prove su tratti reali, gap e disturbi; nessuna claim basata solo su
unità o test sintetici.

Stato 2026-11-01: pipeline F0-1 implementato in `software/rcj2027/line_vision.py` con
undistort CSI, ROI, adaptive threshold, scanline top-down, fit robusto, confidenza, tracker e
CLI. Verifica undistort sulle immagini di calibrazione PASS (0,4392 -> 0,4287 px); test host
verdi. Prova reale su linea retta con robot fermo: 30/30 frame trovati, offset -46,0 px,
heading 3,95 deg, confidenza 0,95, 0 perdite. Loop `line-live`: 100 frame in 5,04 s, 19,8 FPS,
100/100 trovati.

Stato 2026-11-03: F0-2 tentativo 1 su curva reale (`docs/testing/F0_CURVE_TEST.md`). Nei
tratti in cui la linea entra nella ROI viene seguita con confidenza 0,86-0,965, con 6 riprese
e nessun falso confermato evidente. La telecamera e' volutamente vicina: la curva puo' uscire
dalla ROI. F0-2 e' coperto sul banco con il nastro proxy (piu' largo di 1-2 cm); non richiede
raggio fisico. Resta la compatibilita' con la linea regolamentare. Il report live ora separa
`camera_start_s`, `warmup_s` e `first_frame_s`: primo frame 2,08-2,19 s nelle run strumentate;
il ritardo di 18,73 s della run curva e' anomalo.

Il gate resta aperto per gap, disturbi, illuminazione e movimento.

### Gate F1 — mission elements

Ostacolo, salite/discese, marker, stanza, linea argentata e vittime provati singolarmente.

### Gate C0 — full course

Run complete ripetute sul campo, con report, eventi, errori e condizioni di illuminazione.

## 6. Criteri di qualità

- Nessuna funzione dichiarata pronta senza evidenza ripetibile.
- Stop e watchdog verificati anche in presenza di crash o perdita di comunicazione.
- Dati hardware separati da stime e TODO.
- Log JSON/CSV leggibili e associati a una run identificabile.
- Comandi e errori spiegabili all'operatore.
- Il risultato deve poter essere riprodotto sul banco o nel campo.

## 7. Esclusioni

Il progetto non contiene:

- simulatori o mondi di simulazione;
- log di prove simulate;
- copia del codice sviluppato nel progetto precedente;
- parametri inventati per colmare dati hardware mancanti.

## 8. Riferimenti

- `firmware/`
- `firmware/rcj2027/`
- `software/rcj2027/`
- `scripts/`
- `docs/hardware/INVENTORY.md`
- `docs/hardware/MINIMUM_HARDWARE_DATA.md`
- `docs/hardware/Misure Robotica.pdf`
- `docs/hardware/CAD_REFERENCE.md`
- `docs/rules/`
- `docs/architecture/SYSTEM_ARCHITECTURE.md`
- `docs/testing/FIELD_TEST_PLAN.md`
- `docs/MEASUREMENT_LOG.md`
