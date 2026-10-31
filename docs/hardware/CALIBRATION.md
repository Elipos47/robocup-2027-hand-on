# Calibrazione manuale

Non esiste auto-calibrazione in runtime. Ogni camera e ogni sensore viene calibrato con una
procedura manuale, una condizione di luce registrata e un log salvato.

La calibrazione completa viene dopo il contratto minimo del software. Per iniziare servono solo
i parametri indicati in `docs/hardware/MINIMUM_HARDWARE_DATA.md`; le tarature dettagliate restano
differite.

## Strumenti software

La CLI `python3 -m rcj2027.diagnostics` (dalla cartella `software/`) supporta:

```sh
python3 -m rcj2027.diagnostics camera --list
python3 -m rcj2027.diagnostics camera --device 0 --save /tmp/camera0.jpg
python3 -m rcj2027.diagnostics camera --csi --camera-num 0 --warmup 2 \
  --save /tmp/csi0.jpg
python3 -m rcj2027.diagnostics camera --device 0 --checkerboard 9x6
python3 -m rcj2027.diagnostics camera --csi --camera-num 0 --checkerboard 9x6
python3 -m rcj2027.diagnostics sonar --port /dev/ttyACM0 --duration 10 \
  --reference-mm 500 --reference-tolerance 50
python3 -m rcj2027.diagnostics imu --port /dev/ttyACM0 --duration 10 \
  --imu-mode motion --expected-axis yaw --countdown 5
python3 -m rcj2027.diagnostics camera-calibrate \
  --images "calib/*.jpg" --pattern 9x6 --square-mm 25 --output calib.json
```

- `camera` misura luminosita', contrasto, nitidezza e, se richiesto, rileva il checkerboard;
  USB usa OpenCV, CSI usa Picamera2 con autofocus e warm-up;
- `sonar` confronta la media con una distanza misurata e controlla i salti;
- `imu` verifica rumore a riposo o movimento sull'asse atteso;
- `camera-calibrate` calcola matrice intrinseca e distorsione da almeno 3 immagini valide.

I test software non sostituiscono la misura fisica: il lato del checkerboard, la distanza di
riferimento e l'orientamento degli assi vanno dichiarati dall'operatore.

## Camera linea

1. Fissare la camera nella posizione definitiva.
2. Registrare altezza, inclinazione, focale e distanza dal suolo.
3. Catturare una superficie bianca e una linea nera con luce nota.
4. Salvare i range HSV/ROI e la procedura usata.
5. Ripetere con luce debole, luce forte e ombre.

## Camera vittime

- fotografare la posizione della camera;
- misurare distanza e angolo di visione della stanza;
- definire una procedura di calibrazione solo dopo aver verificato il montaggio;
- non usare un modello o una soglia importati senza dati reali.

## IMU e sonar

- annotare orientamento del modulo e assi;
- misurare rumore a robot fermo;
- verificare la scala e l'orientamento degli assi;
- ripetere la misura dopo il montaggio definitivo.

## Regole

- salvare data, condizione, valori e modifiche hardware;
- non dichiarare una calibrazione valida se i test sul campo peggiorano;
- non inserire immagini o dati sensibili non necessari nel repository.
