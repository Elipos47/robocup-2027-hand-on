# Test PWM canali separati

**Scopo:** capire se il guasto del motore destro e' nel canale A del L298N, nel
motore o nel cablaggio. Ruote sollevate, robot fissato.

## Cablaggio

| Canale | ENA/ENB | IN | Motore atteso |
|---|---:|---|---|
| A | ENA 12 | IN1 22, IN2 23 | ruota destra |
| B | ENB 13 | IN3 24, IN4 25 | ruota sinistra |

GND comune Arduino/L298N, alimentazione motori separata.

## Sequenza

Dopo 3 s dal reset:

1. A avanti 255 per 4 s, stop 2 s;
2. B avanti 255 per 4 s, stop 2 s;
3. A indietro 255 per 4 s, stop 2 s;
4. B indietro 255 per 4 s, stop finale.

## Upload

```sh
arduino-cli compile --fqbn arduino:avr:mega firmware/test/pwm_channel_test
arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:avr:mega firmware/test/pwm_channel_test
```

Dopo il test ricaricare il firmware sicuro:

```sh
arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:avr:mega firmware/rcj2027
```

## Come leggere il risultato

- Se A muove la ruota sinistra, i canali o i connettori motore sono scambiati.
- Se A non muove nulla e B muove la sinistra, il problema e' nel canale A, nel
  motore destro o nel suo cablaggio.
- Per separare canale A e motore destro: misurare la tensione su OUT1/OUT2
  durante A avanti; se c'e' tensione ma il motore non gira, il motore o i fili
  sono il problema.
