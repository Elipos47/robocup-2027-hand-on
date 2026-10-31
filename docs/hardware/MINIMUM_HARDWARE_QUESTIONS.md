# Questionario hardware minimo

Servono tre risposte. Il resto non blocca il software: si scopre provando.

## Q1. Batteria

```text
tensione_nominale_v = 11.1    # 2 pacchi Li-Ion 3S in parallelo, 2026-10-22
```

Due pacchi da 11.1 V 2.6 Ah 28.86 Wh in parallelo danno 11.1 V, 5.2 Ah e 57.72 Wh dichiarati.
Per il software basta la tensione.

## Q2. Quale motore e' il sinistro

```text
motore_sinistro = B
motore_destro = A
```

## Q3. Verso di ciascun motore

Con il comando "avanti":

```text
verso_sinistro = avanti (polarita' corretta nel software)
verso_destro   = avanti (polarita' corretta nel software)
```

## Come si misurano

Ruote sollevate, un motore alla volta a PWM basso: si guarda quale gira e in che verso. Cinque
minuti, nessuno strumento. Lo sketch `firmware/test/motor_direction_test/` guida la prova.

## Mappa dei pin

Non e' una domanda: e' una scelta di progetto. La mappa attuale (L298N, HC-SR04, BNO085) e' in
`docs/hardware/MINIMUM_HARDWARE_DATA.md`; restano da definire i pin di servo, LED e interruttore.
