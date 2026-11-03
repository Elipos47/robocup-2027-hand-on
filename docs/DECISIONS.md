# Decisioni aperte e scelte

## Scelte prese

1. **Hardware-first:** il software viene coordinato con misure e prove sul campo.
2. **Nessun simulatore come gate:** il progetto non dipende da Webots o da altri ambienti
   simulati; nessun codice del progetto precedente viene importato.
3. **Regolamento 2026 provvisorio:** i PDF 2026 sono la base fino alla pubblicazione 2027.
4. **STEP esterno:** il file CAD resta fuori dal repository e viene solo referenziato.
5. **TODO espliciti:** dati hardware mancanti non vengono inventati o dedotti dal solo CAD.
6. **Prove ripetibili:** ogni funzione richiede una prova, un test, un log e una spiegazione
   per l'operatore.
7. **Sicurezza prima della missione:** stop e watchdog hanno precedenza sul percorso.
8. **Contratto hardware minimo:** restano solo i dati che il software non puo' dedurre:
   tensione della batteria, asse e verso dei motori. PWM, freno, seriale, camera e sensori sono
   scelte di codice o si scoprono provando; l'inventario esteso resta differito.
9. **Batterie in parallelo:** due pacchi Li-Ion 3S da 11.1 V 2.6 Ah 28.86 Wh in parallelo,
   quindi 11.1 V e 5.2 Ah / 57.72 Wh dichiarati. In parallelo la tensione resta la stessa; i
   pacchi si collegano solo a tensione uguale e con protezioni compatibili. Corrente, BMS e
   cutoff non sono requisiti del contratto software: si osservano sul campo se servono.
10. **Fase codice (2026-10-31):** il repository non e' piu' documentation-only. Il codice nuovo
    vive in `firmware/` (Arduino) e `software/` (Python); gli sketch di banco stanno in
    `firmware/test/<nome>/<nome>.ino` con un README. Restano validi hardware-first, nessun
    simulatore, nessun codice del progetto precedente e prova reale come criterio di
    avanzamento.
11. **Protocollo v1.1 e software Pi (2026-10-31):** checksum XOR su ogni frame, ack
    `K,<sequence>` per i comandi, status a 16 bit. Il package `software/rcj2027/` implementa
    parser, trasporto finto, logger e gate di sicurezza; il firmware Arduino e' in
    `firmware/rcj2027/`.
12. **Firmware protocollo v1.1 (2026-10-31):** implementato in `firmware/rcj2027/` con
    checksum, ack, status, stop e watchdog. Il movimento e' disabilitato di default; il
    protocollo e' verificato a banco senza movimento (P1). Il test B0-1 ha verificato rotazione
    a 255, stop e watchdog con ponte abilitato; a 150 i motori ronzavano senza ruotare.
    Freno/coast e ripetizione restano aperti. Per il test B0 si usano valori di banco espliciti
    (PWM 150/255, watchdog 1000 ms), non definitivi.
13. **Sessione seriale e logger (2026-10-31):** `software/rcj2027/session.py` gestisce
    handshake, heartbeat, status, errori, stop e log JSONL. L'handshake drena gli status gia'
    in coda prima della risposta `V` e scarta i frame pre-handshake; il trasporto seriale
    bufferizza le righe parziali. B1-1 ha verificato la catena reale Raspberry Pi 5 - Mega con
    firmware sicuro, senza movimento (`docs/testing/B1_INTEGRATION_TEST.md`). La perdita fisica
    del cavo e i comandi motori restano fuori da B1-1.
14. **Gate comandi motori (2026-10-31):** `RobotSession.drive(left, right)` richiede il gate di
    `safety.py` completo, limita i valori a `pwm_max`, invia `D` solo dopo l'handshake e attende
    l'ack continuando gli heartbeat. Su rifiuto o timeout invia `X` e solleva
    `CommandRejected`. Non e' esposto dalla CLI. B1-2 e' stata eseguita con ruote sollevate e
    conferma dell'operatore: comandi a 255 su entrambe le ruote e sui canali separati, rotazione
    osservata, firmware sicuro ripristinato. Un tentativo intermedio ha esposto un `ACK_TIMEOUT`
    da backlog di status; `_wait_for_ack` e `stop` ora drenano fino alla deadline.
15. **Valori operativi (2026-10-31):** `pwm_max=255` e' la scelta dell'operatore dopo B1-2; il
    watchdog di `1.0 s` e' l'unico timeout misurato a banco (stop a 1004-1008 ms, B0). I valori
    stanno in `OPERATIONAL_CONFIG` e vanno passati esplicitamente; `DEFAULT_CONFIG` resta
    incompleto e il gate predefinito resta chiuso. Il firmware sicuro continua a rifiutare `D`.
16. **Sensori B1-3 (2026-10-31):** HC-SR04 letto con state machine non bloccante (TRIG 27,
    ECHO 26) e distanza in mm; BNO085 su I2C `0x4A` con `SH2_GAME_ROTATION_VECTOR`, quaternione
    convertito in yaw/pitch/roll mdeg. Il BNO085 non e' pronto subito al boot, quindi
    l'inizializzazione viene ritentata ogni secondo. Status bit 0 `SONAR_VALID` e bit 1
    `IMU_VALID`. Orientamento assi e distanza di riferimento restano da calibrare.
17. **Diagnostica software B1-4 (2026-10-31):** `sensor_checks.py` analizza sonar e IMU,
    `camera_checks.py` misura frame e rileva checkerboard, `camera_calibration.py` calcola la
    matrice intrinseca, `checkerboard.py` genera il target PDF a dimensione reale e
    `diagnostics.py` espone i comandi con exit code 0/1/2. Camera USB e IMU stazionario/yaw
    passano; la CSI acquisisce ma e' sfocata e il sonar e' valido ma il salto di ~695 mm fa
    fallire il test di stabilita'. Le soglie non vengono abbassate senza una prova con target
    stabile.
18. **Montaggio IMU (2026-10-31):** pitch e roll del BNO085 sono fisicamente scambiati rispetto
    al telaio. Il firmware applica `IMU_SWAP_PITCH_ROLL=true`; non e' una calibrazione del
    sensore. I test pitch e roll passano con l'asse dominante corretto. La convenzione dei segni
    e il comportamento dopo un rimontaggio restano da verificare.
19. **Sonar 500 mm accettato (2026-10-31):** con target fermo a ~500 mm le run 005/006 passano
    con mediana 522/507,5 mm, outlier 3,0%/1,0% e riferimento entro ±50 mm. L'operatore accetta
    questo test per ostacoli piu' vicini di 0,5 m; il test a 1000 mm non e' necessario ora. Il
    test resta FAIL se il target si muove.
20. **Calibrazione USB accettata (2026-11-01):** 15/15 immagini, pattern 9x6, lato reale
    23,75 mm, RMS 0,523 px, copertura media 22,7% (20,0-31,3%), focale ~248 px. Accettata come
    prima calibrazione della USB a 640x480 e salvata in
    `software/rcj2027/calibrations/usb_640x480.json`. La copertura e' appena sopra il minimo:
    una calibrazione con target piu' grande puo' migliorare l'RMS.
21. **Ruoli telecamere (2026-11-01):** la **USB 5MP** e' la camera stanza/vittime e palline;
    la **CSI IMX708** e' la camera linea. La calibrazione USB a 640x480 vale solo per la stanza.
    La CSI va calibrata alla risoluzione di lavoro della linea; **1280x720** e' la candidata e
    la probe passa con nitidezza normalizzata 149,3. La preview puo' mostrare piu' campo dello
    still perche' 1280x720 usa il modo 1536x864 con crop 2x; `--full-fov` forza il sensore
    intero 2304x1296 e con checkerboard completo da' 54 corner e `passed=true`. La nitidezza e'
    normalizzata a 640 px per confrontare risoluzioni diverse.
22. **Diversita' delle pose per la calibrazione (2026-11-01):** il calibratore rifiuta set con
    dispersione dei centri < 40 px e rapporto dimensioni < 1,05, perche' viste quasi identiche
    non vincolano focale e distorsione. Con copertura 14-20% e pose diverse si puo' usare
    `--min-coverage 0.14`; il set CSI con 15 frame identici (spread 0,6 px) e' stato rifiutato.
23. **Calibrazione CSI accettata (2026-11-01):** 14/15 viste, copertura 16,3% (12,6-24,4%),
    pose spread 423,6 px, size ratio 1,93, RMS 0,542 px, focale ~957/963 px, centro ~(654, 373).
    Accettata come prima calibrazione della linea a 1280x720 full-fov e salvata in
    `software/rcj2027/calibrations/csi_1280x720.json`. L'undistort va verificato in F0; se
    peggiora la linea, rifare con target piu' grande o piu' pose.
24. **Primo pipeline linea F0 (2026-11-01):** `line_vision.py` usa la calibrazione CSI, ROI
    inferiore, adaptive threshold con fallback scuro per linee larghe, scansione top-down,
    stop dopo un gap e continuita' di larghezza; il fit e' parabolico robusto. Convenzione:
    offset positivo a destra, heading positivo a destra; valori in pixel finche' non c'e' la
    trasformazione al piano del pavimento. La confidenza combina copertura del tratto, residuo
    del fit e regolarita' della larghezza; il tracker conferma dopo 3 frame e perde lo stato
    dopo 5. La verifica undistort sulle immagini di calibrazione passa (0,4392 -> 0,4287 px)
    ma non e' una prova indipendente. Prova reale su linea retta, robot fermo: 30/30 frame
    trovati, offset -46,0 px, heading 3,95 deg, confidenza 0,95, 0 perdite. Curvature, gap,
    illuminazione e movimento restano il criterio per chiudere F0.
25. **Loop live della linea (2026-11-01):** `line-live` usa Picamera2 in configurazione video
    1280x720 full-fov, applica la calibrazione a ogni frame e scrive un JSONL con offset,
    heading, confidenza e tracker. Prima prova: 100 frame in 5,04 s (19,8 FPS), 100/100 trovati,
    offset -46,5 px, heading 4,14 deg, confidenza 0,95, nessun comando ai motori. Il costo e'
    circa 40 ms di elaborazione per frame; il controller resta il passo successivo. La vista
    live usa una finestra OpenCV (`--preview`) o uno stream MJPEG locale (`--http-port`), senza
    autenticazione: solo rete locale. `--debug-overlay` aggiunge la maschera di segmentazione,
    `--duration 0` acquisisce fino a `q`/ESC, il browser ha un pulsante di stop e
    `software/line_live.py` e' l'avvio da Thonny.
26. **ROI near-field e test curva (2026-11-03):** la telecamera linea e' montata vicino alla
    tile per non comandare in anticipo; la ROI e' una finestra sul near-field e la curva puo'
    uscire dall'inquadratura. Il test F0-2 non richiede che l'intera curva resti nella ROI ne'
    un raggio fisico noto: valuta il rilevamento nei tratti in ROI, l'assenza di falsi quando
    la linea esce e la ripresa quando rientra. Il nastro disponibile e' piu' largo di 1-2 cm:
    e' un proxy di banco, non una prova regolamentare.
27. **Continuita' di larghezza nel tracker (2026-11-03):** in bassa luce il rilevatore puo'
    agganciare un bordo sottile della linea (10-31 px contro 188-190 px) e produrre un offset
    sbagliato. `LineTracker` rifiuta un restringimento brusco rispetto alla larghezza attesa;
    un aumento graduale e' ammesso quando la linea entra nel campo o si avvicina. Il report
    live distingue `found`, `tracked_found`, `width_rejected_frames` e `confirmed_frames`;
    `control_passed` usa i frame confermati, non il found ratio grezzo. Da validare con una
    run live e una vera occlusione.
28. **Gap F0 (2026-11-03):** il gap disponibile e' 7 cm, entro il limite 2026 di 20 cm. F0
    valuta perdita e ripresa, non l'attraversamento (F1). Lo stop sul gap scatta solo dopo aver
    agganciato almeno `min_valid_rows` righe; un seme isolato non deve fermare la scansione.
    Se il tratto agganciato e' piu' corto di `min_valid_rows` e compare un candidato lontano,
    il tratto viene scartato e la scansione riparte dal candidato piu' centrale. Il filtro di
    larghezza ammette l'aumento graduale e rifiuta il restringimento brusco. La terza run
    (182854) conferma il fix: 487 frame, 284 trovati, 304 confermati, 6 riprese, frame 120
    FOUND. **F0-4 e' chiuso sul banco**; l'attraversamento resta F1.
29. **Controller dry-run F0-5 (2026-11-03):** `line_control.py` converte `TrackState` in PWM
    differenziali `FOLLOW`/`STOP`, senza seriale. Offset/heading positivi producono una
    correzione positiva (sinistra accelera, destra rallenta). Se `found` o `confirmed` sono
    falsi, il comando e' zero. Configurazione provvisoria: cruise 200, k_offset 0.35,
    k_heading 1.5, max correction 80. Replay sui log reali: retta 98/100 follow, curva
    872/1584, gap 270/487, ombra parziale 578/608, ombra totale 416/900; comandi entro 0..255.
    Restano PWM minimo, cm/s, taratura e integrazione motori.

## Decisioni da prendere

- [ ] regolamento ufficiale 2027;
- [ ] ruote, cinghie e rapporto di trasmissione;
- [ ] massa e centro di massa;
- [ ] modello BNO085 e calibrazione IMU;
- [ ] ruolo del servo;
- [ ] timeout watchdog (da misurare a banco);
- [ ] driver e velocita' del robot (ruote, riduzione, eventuale driver MOSFET);
- [ ] interfaccia operatore;
- [ ] procedura di raccolta vittime;
- [ ] criteri di score e reporting di gara.
