# Test direzioni motori

Sketch di banco per Arduino Mega 2560 + L298N. Serve a verificare lato e verso dei due
motori prima di scrivere il controller.

**Motori:** RS PRO 834-7631, 4.5-15 V DC, riduttore 100:1.

**Mappa:** canale A = ruota destra, canale B = ruota sinistra (verificato 2026-10-31).

**Stato:** compilato; prova a banco in corso.

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
| `1` | canale A avanti (`IN1` basso, `IN2` alto) |
| `2` | canale A indietro (`IN1` alto, `IN2` basso) |
| `3` | canale B avanti (`IN3` basso, `IN4` alto) |
| `4` | canale B indietro (`IN3` alto, `IN4` basso) |
| `0` / `s` | stop entrambi i canali |
| `+` / `-` | PWM di test +/- 10 (parte da 150, limite 255) |
| `?` | aiuto |

La polarita' e' invertita nel software: con il cablaggio attuale "avanti" usa `IN` basso. Il
cablaggio non e' stato modificato.

Ogni comando resta attivo fino a stop manuale (`0` o `s`); non c'e' stop automatico. Un nuovo
comando `1`-`4` sostituisce quello attivo. Tieni le ruote sollevate e l'alimentazione a portata
di mano.

Il PWM parte da 150 perche' i motori RS PRO 834-7631 hanno una tensione minima di 4,5 V: a
120/255, dopo la caduta del L298N, il motore riceveva circa 4,3 V e restava fermo ronzando. Se
la ruota non si muove, premi `+` e riprova; se arriva a 255 senza muoversi, fermati e riporta il
comportamento. Non lasciare un motore bloccato a lungo: scalda motore e driver.

**Velocita':** il riduttore e' 100:1 e la scheda RS dichiara 60 rpm di uscita a 12 V (circa
72 rpm a vuoto). A 255 il motore riceve circa 9 V dopo la caduta del L298N, quindi sono attesi
circa 45-54 rpm di uscita: e' normale che sembri lento. Per la velocita' lineare serve il
diametro effettivo della ruota.

## Risultato da riportare

```text
canale A = sinistro / destro
canale A: comando 1 -> ruota avanti / indietro
canale B = sinistro / destro
canale B: comando 3 -> ruota avanti / indietro
PWM minimo che muove le ruote =
note (rumore, ruota che non gira, verso strano, ecc.) =
```

"Avanti" nello sketch e' la direzione logica corretta dopo l'inversione software; il verso reale
della ruota e' quello che si osserva. Il PWM usato qui non e' il `pwm_max` definitivo del robot.
