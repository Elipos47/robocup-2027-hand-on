# Test A avanti in loop

**Scopo:** tenere il canale A in avanti a PWM 255 per 5 s e fermo per 5 s, in
ciclo continuo, per fare misure ripetute con il multimetro senza premere reset.
Ruote sollevate, robot fissato.

## Cablaggio

| Canale | ENA/ENB | IN | Motore atteso |
|---|---:|---|---|
| A | ENA 12 | IN1 22, IN2 23 | ruota destra |
| B | ENB 13 | IN3 24, IN4 25 | ruota sinistra (ferma) |

GND comune Arduino/L298N, alimentazione motori separata. Il canale B viene
inizializzato e tenuto fermo, cosi' non puo' muoversi per un pin lasciato
flottante.

## Sequenza

Dopo 3 s dal reset, in loop:

1. A avanti 255 per 5 s;
2. stop per 5 s;
3. riparte da 1.

La seriale a 115200 baud stampa l'inizio di ogni fase con il timestamp
`millis()`.

## Upload

Dal Raspberry, nella root del repository:

```sh
arduino-cli compile --fqbn arduino:avr:mega firmware/test/pwm_a_forward_test
arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:avr:mega firmware/test/pwm_a_forward_test
```

Dopo il test ricaricare il firmware sicuro:

```sh
arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:avr:mega firmware/rcj2027
```

## Sicurezza

- Ruote sollevate e robot fissato: il test non si ferma da solo.
- Per fermare togli alimentazione ai motori. Il reset non ferma il ciclo:
  lo fa ripartire dopo 3 s.
- Non lasciare il canale A alimentato a lungo se il motore e' fermo o il
  L298N scalda: la prova serve a misurare, non a tenere il motore in stallo.

## Misure utili

Durante la fase "A avanti 255" (5 s), con il puntale nero sul GND del L298N:

| Misura | Atteso con ponte e alimentazione sani |
|---|---|
| `+12` L298N -> `GND` | 10-12 V |
| batteria `+` -> `-` | 10-12 V |
| `5V` Arduino -> `GND` | ~5 V |
| `ENA` -> `GND` | ~5 V |
| `OUT1` -> `GND` | ~9-10 V con motore collegato |
| `OUT2` -> `GND` | ~0,5-1,5 V |
| `OUT1` -> `OUT2` | ~8-9 V con motore collegato |

Poi ripeti `OUT1` -> `GND` e `OUT1` -> `OUT2` con il motore A scollegato:
se salgono a ~10-11 V il ponte e' sano e il calo e' sotto carico; se restano
bassi anche a vuoto, il problema e' nel ponte o nell'alimentazione.

## Come leggere il risultato

- `+12` crolla sotto carico: batteria, BMS, switch o connettori di
  alimentazione.
- `+12` stabile ma `OUT1` basso anche a vuoto: canale alto del L298N.
- `+12` stabile e `OUT1` a vuoto alto, ma sotto carico crolla: motore A,
  cablaggio del motore o massa di ritorno.
- `5V` o `ENA` bassi: Arduino, pin 12, filo o jumper ENA/ENB.
- L298N molto caldo dopo pochi secondi: protezione termica o corrente
  eccessiva.
