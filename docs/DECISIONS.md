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
    matrice intrinseca, `diagnostics.py` espone i comandi con exit code 0/1/2. Camera 0 e IMU
    stazionario/yaw passano; il sonar e' valido ma il salto di ~695 mm fa fallire il test di
    stabilita'. La soglia non viene abbassata senza una prova con bersaglio stabile.

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
