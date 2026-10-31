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
| 2026-10-31 | Arduino/L298N | tempo di arresto del watchdog | 1004.9-1008.3 ms dall'ultimo H | timestamp seriale | PWM 150/255, ruote sollevate, timeout 1000 ms | pochi ms (seriale) | verificato su piu' prove |
| 2026-10-31 | Arduino/L298N | latenza ack stop X | 3.7-3.9 ms | timestamp seriale | PWM 150/255, motori attivi | pochi ms (seriale) | verificato; status fermo a 98-99 ms |
| 2026-10-31 | Motori | PWM di banco che muove | 150: solo ronzio; 255: rotazione confermata dall'operatore | osservazione visiva + telemetria | ruote sollevate | - | 255 non e' il pwm_max definitivo |
| TBD | Ruota | diametro effettivo | TODO | calibro | ruota montata | - | per la velocita' lineare |
| TBD | Motori | RPM a PWM noto | TODO | conteggio giri in 10 s | ruote sollevate, PWM 255 | - | opzionale |

## Dimensioni gia raccolte

Le quote degli ingombri sono in `docs/hardware/Misure Robotica.pdf` e servono al CAD, non al
controller: non vanno trasferite qui.
