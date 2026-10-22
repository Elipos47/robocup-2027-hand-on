# Dati hardware minimi per il software

**Scopo:** elencare i pochi dati fisici che il software non puo' ricavare da solo.

**Regola:** un dato non confermato resta `TODO`. Non si inseriscono valori inventati. Un dato
mancante non blocca la scrittura del codice: blocca solo la funzione che ne dipende.

**Questionario operativo:** `docs/hardware/MINIMUM_HARDWARE_QUESTIONS.md`.

## Contratto minimo

| Campo | Valore | Uso |
|---|---|---|
| `battery_nominal_v` | `11.1` | scala tensione e limiti dei motori |
| `motor_side_map` | `TODO` | quale motore e' sinistro e quale destro |
| `motor_direction_polarity` | `TODO` | verso avanti/indietro di ciascun motore |

Sono tre dati fisici che il software non puo' dedurre, e si ricavano in cinque minuti con le
ruote sollevate: si comanda un motore alla volta e si guarda quale gira e in che verso.

La batteria e' nota dall'etichetta (2026-10-22): due pacchi Li-Ion 3S da 11.1 V 2.6 Ah 28.86 Wh
in parallelo, cioe' 11.1 V, 5.2 Ah e 57.72 Wh dichiarati. In parallelo la tensione non cambia.

## Scelte del software, non dati da chiedere

- `pwm_max`: si parte da un valore prudente e si alza in prova; e' un limite scelto, non misurato.
- freno, coast e stop: comportamento deciso nel codice.
- baud e porta seriale: impostati e verificati quando si collega l'Arduino.
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

## Riferimento dimensionale

Le quote di schede e batterie sono in `docs/hardware/Misure Robotica.pdf` e servono al CAD, non
al controller: non vanno riportate qui.

## Modello di raccolta

```text
battery_nominal_v = 11.1
motor_side_map =
motor_direction_polarity =
```
