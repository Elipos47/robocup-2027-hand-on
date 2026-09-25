# Piano di sviluppo hardware-first

## Principio

Il software viene scritto in coordinamento con i progressi hardware e con test sul campo. Un
comportamento non e' considerato pronto perche' esiste un test statico, unita' o una previsione:
servono evidenze sul robot reale, condizioni di prova e un log associato.

## Fasi

### H0a — Contratto minimo hardware

- raccogliere solo i dati necessari a scrivere il software: alimentazione, verso motori,
  limiti PWM, freno, ruota, comunicazione, camera linea e orientamento dei sensori usati;
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

### F0 — Linea

- test su linee reali, curvature, gap, disturbi e illuminazione;
- misurare deviazione e ripresa dopo perdita linea;
- non usare coordinate di percorso al posto della percezione.

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
