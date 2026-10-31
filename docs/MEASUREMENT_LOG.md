# Registro misure hardware

**Regola:** compilare solo misure realmente eseguite. Un valore non misurato resta `TODO`.

## Contratto minimo

| Data | Componente | Misura | Valore | Strumento | Condizione | Incertezza | Esito |
|---|---|---|---|---|---|---|---|
| 2026-10-22 | Batterie | tensione nominale | 11.1 V | etichetta del pacco (dato del produttore) | 2 pacchi Li-Ion 3S in parallelo | dichiarato, non misurato | confermato; misura a vuoto solo per controllo |
| 2026-10-31 | Motori | asse sinistro/destro | A = destra, B = sinistra | occhio, ruote sollevate | canali separati | - | confermato |
| 2026-10-31 | Motori | verso avanti/indietro | entrambi invertiti (A e B) | occhio, ruote sollevate | PWM 255, canali separati | - | corretto nel software e riverificato: 1/3 avanti |

## Altre misure

Si aggiungono solo quando servono a una prova: autonomia, RPM, corrente sotto carico, geometria
della camera, IMU, sonar. Il registro non e' un inventario da completare.

| Data | Componente | Misura | Valore | Strumento | Condizione | Incertezza | Esito |
|---|---|---|---|---|---|---|---|
| 2026-10-31 | Arduino/L298N | tempo di arresto del watchdog | 1007-1008 ms dall'ultimo H | timestamp seriale | PWM 150, ruote sollevate, timeout 1000 ms | pochi ms (seriale) | verificato su 2 prove |
| 2026-10-31 | Arduino/L298N | latenza ack stop X | 3.9 ms | timestamp seriale | PWM 150, motori attivi | pochi ms (seriale) | verificato; status fermo a 98 ms |
| TBD | Ruota | diametro effettivo | TODO | calibro | ruota montata | - | per la velocita' lineare |
| TBD | Motori | RPM a PWM noto | TODO | conteggio giri in 10 s | ruote sollevate, PWM 255 | - | opzionale |

## Dimensioni gia raccolte

Le quote degli ingombri sono in `docs/hardware/Misure Robotica.pdf` e servono al CAD, non al
controller: non vanno trasferite qui.
