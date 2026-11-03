# Test PWM con avvio scaglionato

**Scopo:** capire se il problema dei due motori insieme e' di alimentazione o di
un canale/motore. Ruote sollevate, robot fissato.

## Sequenza

Dopo 3 s dal reset:

1. A avanti 255 da solo per 2 s;
2. aggiungo B: entrambi a 255 per 4 s;
3. stop 2 s;
4. B avanti 255 da solo per 2 s;
5. aggiungo A: entrambi a 255 per 4 s;
6. stop finale.

## Upload

```sh
arduino-cli compile --fqbn arduino:avr:mega firmware/test/pwm_staggered_test
arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:avr:mega firmware/test/pwm_staggered_test
```

Dopo il test ricaricare il firmware sicuro:

```sh
arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:avr:mega firmware/rcj2027
```

## Interpretazione

- Se il secondo motore aggiunto non parte in entrambe le sequenze, il problema
  e' di alimentazione/corrente (batteria, L298N, GND, cablaggio).
- Se fallisce sempre lo stesso canale/motore, il problema e' in quel canale,
  nel motore o nei suoi fili.
- Se entrambi partono in questa prova ma non nel test simultaneo, l'avvio
  simultaneo provoca uno spunto eccessivo.

## Misure utili

- tensione batteria ai morsetti +12/GND del L298N;
- tensione +12/GND durante entrambi i motori attivi;
- tensione ENA/ENB e OUT1/OUT2/OUT3/OUT4.
