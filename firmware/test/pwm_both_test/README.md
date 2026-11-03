# Test PWM entrambi i canali

**Scopo:** verificare che entrambi i canali del L298N ricevano PWM 255 e facciano
girare le ruote. E' un test di banco, non il firmware operativo.

## Cablaggio

| Segnale L298N | Pin Mega 2560 |
|---|---:|
| ENA | 12 |
| IN1 | 22 |
| IN2 | 23 |
| ENB | 13 |
| IN3 | 24 |
| IN4 | 25 |

GND comune tra Arduino e L298N; alimentazione motori separata. Ruote sollevate
e robot fissato.

## Comportamento

Dopo 3 s dal reset:

1. entrambi i motori avanti a 255 per 4 s;
2. stop 2 s;
3. entrambi i motori indietro a 255 per 4 s;
4. stop 2 s;
5. ripete per 2 cicli e termina con i motori fermi.

Non usa la seriale per i comandi: stampa solo i passaggi a 115200 baud.

## Upload

```sh
arduino-cli compile --fqbn arduino:avr:mega firmware/test/pwm_both_test
arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:avr:mega firmware/test/pwm_both_test
```

Il firmware operativo sicuro va ricaricato dopo il test:

```sh
arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:avr:mega firmware/rcj2027
```

## Risultato atteso

- entrambe le ruote girano in avanti a 255;
- stop;
- entrambe girano indietro a 255;
- stop finale.

Se una ruota non gira, il problema e' nel canale corrispondente. Se nessuna
gira, controllare alimentazione motori, ENA/ENB, GND comune e L298N.
