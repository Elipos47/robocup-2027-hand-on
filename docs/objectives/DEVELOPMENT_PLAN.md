# Piano di sviluppo hardware-first

## Principio

Il software viene scritto in coordinamento con i progressi hardware e con test sul campo. La
fase di codice e' iniziata: firmware di banco e software Raspberry vivono nel repository, ma un
comportamento non e' considerato pronto perche' esiste un test statico, unita' o una previsione:
servono evidenze sul robot reale, condizioni di prova e un log associato.

## Fasi

### H0a — Contratto minimo hardware

- raccogliere solo i tre dati che il software non puo' dedurre: tensione della batteria, asse e
  verso dei motori;
- trattare pin, PWM, freno, seriale, camera e sensori come scelte di codice o dati da scoprire
  durante le prove;
- usare `docs/hardware/MINIMUM_HARDWARE_DATA.md` come fonte unica dei parametri minimi;
- mantenere espliciti i TODO e non dedurre valori dal CAD, dalle foto o dai nomi dei moduli;
- permettere lo scaffolding di protocollo, logger e moduli di percezione anche con dati non
  critici ancora mancanti;
- mantenere disabilitato il movimento reale se mancano i parametri di sicurezza.

### H0b — Inventario e misure estese

- completare foto, ingombri, masse, cablaggi, ruote/cinghie e tarature;
- registrare le misure con data, strumento, condizione e incertezza;
- tenere separati fatti, stime e TODO.

H0b non e' un prerequisito per iniziare a scrivere il software.

### D0 — Codice di banco

- layout `firmware/` per Arduino e `software/` per il Raspberry;
- build riproducibile con `scripts/build.sh`;
- sketch di test con README, comandi e risultato atteso;
- nessuna pretesa di missione o di movimento autonomo.

### B0 — Sicurezza e banco

- verificare alimentazione e limiti di corrente;
- provare freno e verso motori con ruote sollevate;
- verificare stop di emergenza e comportamento in caso di crash;
- misurare latenza e affidabilita' della comunicazione.

### B1 — Primitive software

- heartbeat e watchdog;
- logger strutturato;
- comandi motori con limiti;
- lettura dei sensori e diagnostica;
- calibrazione manuale delle telecamere.

Stato 2026-10-31: B1-1 verificata sul link reale Raspberry Pi 5 - Mega con firmware sicuro
(handshake, heartbeat, status, logger JSONL, stop `X`). B1-2 verificata con ruote sollevate e
conferma dell'operatore: comandi a 255 su entrambe le ruote e sui canali separati, ack, stop e
rotazione osservata; firmware sicuro ripristinato. B1-3: HC-SR04 e BNO085 letti nello status.
Valori operativi `pwm_max=255` e watchdog 1.0 s in `OPERATIONAL_CONFIG`, con gate predefinito
chiuso. Calibrazione di sonar, assi IMU e camere ancora da completare.

### F0 — Linea

- test su linee reali, curvature, gap, disturbi e illuminazione;
- misurare deviazione e ripresa dopo perdita linea;
- non usare coordinate di percorso al posto della percezione.

Stato 2026-11-01: F0-1 avviato. `line_vision.py` implementa undistort CSI, ROI, soglia
adattiva, scanline top-down, fit parabolico, confidenza e tracker; la CLI `line` analizza
sequenze e `line-live` elabora la CSI in tempo reale con vista locale o stream MJPEG. Test
host e verifica undistort passano.
Prova reale su linea retta con robot fermo: 30/30 frame, offset -46,0 px, heading 3,95 deg,
confidenza 0,95; live 100 frame in 5,04 s a 19,8 FPS, 100/100 trovati.

Stato 2026-11-03: F0-2 tentativo 1 su curva. Nei tratti in cui la linea entra nella ROI viene
seguita con confidenza 0,86-0,965 e 6 riprese; il nastro disponibile e' piu' largo di 1-2 cm ed
e' un proxy di banco. La telecamera e' volutamente vicina, quindi la curva puo' uscire dalla
ROI: F0-2 e' coperto sul banco senza raggio ne' linea regolamentare. Il report live ora misura
`camera_start_s`, `warmup_s` e `first_frame_s` (2,08-2,19 s nelle run strumentate; 18,73 s nella
run curva e' anomalo). Disturbi, illuminazione e movimento non sono ancora provati: F0 non
e' chiuso.

Stato 2026-11-03: F0-3 ombra parziale, tentativo 1: 608/608 frame trovati, 0 perdite,
confidenza 0,663-0,978. L'ombra era probabilmente leggera; restano da provare un'ombra netta
su 1/3-2/3 e l'occlusione totale. Nella prova di bassa luce il rilevatore agganciava un bordo
sottile (10-31 px contro 188-190) con offset errato; aggiunto il guard di continuita' di
larghezza, da validare live. F0-3 non e' chiuso.

Stato 2026-11-03: F0-4 gap da 7 cm (`docs/testing/F0_GAP_TEST.md`): 513 frame, 251/513
trovati, 266 confermati, 6 riprese, FOUND sui segmenti e LOST nel vuoto. Corretti seme
isolato e filtro di larghezza. Terza run 182854: 487 frame, 284/487 trovati, 304 confermati,
6 riprese, frame 120 FOUND. **F0-4 chiuso sul banco**; l'attraversamento resta F1.

Stato 2026-11-03: F0-5 controller dry-run (`docs/testing/F0_DRY_RUN.md`). `line_control.py`
produce comandi FOLLOW/STOP senza seriale; replay: retta 98/100, curva 872/1584, gap 270/487,
ombra parziale 578/608, ombra totale 416/900. Configurazione provvisoria. Restano PWM minimo,
cm/s e movimento reale.

### F1 — Elementi di missione

ostacolo, marker, salite/discese, velocita' variabile, linea argentata, stanza, vittime e uscita.
Ogni elemento ha una prova isolata e una prova di integrazione.

### C0 — Gara

- percorso completo ripetuto;
- condizioni di batteria, luce e superficie registrate;
- report con eventi, errori, tempi e prove video/foto;
- revisione delle discrepanze tra prova e regolamento.

## Regola di avanzamento

Un parametro non critico mancante puo restare `TODO` e non blocca lo scaffolding del software.
Un parametro di sicurezza mancante blocca il movimento reale. Non si passa al gate successivo
se il safety gate e' in rosso. Un test fallito e' un dato da correggere, non un motivo per
dichiarare l'elemento opzionale.
