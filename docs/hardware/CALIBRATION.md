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
python3 -m rcj2027.diagnostics checkerboard \
  --pattern 9x6 --square-mm 25 --output checkerboard.pdf
```

- `camera` misura luminosita', contrasto, nitidezza e, se richiesto, rileva il checkerboard;
  USB usa OpenCV, CSI usa Picamera2 con autofocus e warm-up;
- `sonar` confronta la media con una distanza misurata e controlla i salti;
- `imu` verifica rumore a riposo o movimento sull'asse atteso;
- `camera-calibrate` calcola matrice intrinseca e distorsione da almeno 3 immagini valide;
- `checkerboard` genera un PDF A4 con quadrati a dimensione fisica reale e barra da 100 mm.

I test software non sostituiscono la misura fisica: il lato del checkerboard, la distanza di
riferimento e l'orientamento degli assi vanno dichiarati dall'operatore.

## Calibrazione camera con checkerboard

1. Genera il target con `checkerboard` (default 9x6 corner interni, quadrati 25 mm).
2. Stampa al 100% e verifica con un righello che la barra in basso sia lunga 100 mm.
3. Fissa il target su una superficie piana e opaca; cattura 12-20 immagini con la camera
  definitiva, a distanze e angolazioni diverse, con il pattern che occupa circa il 50-80% del
   frame. Evita riflessi, ombre e mosso.
4. Salva le immagini in una cartella, ad esempio `calib/`.
5. Esegui `camera-calibrate` con lo stesso pattern e lato usati per la stampa.
6. Conserva il JSON prodotto e verifica l'RMS: sotto 1 px e' accettabile, sotto 0,5 px e' buono.

La calibrazione reale usa la lente e il montaggio veri; le viste sintetiche verificano solo il
codice. Una camera sfocata o un target storto producono un RMS alto e non vanno usati.

## Assi IMU

Il BNO085 riporta tre rotazioni rispetto ai propri assi:

- **yaw**: rotazione attorno all'asse verticale, cioe' il cambio di direzione;
- **pitch**: rotazione attorno all'asse trasversale, cioe' muso su/giu';
- **roll**: rotazione attorno all'asse longitudinale, cioe' inclinazione destro/sinistro.

Per verificare l'allineamento al telaio, esegui un test per asse:

```sh
python3 -m rcj2027.diagnostics imu --port /dev/ttyACM0 --duration 10 \
  --imu-mode motion --expected-axis yaw --countdown 5
python3 -m rcj2027.diagnostics imu --port /dev/ttyACM0 --duration 10 \
  --imu-mode motion --expected-axis pitch --countdown 5
python3 -m rcj2027.diagnostics imu --port /dev/ttyACM0 --duration 10 \
  --imu-mode motion --expected-axis roll --countdown 5
```

Ruota il robot attorno all'asse indicato, senza spostarlo. Il report mostra l'asse dominante,
l'escursione e la deriva. Se l'asse dominante non coincide con quello atteso, il montaggio o la
convenzione degli assi vanno corretti nel software.

## Distanza del sonar

Per il test di riferimento usa un bersaglio piano e rigido, perpendicolare al sensore:

- **500 mm** come primo punto, con un bersaglio di almeno 20x20 cm;
- **1000 mm** come secondo punto, con un bersaglio di almeno 30x30 cm.

Misura la distanza dalla faccia del sensore alla faccia del bersaglio con un metro. Lascia almeno
1,5 m liberi dietro il bersaglio e togli oggetti laterali che possano riflettere. La tolleranza
iniziale e' ±50 mm. Se il test mostra salti verso distanze molto diverse, il problema e' il
bersaglio o l'ambiente, non la formula del firmware.

```sh
python3 -m rcj2027.diagnostics sonar --port /dev/ttyACM0 --duration 10 \
  --reference-mm 500 --reference-tolerance 50
```

Ripeti a 1000 mm e registra media, deviazione standard e salto massimo.

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

## Regole

- salvare data, condizione, valori e modifiche hardware;
- non dichiarare una calibrazione valida se i test sul campo peggiorano;
- non inserire immagini o dati sensibili non necessari nel repository.
