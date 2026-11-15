# Test F0-5 - line following a bassa velocita'

**ID:** F0-5 / LINE-FOLLOW-1
**Data:** 2026-11-15
**Software:** `line-live --drive`, `LineController`, `LineFollower`, `LOW_SPEED_CONFIG`
**Hardware:** Raspberry Pi 5 + Arduino Mega 2560 + L298N, camera CSI, ruote a terra

## Obiettivo

Verificare che il controller di linea comandi davvero i motori con la legge gia' validata in
dry-run, restando a bassa velocita' e fermandosi quando la linea non e' confermata.

## Configurazione provvisoria

| Parametro | Valore | Note |
|---|---:|---|
| `pwm_max` del controller | 130 | limite dei comandi di linea |
| `cruise` | 100 | sopra il PWM minimo misurato a vuoto (65) |
| `max_correction` | 30 | comandi tra 70 e 130 |
| `k_offset` | 0.35 | da tarare |
| `k_heading` | 1.5 | da tarare |
| `send_interval` | 0.1 s | comandi a circa 10 Hz |
| watchdog firmware | 1000 ms | stop se il Pi smette di inviare heartbeat |

`LOW_SPEED_CONFIG` in `software/rcj2027/line_control.py` contiene questi valori. Non sono
tarati sul campo: servono solo per la prima prova.

## Sicurezza

- Prima prova a **ruote sollevate**, con la linea sotto la camera: si verificano direzione,
  stop e seriale senza spostare il robot.
- Poi prova a terra su una **linea retta**, con operatore pronto a togliere alimentazione o a
  premere `q`/`ESC`.
- `--confirm-motion` e' obbligatorio: senza il flag il comando si rifiuta di partire.
- Il controller restituisce zero e invia `X` quando la linea non e' piu' confermata.
- Il firmware deve avere `BENCH_MOTION_ENABLED=true`, `PWM_MAX=255` e watchdog 1000 ms.
  Dopo la prova ricaricare `firmware/rcj2027` sicuro.

## Comandi

Firmware di banco:

```sh
arduino-cli compile --fqbn arduino:avr:mega firmware/rcj2027
arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:avr:mega firmware/rcj2027
```

Line following con preview locale:

```sh
cd software
python3 -m rcj2027.diagnostics line-live \
  --drive --confirm-motion \
  --port /dev/ttyACM0 \
  --cruise 100 --max-correction 30 --pwm-limit 130 \
  --duration 0 --countdown 5 --preview \
  --run-id f0-line-follow-001
```

Senza display, usare lo stream browser:

```sh
python3 -m rcj2027.diagnostics line-live \
  --drive --confirm-motion \
  --port /dev/ttyACM0 \
  --cruise 100 --max-correction 30 --pwm-limit 130 \
  --duration 0 --countdown 5 --http-port 8080 \
  --run-id f0-line-follow-001
```

Per fermare: `q`/`ESC` nella preview, il pulsante di stop nel browser, oppure `Ctrl-C`.
Alla chiusura il programma invia `X` e chiude la sessione.

## Criteri

- **PASS banco:** con la linea centrata le ruote girano nella direzione giusta; spostando la
  linea a destra/sinistra la correzione va nel verso atteso; senza linea i motori si fermano.
- **PASS terra:** il robot segue una linea retta per almeno 1 m senza uscire, con stop pulito
  a fine prova.
- **FAIL:** comandi fuori da 70-130, stop non inviato, perdita seriale non recuperata, robot
  che esce dalla linea o non si ferma.

## Log e report

- JSONL: `software/logs/f0-line-follow-001.jsonl`.
- Eventi utili: `line`, `line_command`, `drive_sent`, `drive_ack`, `stop_sent`, `stop_ack`,
  `session_end`.
- Report: `motor_output=true`, `control.commands_sent`, `control.stops_sent`, `summary`.

## Esito

Da compilare dopo la prova. Il gate F0-5 resta aperto finche' non c'e' una prova a terra
ripetibile.
