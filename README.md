# Robocup2027HandOn

## Scopo

Repository di sviluppo hardware-first per **RoboCupJunior Rescue Line 2027**.
L'obiettivo e' costruire e validare sul robot reale un sistema Raspberry Pi 5 + Arduino Mega
capace di seguire la linea, gestire ostacoli e terreni, riconoscere vittime e completare il
percorso con evidenze raccolte in laboratorio e sul campo.

Il progetto precedente resta intatto e non viene importato qui: niente Webots, niente controller
del progetto precedente, niente log di simulazione e niente codice funzionale gia' sviluppato.

## Stato

- Fase corrente: F0 (visione linea) dopo B1 su banco. Protocollo, logger, comandi motori e
  lettura di base di sonar/IMU sono verificati; calibrazione, misure termiche e punti aperti di
  B0 restano da completare.
- Fatto: package `software/rcj2027/` con protocollo v1.1, trasporto finto, logger e gate di
  sicurezza; test unittest verdi e demo fake disponibile. Il movimento reale resta disabilitato.
- Fatto: firmware Arduino del protocollo v1.1 in `firmware/rcj2027/`, compilato; default con
  movimento disabilitato. Valori operativi `pwm_max=255` e watchdog 1.0 s in
  `OPERATIONAL_CONFIG`; il gate predefinito resta chiuso.
- Fatto: protocollo verificato sul Mega senza movimento (test P1): handshake, status, stop e
  gate `MOTION_DISABLED`.
- Fatto: B0 parziale: stop X con ack 3,7-3,9 ms e watchdog a 1004,9-1008,3 ms; a 150 i motori
  ronzavano senza ruotare, a 255 hanno girato (conferma dell'operatore). Freno/coast ancora
  aperti.
- Fatto: B1-1, sessione reale Raspberry Pi 5 - Arduino Mega con firmware sicuro: handshake,
  heartbeat 200 ms, status a circa 100 ms, log JSONL e stop X con ack 3-5 ms, senza movimento
  (`docs/testing/B1_INTEGRATION_TEST.md`).
- Fatto: B1-2, comandi motori con gate e ack, eseguita con ruote sollevate e rotazione
  confermata dall'operatore a 255 su entrambe le ruote e sui canali separati. Un tentativo
  intermedio ha esposto un `ACK_TIMEOUT` da backlog di status, corretto; firmware sicuro
  ripristinato.
- Fatto: B1-3, HC-SR04 e BNO085 letti nello status con movimento disabilitato
  (`docs/testing/B1_SENSORS_TEST.md`): sonar ~0,9-1,2 m, BNO085 su I2C `0x4A`, bit 0+1.
  Calibrazione di assi e distanza di riferimento ancora da fare.
- Fatto: B1-4, suite software di diagnostica (`docs/testing/B1_SOFTWARE_DIAGNOSTICS.md`):
  probe camera USB e CSI via Picamera2, metriche, target checkerboard PDF, calibrazione,
  analisi sonar/IMU e test IMU in movimento. Ruoli camera: USB = stanza/vittime/palline, CSI =
  linea. USB e IMU passano; pitch/roll scambiati sul montaggio e corretti; calibrazione USB
  accettata (RMS 0,523 px); CSI nitida con autofocus, 1280x720 full-fov verificata e
  calibrazione CSI accettata (RMS 0,542 px, copertura 16,3%); il sonar a 500 mm e' accettato
  per ostacoli piu' vicini di 0,5 m con target fermo.
- Fatto: F0-1, primo pipeline visione linea (`docs/testing/F0_LINE_VISION.md`): undistort
  CSI, ROI, adaptive threshold, scanline top-down, fit robusto, confidenza e tracker. Prova
  reale su linea retta con robot fermo: 30/30 frame trovati, offset stabile -46,0 px, heading
  ~3,95 deg, confidenza ~0,95, 0 perdite. Loop `line-live` dalla CSI: 100 frame in 5,04 s,
  19,8 FPS, 100/100 trovati. Vista live con finestra locale o stream browser per telefono/PC;
  `--debug-overlay` mostra la maschera e `--duration 0` va fino a `q`/ESC. Avvio rapido da
  Thonny in `software/line_live.py`; lo stream browser ha un pulsante di stop. Curvature, gap,
  ombre e movimento restano da provare.
- Fatto: F0-2 tentativo 1 su curva reale (`docs/testing/F0_CURVE_TEST.md`): la curva e' seguita
  nei tratti in ROI con confidenza 0,86-0,965, ma la run contiene 317 frame iniziali vuoti e
  223 di riposizionamento; F0-2 resta aperto. Il primo frame live arriva in 2,1-2,2 s nelle run
  strumentate; il ritardo di 18,7 s della run curva e' anomalo.
- Contratto minimo completo: batteria 11.1 V da etichetta; A = ruota destra, B = ruota
  sinistra; polarita' invertita corretta nel software. La mappa dei pin e' in
  `docs/hardware/MINIMUM_HARDWARE_DATA.md`.
- Le quote degli ingombri gia raccolte in `docs/hardware/Misure Robotica.pdf` sono per il CAD e
  non sono trattate come parametri del controller senza conferma.
- Simulazione: non e' un gate di sviluppo per questa linea di lavoro.
- Avanzamento: una funzione software viene considerata pronta solo dopo una prova ripetibile
  sul banco o sul campo, con sicurezza e diagnostica associate.
- Regolamento: RCJ Rescue Line 2026 e' la base provvisoria; la versione 2027 deve sostituirla
  quando pubblicata.

## Mappa del progetto

| Area | Percorso |
|---|---|
| Firmware Arduino | `firmware/`, `firmware/test/`, `firmware/rcj2027/` |
| Software Raspberry Pi | `software/rcj2027/`, `software/tests/` |
| Build e test | `scripts/build.sh`, `scripts/test.sh`, `scripts/check_context.sh` |
| Obiettivi e regole | `docs/objectives/DEVELOPMENT_PLAN.md`, `docs/rules/` |
| Inventario hardware | `docs/hardware/INVENTORY.md` |
| Dati minimi per il software | `docs/hardware/MINIMUM_HARDWARE_DATA.md` |
| Questionario hardware minimo | `docs/hardware/MINIMUM_HARDWARE_QUESTIONS.md` |
| Misure e TODO | `docs/MEASUREMENT_LOG.md` |
| Riferimento CAD | `docs/hardware/CAD_REFERENCE.md` |
| Bring-up e calibrazione | `docs/hardware/BRINGUP_CHECKLIST.md`, `docs/hardware/CALIBRATION.md` |
| Architettura | `docs/architecture/SYSTEM_ARCHITECTURE.md` |
| Protocollo seriale v1.1 | `docs/architecture/SERIAL_PROTOCOL.md` |
| Test di banco | `docs/testing/PROTOCOL_BENCH_TEST.md`, `docs/testing/B0_BENCH_TEST.md`, `docs/testing/B1_INTEGRATION_TEST.md`, `docs/testing/B1_SENSORS_TEST.md`, `docs/testing/B1_SOFTWARE_DIAGNOSTICS.md`, `docs/testing/F0_LINE_VISION.md`, `docs/testing/F0_CURVE_TEST.md` |
| Test sul campo | `docs/testing/FIELD_TEST_PLAN.md` |
| Decisioni aperte | `docs/DECISIONS.md` |
| Provenienza e scelte di importazione | `docs/SOURCE_MAP.md` |

## Hardware di riferimento

- Raspberry Pi 5 4GB: visione, logica di alto livello e interfaccia operatore.
- Arduino Mega 2560: motori, PWM, sensori rapidi, servo e watchdog.
- Due telecamere: camera linea e camera stanza/vittime.
- HC-SR04, BNO085, L298N, UPS, schermo, batterie e servo sono presenti sull'hardware ma
  alcuni dettagli restano da verificare a banco.

L'inventario, il contratto minimo e le limitazioni sono in
`docs/hardware/INVENTORY.md` e `docs/hardware/MINIMUM_HARDWARE_DATA.md`.

## Regole d'uso

1. Non cambiare hardware o cablaggi senza approvazione.
2. Non dichiarare una misura affidabile se non ha data, strumento e condizione di prova.
3. Non usare un test statico o una simulazione al posto di una prova reale.
4. Ogni modifica deve avere una prova, un test, un log e una spiegazione per l'operatore.
5. I segreti e le credenziali non vanno nel repository.

## Prossimo lavoro

1. Ripetere F0-2 con la curva sempre dentro la ROI e il raggio misurato; poi ombre, gap e
   movimento a bassa velocita'. La linea retta e' gia' stata rilevata 30/30 e in live a 19,8 FPS.
2. Completare la convenzione dei segni IMU.
3. Chiudere B0: freno/coast, ripetizione e verifica termica di PWM 255/watchdog.
4. Ripetere il test della linea con illuminazione e superfici diverse, poi collegare il
   controller ai motori solo dopo il gate di sicurezza.

La validazione e la build si eseguono con:

```sh
bash scripts/test.sh
```
