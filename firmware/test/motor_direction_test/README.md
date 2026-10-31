# Test direzioni motori

Sketch di banco per Arduino Mega 2560 + L298N. Serve a verificare lato e verso dei due
motori prima di scrivere il controller.

**Stato:** compilato; prova a banco da eseguire.

## Cablaggio usato

| Segnale L298N | Pin Mega 2560 |
|---|---:|
| `ENA` | 12 |
| `IN1` | 22 |
| `IN2` | 23 |
| `ENB` | 13 |
| `IN3` | 24 |
| `IN4` | 25 |

Il modulo non ha jumper `ENA`/`ENB`. Alimentazione motori separata dall'Arduino, con GND comune.

## Caricamento

1. Apri `motor_direction_test.ino` con l'Arduino IDE.
2. Seleziona **Arduino Mega 2560** e la porta corretta.
3. Tieni spenta l'alimentazione dei motori durante l'upload.
4. Alimenta Arduino via USB e i motori con la loro alimentazione.
5. Solleva le ruote.
6. Apri il Serial Monitor a **115200 baud**.

Da terminale:

```sh
bash scripts/build.sh
arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:avr:mega firmware/test/motor_direction_test
```

La porta puo' cambiare: verificala con `arduino-cli board list`.

## Comandi

| Tasto | Azione |
|---|---|
| `1` | canale A avanti (`IN1` alto, `IN2` basso) |
| `2` | canale A indietro (`IN1` basso, `IN2` alto) |
| `3` | canale B avanti (`IN3` alto, `IN4` basso) |
| `4` | canale B indietro (`IN3` basso, `IN4` alto) |
| `0` | stop |
| `+` / `-` | PWM di test +/- 10 (parte da 80, limite 120) |
| `?` | aiuto |

Ogni comando dura 3 secondi e poi si ferma da solo. Se la ruota non si muove, premi `+` e
riprova; se arriva a 120 senza muoversi, fermati e riporta il comportamento.

## Risultato da riportare

```text
canale A = sinistro / destro
canale A: comando 1 -> ruota avanti / indietro
canale B = sinistro / destro
canale B: comando 3 -> ruota avanti / indietro
PWM minimo che muove le ruote =
note (rumore, ruota che non gira, verso strano, ecc.) =
```

"Avanti" nello sketch indica solo `IN` alto: il verso reale della ruota e' quello che si osserva.
Il PWM usato qui non e' il `pwm_max` definitivo del robot.
