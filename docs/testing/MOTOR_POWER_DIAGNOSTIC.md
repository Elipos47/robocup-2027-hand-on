# Diagnosi alimentazione motori

**ID:** F0-5 / PWM-DIAG-1
**Data:** 2026-11-04
**Contesto:** due run del test a coppia 255
(`software/logs/pwm-pair-repeat-001.jsonl`, `software/logs/pwm-pair-repeat-002.jsonl`).
**Stato:** seconda run eseguita con multimetro; alimentazione stabile, misura A da solo 3 V e
A+B 0-1 V. In corso l'isolamento tra L298N, motore destro e connettori.
**Obiettivo:** isolare la causa del guasto sotto carico prima di riprendere le misure di PWM
minimo e cm/s.

## Sintomo osservato

- prima fase avanti (255 su entrambe le ruote): entrambe le ruote girano;
- prima fase indietro (-255): la ruota destra non gira;
- fasi successive: entrambe le ruote fanno uno scatto iniziale e poi si fermano.

Il software ha accettato tutti i 6 comandi (`ack` 6-7 ms), lo status riporta `motors_active`
per tutta la durata e gli stop hanno ricevuto ack. Il firmware non ha segnalato errori o
watchdog. Il guasto e' quindi a valle dei pin del Mega: alimentazione, L298N, connettori o
motori.

## Risultati delle due run

| Run | Condizione | Esito fisico | Tensione +12/GND L298N |
|---|---|---|---|
| `pwm-pair-repeat-001` | robot appoggiato al tavolo, sotto carico | prima avanti ok, poi ruota destra ferma e scatti | non misurata |
| `pwm-pair-repeat-002` | ruote sollevate, multimetro DC | stesso guasto | stabile 10-12 V per tutta la prova |

La tensione stabile esclude batteria, BMS e caduta sul collegamento di alimentazione come causa
primaria. Restano il L298N (canale A o protezione termica), il motore destro e i connettori.
La prossima prova utile e' il test dei canali separati con misura di `OUT1`/`OUT2` e
`OUT3`/`OUT4` durante A avanti, A indietro, B avanti e B indietro, piu' la temperatura del
L298N.

## Misura con `pwm_staggered_test` (2026-11-04)

- A da solo a 255: **3 V** ai capi di `OUT1`/`OUT2`, motore A gira lentamente;
- A+B insieme: **0-1 V** ai capi di `OUT1`/`OUT2`, motore A fermo o solo scatto;
- multimetro in DC, puntali su `OUT1`/`OUT2`, ruote sollevate.

3 V sono troppo pochi: con alimentazione 10-12 V e la caduta tipica dell'L298N il motore
dovrebbe vedere circa 7-9 V. Il calo a 0-1 V quando si aggiunge B indica un limite condiviso:
alimentazione, massa o protezione termica. Poiche' `+12`/`GND` era stabile, i candidati
principali sono il **canale A del L298N** (caduta interna o protezione) e il **motore A**
(assorbimento anomalo per attrito o corto).

Misure successive, in ordine:

1. `5V` dell'Arduino rispetto a `GND`, a riposo e durante A da solo: atteso ~5 V;
2. `ENA` rispetto a `GND` durante A da solo: atteso ~5 V a 255;
3. temperatura del L298N dopo A da solo: se molto caldo, e' protezione termica;
4. scambio dei due connettori motore su `OUT1`/`OUT2` e `OUT3`/`OUT4`, a motori spenti e con
   approvazione: se il guasto segue il motore A e' il motore, se resta sul canale A e' l'L298N.

## Ipotesi

| # | Ipotesi | Come discriminare |
|---:|---|---|
| 1 | batteria scarica o BMS che limita la corrente | tensione ai morsetti a riposo e durante il comando; se crolla o il BMS stacca, e' l'alimentazione |
| 2 | L298N in protezione termica o sovracorrente | temperatura del modulo e durata prima dell'arresto; se riparte dopo raffreddamento, e' il ponte |
| 3 | connettore o GND intermittente | prova a ruote sollevate muovendo delicatamente i connettori; cercare cavi caldi o contatti allentati |
| 4 | semiconduttore del canale A (ruota destra) danneggiato | A avanti/indietro da solo; misurare OUT1/OUT2 e scambiare i motori solo con approvazione |
| 5 | motore o riduttore destro bloccato | ruota girata a mano con alimentazione staccata; corrente a vuoto del solo motore |

## Procedura

**Sicurezza:** ruote sollevate e robot fissato per tutte le prove elettriche. Nessun test a
terra finche' la causa non e' isolata. Non cambiare cablaggi senza approvazione.

1. **Ispezione a motori spenti**
   - ruote girate a mano: devono girare libere;
   - connettori ENA/ENB, IN1..IN4, OUT1..OUT4 e GND ben inseriti;
   - nessun cavo caldo, spellato o connettore sciolto.

2. **Misure a riposo e sotto carico**
   - tensione batteria ai morsetti;
   - tensione +12 V e +5 V sul L298N;
   - tensione durante un comando a 255 (ruote sollevate);
   - temperatura del L298N prima e dopo 3 s a 255.
   Registrare i valori in `docs/MEASUREMENT_LOG.md`.

3. **Canali separati a ruote sollevate**
   - caricare `firmware/test/pwm_channel_test/`;
   - osservare A avanti, B avanti, A indietro, B indietro a 255;
   - se un solo verso del canale A fallisce, il sospetto e' il semiconduttore del ponte;
   - se tutti i canali funzionano da soli ma falliscono insieme, il sospetto e' la batteria o
     la corrente disponibile.

4. **Ripetizione a coppia con monitoraggio**
   - solo dopo i passi precedenti, ripetere 2-3 cicli a 255 con ruote sollevate;
   - misurare tensione e temperatura durante ogni ciclo;
   - se il guasto compare solo sotto carico, ripetere con la batteria carica e annotare la
     tensione.

5. **Scambio uscite motore (solo con approvazione)**
   - invertire i due connettori motore su OUT1/OUT2 e OUT3/OUT4;
   - se il guasto segue il motore, il problema e' nel motore o nei suoi fili;
   - se resta sul canale, il problema e' nel L298N.

## Criteri

- **PASS alimentazione:** tensione stabile sotto comando, senza stacco del BMS.
- **PASS ponte:** nessun spegnimento termico e tutti i canali ripetibili a 255.
- **PASS meccanica:** ruote libere e stesso comportamento avanti/indietro.
- Il test a coppia si considera chiuso solo con 3 ripetizioni consecutive a ruote sollevate,
  senza perdita di un canale.

## Dati da riportare

| Prova | Strumento | Valore | Condizione | Esito |
|---|---|---|---|---|
| Batteria a riposo |  |  |  |  |
| Batteria sotto comando 255 |  |  |  |  |
| L298N +12 V sotto comando |  |  |  |  |
| L298N +5 V |  |  |  |  |
| Temperatura L298N |  |  |  |  |
| A avanti/indietro |  |  | ruote sollevate |  |
| B avanti/indietro |  |  | ruote sollevate |  |
| Coppia 255, 3 cicli |  |  | ruote sollevate |  |
