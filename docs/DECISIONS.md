# Decisioni aperte e scelte

## Scelte prese per la baseline

1. **Hardware-first:** il software viene coordinato con misure e prove sul campo.
2. **Nessun simulatore come gate:** il progetto non dipende da Webots o da altri ambienti
   simulati; nessun codice del progetto precedente viene importato.
3. **Regolamento 2026 provvisorio:** i PDF 2026 sono la base fino alla pubblicazione 2027.
4. **STEP esterno:** il file CAD resta fuori dal repository e viene solo referenziato.
5. **TODO espliciti:** dati hardware mancanti non vengono inventati o dedotti dal solo CAD.
6. **Prove ripetibili:** ogni funzione richiede una prova, un test, un log e una spiegazione
   per l'operatore.
7. **Sicurezza prima della missione:** stop e watchdog hanno precedenza sul percorso.

## Decisioni da prendere

- [ ] regolamento ufficiale 2027;
- [ ] ruote, cinghie e rapporto di trasmissione;
- [ ] batterie e distribuzione di alimentazione;
- [ ] massa e centro di massa;
- [ ] modello BNO085 e calibrazione IMU;
- [ ] ruolo del servo;
- [ ] contratto seriale e timeout watchdog;
- [ ] interfaccia operatore;
- [ ] procedura di raccolta vittime;
- [ ] criteri di score e reporting di gara.
