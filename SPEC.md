# SPEC — Robocup2027HandOn

**Versione:** 0.1
**Data:** 24/09/2026
**Stato:** baseline documentale hardware-first

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
| Batterie | alimentazione | tipo, tensione e capacita' da verificare |
| UPS | continuità alimentazione Raspberry | presente |
| Servo | meccanismo ausiliario | modello e funzione da verificare |
| Ruote/cinghie | locomozione | modello e dimensioni mancanti |
| Schermo | diagnostica operatore | presente, interfaccia da definire |

## 3. Architettura

- Il Raspberry gestisce percezione, decisione di alto livello, logging e interfaccia.
- Arduino gestisce attuatori e sensori a bassa latenza, con heartbeat e stop sicuro.
- La comunicazione seriale e' versionata, leggibile e protetta da una scadenza di sicurezza.
- Il controller non usa coordinate di percorso al posto di sensori e IMU.
- La telemetria deve distinguere stato, sensori, attuatori, errori e prove.

## 4. Regole di sviluppo

1. Nessuna modifica hardware senza approvazione esplicita.
2. Ogni misura ha provenienza, data, strumento e incertezza.
3. Ogni funzione software ha un test ripetibile e un log.
4. I test statici non sostituiscono una prova sul campo.
5. I fallimenti di sicurezza hanno precedenza sulla missione.
6. Il regolamento Rescue Line 2026 e' provvisorio; le differenze 2027 devono essere registrate
   prima di modificarne l'implementazione.
7. Il progetto non contiene codice o log importati dal precedente repository.

## 5. Gate di avanzamento

### Gate H0 — hardware inventory

Inventario completo, batterie/motori/ruote/masse/cablaggi misurati, TODO separati dai fatti.

### Gate B0 — bench safety

Freni, verso motori, stop di emergenza, watchdog e perdita seriale verificati a robot sollevato.

### Gate B1 — primitive

Comunicazione, heartbeat, logger, motori e sensori ripetibili su banco.

### Gate F0 — line

Tracking della linea con prove su tratti reali, gap e disturbi; nessuna claim basata solo su
unità o test sintetici.

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

Questa baseline non contiene:

- simulatori o mondi di simulazione;
- controller, firmware o librerie funzionali;
- log di prove simulate;
- copia del codice sviluppato nel progetto precedente;
- parametri inventati per colmare dati hardware mancanti.

## 8. Riferimenti

- `docs/hardware/INVENTORY.md`
- `docs/hardware/CAD_REFERENCE.md`
- `docs/rules/`
- `docs/architecture/SYSTEM_ARCHITECTURE.md`
- `docs/testing/FIELD_TEST_PLAN.md`
- `docs/MEASUREMENT_LOG.md`
