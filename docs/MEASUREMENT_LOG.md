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
| 2026-10-31 | Camera USB 5MP | frame e qualita' | 640x480 @30; luminosita' 70.9-80.9, contrasto 52.2-54.3, nitidezza 67.5-73.1 | OpenCV 4.11 | USB, device 0 | soglie software | B1-4: camera USB PASS |
| 2026-10-31 | Camera CSI IMX708 | frame e qualita' | 640x480; luminosita' 147.9, contrasto 34.6, nitidezza 9.3 | Picamera2/libcamera | CSI camera 0, AF continuo, warm-up 2 s | soglie software | B1-4: FAIL fuoco/montaggio, frame sfocato |
| 2026-10-31 | HC-SR04 | stabilita' su 10 s | 99/100 e 101/101 validi; salto max 695-697 mm | telemetria + analisi software | robot fermo, ambiente con riflessi | non calibrata | B1-4: FAIL stabilita', da ripetere con bersaglio stabile |
| 2026-10-31 | HC-SR04 | riferimento 500 mm | media 597.6 mm, errore +97.6 mm, salto 703 mm | telemetria + analisi software | target a 500 mm dichiarato, robot fermo | pochi mm (seriale) | FAIL: probabile offset di misura dal telaio o riflessioni |
| 2026-10-31 | BNO085 | rumore a riposo | 98/100 validi; yaw std 3.2 mdeg, pitch 59.8 mdeg, roll 28.2 mdeg | telemetria + analisi software | robot fermo, 10 s | pochi mdeg | B1-4: PASS |
| 2026-10-31 | BNO085 | rotazione yaw manuale | 178/180 validi; yaw -6.7..62.0 deg; asse dominante yaw | telemetria + analisi software | rotazione a mano ~90 deg | movimento manuale | B1-4: PASS |
| 2026-10-31 | BNO085 | stazionario dopo correzione assi | 100/100 validi; pitch std 4.2 mdeg, roll 10.7 mdeg, yaw 7.1 mdeg | telemetria + analisi software | robot fermo, 10 s | pochi mdeg | pitch/roll scambiati corretti; PASS |
| 2026-10-31 | BNO085 | rotazione pitch manuale | 149/151 validi; pitch -21.2..8.0 deg; asse dominante pitch | telemetria + analisi software | muso su/giu' a mano | movimento manuale | B1-4: PASS dopo swap |
| 2026-10-31 | BNO085 | rotazione roll manuale | 150/150 validi; roll -19.8..25.6 deg; asse dominante roll | telemetria + analisi software | inclinazione destra/sinistra a mano | movimento manuale | B1-4: PASS dopo swap |
| 2026-10-31 | Motori | PWM di banco che muove | 150: solo ronzio; 255: rotazione confermata dall'operatore | osservazione visiva + telemetria | ruote sollevate | - | 255 non e' il pwm_max definitivo |
| TBD | Ruota | diametro effettivo | TODO | calibro | ruota montata | - | per la velocita' lineare |
| TBD | Motori | RPM a PWM noto | TODO | conteggio giri in 10 s | ruote sollevate, PWM 255 | - | opzionale |

## Dimensioni gia raccolte

Le quote degli ingombri sono in `docs/hardware/Misure Robotica.pdf` e servono al CAD, non al
controller: non vanno trasferite qui.
