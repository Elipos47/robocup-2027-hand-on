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
| 2026-10-31 | Link seriale Raspberry-Mega | latenza handshake `V` -> risposta | 3.7-6.9 ms | timestamp JSONL | USB 115200, firmware sicuro, 3 run da 5 s | pochi ms (seriale) | B1-1 verificato |
| 2026-10-31 | Link seriale Raspberry-Mega | periodo status `A` | 100.1-100.2 ms medio, 98-103 ms min-max | timestamp JSONL | 51 frame per run, 3 run da 5 s | pochi ms (seriale) | B1-1 verificato |
| 2026-10-31 | Link seriale Raspberry-Mega | latenza ack stop `X` | 3-5 ms | timestamp JSONL | chiusura sessione, firmware sicuro, 3 run | pochi ms (seriale) | B1-1 verificato |
| 2026-10-31 | Link seriale Raspberry-Mega | latenza ack comando `D` | 5-7 ms | timestamp JSONL | firmware di banco, PWM 255, 3 comandi | pochi ms (seriale) | B1-2 verificato |
| 2026-10-31 | Link seriale Raspberry-Mega | latenza ack stop `X` con motori attivi | 2-6 ms | timestamp JSONL | firmware di banco, PWM 255, 3 stop | pochi ms (seriale) | B1-2 verificato |
| 2026-10-31 | Motori/L298N | rotazione a PWM 255 con gate software | entrambe le ruote e canali separati ruotano | osservazione visiva + log | ruote sollevate, alimentazione inserita, firmware di banco | - | B1-2 verificato; 255 non e' il pwm_max definitivo |
| 2026-10-31 | HC-SR04 | distanza letta | 900-1206 mm | telemetria seriale JSONL | robot fermo, due run da 5 s | non calibrata con metro campione | B1-3: bit 0 valido 50/51 status |
| 2026-10-31 | BNO085 | presenza I2C e angoli | 0x4A; yaw -183..8 mdeg, pitch 4685..8155 mdeg, roll -2248..21 mdeg | scanner I2C + telemetria JSONL | robot fermo, due run da 5 s | assi/montaggio non calibrati | B1-3: bit 1 valido 49/51 status |
| 2026-10-31 | Camera USB 5MP | frame e qualita' | 640x480 @30; luminosita' 70.9-80.9, contrasto 52.2-54.3, nitidezza 67.5-73.1 | OpenCV 4.11 | USB, camera stanza | soglie software | B1-4: camera stanza PASS |
| 2026-10-31 | Camera USB 5MP | calibrazione checkerboard | 15 viste, RMS 0.896 px, copertura media 7.2% (3.6-9.6%) | OpenCV 4.11 | A4 stampato al 95%, lato reale 23.75 mm | RMS nominale, copertura insufficiente | RIFIUTATA: target troppo piccolo, rifare a 50-80% del frame |
| 2026-10-31 | Camera USB 5MP | calibrazione checkerboard, secondo set | 8/15 rilevati; copertura 3.8-28.8%, media 11.0%; solo 3 viste >=20% | OpenCV 4.11 | A4 stampato al 95%, lato reale 23.75 mm | distanza incoerente tra i frame | RIFIUTATA: servono almeno 8-10 viste con copertura >=20% |
| 2026-11-01 | Camera USB 5MP | calibrazione checkerboard | 15/15; RMS 0.523 px; copertura media 22.7% (20.0-31.3%); fx/fy 248.1/246.6; cx/cy 298.4/239.9 | OpenCV 4.11 | A4 stampato al 95%, lato reale 23.75 mm, camera stanza | RMS <1 px | ACCETTATA come prima calibrazione della stanza; migliorabile con piu' copertura |
| 2026-11-01 | Camera CSI IMX708 | frame e qualita' | 640x480-2304x1296; nitidezza normalizzata 103-214; 1280x720: 149.3, luminosita' 140.9, contrasto 64.8 | Picamera2/libcamera | CSI camera 0, AF, checkerboard | soglie software | PASS a tutte le risoluzioni; 1280x720 candidata per la linea |
| 2026-11-01 | Camera CSI IMX708 | probe 1280x720 full-fov | 54 corner, qualita' e pass true, nitidezza 552 | Picamera2/libcamera | sensore intero 2304x1296, checkerboard completo | soglie software | PASS: campo visivo corrispondente alla preview |
| 2026-11-01 | Camera CSI IMX708 | calibrazione checkerboard | 15 frame, copertura 14.0%, dispersione centri 0.6 px, rapporto dimensioni 1.00 | OpenCV 4.11 | 1280x720 full-fov, board fermo | pose identiche | RIFIUTATA: viste troppo simili; servono 8-10 pose diverse |
| 2026-11-01 | Camera CSI IMX708 | calibrazione checkerboard | 14/15 viste, copertura 16.3% (12.6-24.4%), RMS 0.542 px, pose spread 423.6 px, size ratio 1.93 | OpenCV 4.11 | 1280x720 full-fov, pose varie | RMS <1 px | ACCETTATA come prima calibrazione della linea; verificare undistort in F0 |
| 2026-10-31 | HC-SR04 | stabilita' su 10 s | 99/100 e 101/101 validi; salto max 695-697 mm | telemetria + analisi software | robot fermo, ambiente con riflessi | non calibrata | B1-4: FAIL stabilita', da ripetere con bersaglio stabile |
| 2026-10-31 | HC-SR04 | riferimento 500 mm, criterio robusto | 005/006: mediane 522/507.5 mm, outlier 3.0%/1.0%, riferimento PASS; 007: mediana 597 mm, outlier 9.2%, riferimento FAIL | telemetria + analisi software | target spostato tra le run | pochi mm (seriale) | target fermo: PASS; target mosso: FAIL |
| 2026-10-31 | BNO085 | rumore a riposo | 98/100 validi; yaw std 3.2 mdeg, pitch 59.8 mdeg, roll 28.2 mdeg | telemetria + analisi software | robot fermo, 10 s | pochi mdeg | B1-4: PASS |
| 2026-10-31 | BNO085 | rotazione yaw manuale | 178/180 validi; yaw -6.7..62.0 deg; asse dominante yaw | telemetria + analisi software | rotazione a mano ~90 deg | movimento manuale | B1-4: PASS |
| 2026-10-31 | BNO085 | stazionario dopo correzione assi | 100/100 validi; pitch std 4.2 mdeg, roll 10.7 mdeg, yaw 7.1 mdeg | telemetria + analisi software | robot fermo, 10 s | pochi mdeg | pitch/roll scambiati corretti; PASS |
| 2026-10-31 | BNO085 | rotazione pitch manuale | 149/151 validi; pitch -21.2..8.0 deg; asse dominante pitch | telemetria + analisi software | muso su/giu' a mano | movimento manuale | B1-4: PASS dopo swap |
| 2026-10-31 | BNO085 | rotazione roll manuale | 150/150 validi; roll -19.8..25.6 deg; asse dominante roll | telemetria + analisi software | inclinazione destra/sinistra a mano | movimento manuale | B1-4: PASS dopo swap |
| 2026-11-01 | Camera CSI IMX708 | verifica undistort su checkerboard | errore omografia 0.4392 -> 0.4287 px; spostamento corner 0.717 px medio, 3.622 px max | OpenCV 4.11 + `csi_1280x720.json` | 14/15 immagini di calibrazione, 1280x720 full-fov | RMS nominale | PASS tecnico; non sostituisce la prova su linea reale |
| 2026-11-01 | Software linea F0 | tempo di elaborazione frame 1280x720 | 38.4 ms mediana (34.0-45.0) su 30 frame reali; primo frame fino a 73.2; senza undistort 27.9 ms | Python + OpenCV 4.11 su Raspberry Pi 5 | sequenza linea F0-1, mappe gia' calcolate | pochi ms | sufficiente per F0 a bassa velocita'; non include l'acquisizione |
| 2026-11-01 | Camera CSI IMX708 / linea F0 | rilevamento linea reale, 30 frame | 30/30 trovati; offset -46.04..-45.87 px; heading 3.88..4.01 deg; confidenza 0.946-0.954; residuo 0.30-0.37 px; 37/60 righe valide | `line` con calibrazione `csi_1280x720.json` | linea nera su piano bianco, bordo tavolo visibile, robot fermo, 1280x720 full-fov | soglie software | PASS F0-1 linea retta; curvature, gap e movimento ancora da provare |
| 2026-11-01 | Camera CSI IMX708 / linea F0 | loop live `line-live` | 100 frame in 5.04 s (19.8 FPS); 100/100 trovati; offset mediano -46.52 px; heading 4.14 deg; confidenza 0.955; elaborazione 39.9 ms mediana | Picamera2 video 1280x720 full-fov + `line_vision` | linea retta, robot fermo, nessun comando motore | soglie software | PASS live; il controller non e' collegato |
| 2026-11-01 | Software F0 | vista live `--preview` e `--http-port` | preview 18 frame in 1 s; stream MJPEG con indice HTML e JPEG valido, 85 frame in 5 s; con `--debug-overlay` 26 frame in 2 s; stop browser 7 frame in 2 s | OpenCV 4.11 + `live_view.py` | rete locale, display :0 | soglie software | PASS; stream senza autenticazione, solo rete locale |
| 2026-11-03 | Camera CSI IMX708 / linea F0 | curva reale, tentativo 1 | 1584 frame in 89.29 s; 899/1584 trovati (56.8%) ma 317 frame iniziali vuoti e 223 di riposizionamento; tratti in ROI 100% trovati con confidenza 0.86-0.965 e 6 riprese | `line-live` + `csi_1280x720.json` | curva nera su piano bianco, nastro proxy piu' largo di 1-2 cm, robot spostato a mano | soglie software | PASS banco: la curva puo' uscire dalla ROI, raggio non richiesto; resta compatibilita' con linea 1-2 cm |
| 2026-11-03 | Camera CSI IMX708 / linea F0 | ombra parziale, tentativo 1 | 608 frame in 35.29 s; 608/608 trovati, 606 confermati, 0 perdite; offset -114.7..186.0 px; heading -3.3..6.8 deg; confidenza 0.663-0.978 (mediana 0.974); startup 5.6 s | `line-live` + `csi_1280x720.json` | linea nera, ombra parziale, probabilmente leggera | soglie software | PASS tecnico; ripetere con ombra netta su 1/3 e 2/3 della linea |
| 2026-11-03 | Camera CSI IMX708 / linea F0 | ombra totale/bassa luce, tentativo 1 | 900 frame in 54.92 s; 765/900 trovati (85%) ma falso bordo sottile (larghezza 10-31 px contro 188-190) con offset +48 px; 5 riprese | `line-live` + `csi_1280x720.json` | luce spenta, linea ancora visibile a tratti | soglie software | NON chiuso: il falso bordo non e' una linea valida; serve run live con il nuovo guard |
| 2026-11-03 | Software F0 | replay tracker con continuita' di larghezza | 765 trovati -> 433 accettati, 332 rifiutati per larghezza, 426 confermati; `control_passed=false` | `LineTracker` aggiornato | stessi frame della run ombra totale | soglie software | guard valido sui dati registrati; da confermare live |
| 2026-11-03 | Camera CSI IMX708 / linea F0 | gap reale da 7 cm, tentativo 1 | 513 frame in 28.47 s; 251/513 trovati (48.9%), 266 confermati, 6 riprese, 0 falsi evidenti; offset -176.6..71.4 px | `line-live` + `csi_1280x720.json` | gap 7 cm, linea nera su piano bianco, linea spostata a mano | soglie software | QUALITATIVO PASS: FOUND sui segmenti, LOST nel vuoto, ripresa; frame 150 perso per seme/width poi corretto |
| 2026-11-03 | Software F0 | fix aggancio dopo gap | stop sul gap solo dopo `min_valid_rows`; larghezza in aumento ammessa; test `speck_then_line` | `line_vision.py` | sintetico + frame annotato 150 | soglie software | da validare con nuova run live sul gap |
| 2026-11-03 | Camera CSI IMX708 / linea F0 | gap reale da 7 cm, tentativo 2 | 479 frame in 27.82 s; 288/479 trovati (60.1%), 320 confermati, 6 riprese, 0 width-rejected; frame 120 perso per seme lontano | `line-live` + `csi_1280x720.json` | gap 7 cm, linea spostata a mano | soglie software | comportamento gap corretto; seme lontano corretto con reset del tratto corto, da rivalidare live |
| 2026-11-03 | Camera CSI IMX708 / linea F0 | gap reale da 7 cm, tentativo 3 | 487 frame in 27.86 s; 284/487 trovati (58.3%), 304 confermati, 6 riprese, 0 width-rejected; frame 120 FOUND | `line-live` + `csi_1280x720.json` | gap 7 cm, linea spostata a mano, codice con reset del seme | soglie software | PASS banco F0-4; attraversamento gap resta F1 |
| 2026-11-03 | Software F0 | controller dry-run F0-5 | retta 98/100 FOLLOW, curva 872/1584, gap 270/487, ombra parziale 578/608, ombra totale 416/900; comandi entro 0..255 | `line-control` + `line_control.py` | replay dei log reali, nessun comando motore | soglie software | PASS dry-run; `motor_output=false`; guadagni e cruise provvisori |
| 2026-11-03 | Motori/L298N | sweep PWM a ruote sollevate | 150, 175, 200, 225, 255 per 4 s ciascuno: nessuna rotazione; `motors_active=true`, 0 errori, stop ack | `pwm_sweep.py` + firmware di banco | ruote sollevate, robot fissato, pausa 2 s | - | software comanda; causa da isolare su alimentazione/enable/L298N; firmware sicuro ripristinato |
| 2026-11-03 | Motori/L298N | entrambi i canali a 255 | ruota sinistra gira, ruota destra ferma; velocita' lenta | sketch `pwm_both_test` | ruote sollevate, 2 cicli avanti/indietro | - | canale A/motore destro sotto diagnosi; velocita' massima non misurabile con un solo motore |
| 2026-11-03 | Motori/L298N | canali separati a 255 | A e B funzionano separatamente, avanti e indietro | sketch `pwm_channel_test` | ruote sollevate | - | motori e canali singolarmente ok; il problema compare con entrambi attivi |
| 2026-11-03 | Motori/L298N | avvio scaglionato | sketch pronto, non caricato; A poi B e B poi A | `pwm_staggered_test` | ruote sollevate | - | prossimo test per alimentazione/corrente vs canale |
| 2026-11-03 | Motori/L298N | verifica finale singoli e coppia | entrambi i motori funzionano singolarmente e insieme a 255; guasto precedente non riprodotto | sketch di banco | ruote sollevate, dopo controllo collegamenti | - | causa non identificata, sospetto connettore; rischio affidabilita', ripetere e controllare i serraggi |
| 2026-11-03 | Camera CSI IMX708 / linea F0 | avvio live dopo strumentazione | camera start 0.06-0.17 s; warmup 2.06-2.19 s; primo frame 2.08-2.19 s | Picamera2 + `line-live` | due run di prova, 1280x720 full-fov | pochi ms | il ritardo di 18.7 s della run curva e' anomalo, non il comportamento atteso |
| 2026-10-31 | Motori | PWM di banco che muove | 150: solo ronzio; 255: rotazione confermata dall'operatore | osservazione visiva + telemetria | ruote sollevate | - | 255 non e' il pwm_max definitivo |
| TBD | Ruota | diametro effettivo | TODO | calibro | ruota montata | - | per la velocita' lineare |
| TBD | Motori | RPM a PWM noto | TODO | conteggio giri in 10 s | ruote sollevate, PWM 255 | - | opzionale |

## Dimensioni gia raccolte

Le quote degli ingombri sono in `docs/hardware/Misure Robotica.pdf` e servono al CAD, non al
controller: non vanno trasferite qui.
