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

## Dimensioni gia raccolte

Le quote degli ingombri sono in `docs/hardware/Misure Robotica.pdf` e servono al CAD, non al
controller: non vanno trasferite qui.
