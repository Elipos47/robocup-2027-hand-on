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
motore_sinistro =
motore_destro =
```

## Q3. Verso di ciascun motore

Con il comando "avanti":

```text
verso_sinistro = avanti / indietro / non verificato
verso_destro   = avanti / indietro / non verificato
```

## Come si misurano

Ruote sollevate, un motore alla volta a PWM basso: si guarda quale gira e in che verso. Cinque
minuti, nessuno strumento.

## Mappa dei pin

Non e' una domanda: e' una scelta di progetto da proporre e approvare prima di cablare.
