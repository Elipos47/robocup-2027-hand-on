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
