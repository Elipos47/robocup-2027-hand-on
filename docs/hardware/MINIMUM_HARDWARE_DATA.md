# Dati hardware minimi per il software

**Scopo:** elencare i pochi dati fisici che il software non puo' ricavare da solo.

**Regola:** un dato non confermato resta `TODO`. Non si inseriscono valori inventati. Un dato
mancante non blocca la scrittura del codice: blocca solo la funzione che ne dipende.

**Questionario operativo:** `docs/hardware/MINIMUM_HARDWARE_QUESTIONS.md`.

## Contratto minimo

| Campo | Valore | Uso |
|---|---|---|
| `battery_nominal_v` | `11.1` | scala tensione e limiti dei motori |
| `motor_side_map` | `A = destra, B = sinistra` | quale motore e' sinistro e quale destro |
| `motor_direction_polarity` | `A e B invertiti` | verso avanti/indietro; corretto nel software |

Sono tre dati fisici che il software non puo' dedurre, e si ricavano in cinque minuti con le
ruote sollevate: si comanda un motore alla volta e si guarda quale gira e in che verso.

La polarita' e la mappa dei lati sono state verificate a banco il 2026-10-31: entrambi i canali
girano indietro con il comando "avanti" (corretto nel software; dopo l'upload `1` e `3` vanno
avanti) e il canale A e' la ruota destra, il canale B la ruota sinistra.

La batteria e' nota dall'etichetta (2026-10-22): due pacchi Li-Ion 3S da 11.1 V 2.6 Ah 28.86 Wh
in parallelo, cioe' 11.1 V, 5.2 Ah e 57.72 Wh dichiarati. In parallelo la tensione non cambia.

## Scelte del software, non dati da chiedere

- `pwm_max`: motori RS PRO 834-7631 (4.5-15 V DC, riduttore 100:1, 60 rpm di uscita a 12 V da
  scheda). Con batteria 11.1 V nominali e caduta del L298N, il duty pieno resta sotto i 15 V;
  il valore definitivo si sceglie dopo la prova di spunto, corrente e temperatura. E' un limite
  scelto, non misurato. Prova di banco 2026-10-31: a 150 i motori ronzavano senza ruotare; a
  255 i motori hanno girato (conferma dell'operatore).
- freno, coast e stop: comportamento deciso nel codice.
- baud e porta seriale: 115200 8N1 su `/dev/ttyACM0`, verificati in B1-1.
- velocita' in mm/s, odometria e RPM: servono solo quando si passa dal PWM grezzo alla velocita'
  controllata.

## Il resto si scopre provando

- collegamento Arduino-Pi (USB o UART): si vede quando lo colleghi;
- orientamento dell'IMU: si legge dai valori;
- altezza e inclinazione della camera: si regolano guardando l'immagine;
- corrente, BMS e cutoff della batteria: si osservano sotto carico, se danno problemi.

## Mappa dei pin

Non e' un dato ma una scelta di progetto: si propone, si approva e solo dopo si tocca il
cablaggio. Serve per `ENA`, `ENB`, `IN1..IN4` dell'L298N e, se usati, servo, HC-SR04, BNO085,
led e interruttore.

### L298N - mappa fornita dall'utente

| Segnale | Pin Arduino Mega 2560 | Note |
|---|---:|---|
| `ENA` | 12 | PWM, canale A |
| `IN1` | 22 | direzione, canale A |
| `IN2` | 23 | direzione, canale A |
| `ENB` | 13 | PWM, canale B |
| `IN3` | 24 | direzione, canale B |
| `IN4` | 25 | direzione, canale B |

- Canale A: `ENA` + `IN1`/`IN2`, verso `OUT1`/`OUT2` del L298N.
- Canale B: `ENB` + `IN3`/`IN4`, verso `OUT3`/`OUT4` del L298N.
- I pin 12 e 13 sono PWM sul Mega 2560. Il pin 13 ha il LED di bordo: con `ENB` in PWM il LED
  lampeggia e non va usato come indicatore di stato.
- Il modulo L298N non ha jumper `ENA`/`ENB`: gli enable sono pilotati direttamente dai pin 12 e
  13.
- La corrispondenza e' verificata a banco: canale A = ruota destra, canale B = ruota sinistra.
- La mappa e' una decisione, non una misura: freno e limite PWM restano da verificare.

### HC-SR04 - mappa fornita dall'utente

| Segnale | Pin Arduino Mega 2560 | Note |
|---|---:|---|
| `TRIG` | 27 | uscita digitale |
| `ECHO` | 26 | ingresso digitale, 5 V |

- I pin 26 e 27 sono digitali e non hanno funzioni alternate sul Mega: nessun conflitto con
  seriale, I2C o SPI.
- Il modulo e' alimentato a 5 V; l'uscita `ECHO` e' compatibile con gli ingressi del Mega.
- Altezza e inclinazione di montaggio restano da misurare quando il sensore entra in un test.

### BNO085 - mappa fornita dall'utente

| Segnale | Pin Arduino Mega 2560 | Note |
|---|---:|---|
| `SDA` | 20 | I2C hardware |
| `SCL` | 21 | I2C hardware |

- I pin 20 e 21 sono l'I2C hardware del Mega 2560: nessun conflitto con motori o sonar.
- Il modulo e' un breakout Adafruit che accetta 5 V diretti, confermato dall'utente
  (2026-10-31): il collegamento all'I2C a 5 V del Mega e' ammesso.
- Modello esatto del modulo e orientamento degli assi restano `TODO`.

Non ancora definiti: pin del servo, LED e interruttore.

Nessun cablaggio va modificato prima dell'approvazione esplicita della mappa.

## Riferimento dimensionale

Le quote di schede e batterie sono in `docs/hardware/Misure Robotica.pdf` e servono al CAD, non
al controller: non vanno riportate qui.

## Modello di raccolta

```text
battery_nominal_v = 11.1
motor_side_map = A=destra, B=sinistra
motor_direction_polarity = A e B invertiti
```
