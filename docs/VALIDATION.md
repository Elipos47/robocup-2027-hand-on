# Validazione del progetto

**Data:** 31/10/2026

## Controllo

```sh
bash scripts/check_context.sh
bash scripts/build.sh
```

Oppure, per struttura, build e test Python disponibili:

```sh
bash scripts/test.sh
```

`check_context.sh` verifica la presenza di documenti, firmware e software; rifiuta le directory
di simulazione e gli sketch `.ino` fuori da `firmware/`; richiede che la cartella di ogni sketch
corrisponda al nome del file.

`build.sh` compila tutti gli sketch con `arduino-cli` per `arduino:avr:mega`; il FQBN si puo'
sovrascrivere con la variabile `FQBN`.

`test.sh` esegue il controllo, la build e i test Python (`unittest`) in `software/tests/`. La
suite copre protocollo, logger, safety, trasporto finto e reale bufferizzato, sessione
(handshake, heartbeat, status, stop, link), comandi motori con gate e ack, analisi sonar/IMU,
metriche camera, calibrazione checkerboard sintetica, CLI diagnostica, normalizzazione della
console, pipeline linea F0 (undistort, rilevamento, tracker, report, loop live) e stream MJPEG.

## Criterio

Il progetto e' pronto per il prossimo test di banco quando `scripts/test.sh` termina senza
errori. Questo non implica che hardware, firmware o software siano gia' verificati sul robot.
