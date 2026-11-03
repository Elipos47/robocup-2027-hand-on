# Test F0-5 - controller dry-run

**ID:** F0-5 (dry-run, senza motori)
**Data:** 2026-11-03
**Software:** `line_control.py`, `line-control`, `line_vision.py`
**Hardware:** nessun comando ai motori; replay dei log della CSI

## Obiettivo

Trasformare lo stato del tracker in una proposta di comando differenziale e verificare che:

- con la linea confermata il robot proponga una sterzata coerente con offset/heading;
- con la linea persa o non confermata proponga **zero** su entrambe le ruote;
- i valori restino entro `pwm_max`;
- il controller non invii nulla alla seriale.

## Configurazione provvisoria

| Parametro | Valore |
|---|---:|
| `pwm_max` | 255 |
| `cruise` | 200 |
| `k_offset` | 0,35 PWM/px |
| `k_heading` | 1,5 PWM/deg |
| `max_correction` | 80 |
| deadband offset | 3 px |
| deadband heading | 1 deg |

Sono valori di **dry-run**, non tarati sul campo. `cruise=200` non e' un valore di movimento
sicuro: B0 ha mostrato ronzio a 150 e rotazione a 255. Prima di collegare i motori servono
misure di PWM minimo e cm/s.

## Replay dei log reali

Comando:

```sh
cd software
python3 -m rcj2027.diagnostics line-control \
  --log logs/<run>.jsonl \
  --commands-out /tmp/<run>-commands.jsonl \
  --json-out /tmp/<run>-control.json
```

| Log | Frame | FOLLOW | STOP not found | STOP not confirmed | Note |
|---|---:|---:|---:|---:|---|
| `f0-live-001` (retta) | 100 | 98 | 0 | 2 | correzione circa -10 PWM, left 190/right 210 |
| `f0-curva` | 1584 | 872 | 687 | 25 | correzione -80..+80, comandi entro 120..255 |
| `f0-gap-7` (182854) | 487 | 270 | 203 | 14 | stop nel gap, follow sui segmenti |
| `f0-ombra-parziale` | 608 | 578 | 12 | 18 | follow prevalente; stop sui bordi anomali |
| `f0-ombra-totale` | 900 | 416 | 467 | 17 | il guard di larghezza ferma il falso bordo |

Nella retta il comando proposto e' left 190 / right 210: la linea e' circa 46 px a sinistra
dell'asse ottico e l'heading e' circa +4 gradi, quindi il controller propone una correzione
moderata a sinistra. Non e' un comando da inviare: e' solo la verifica della legge.

## Sicurezza

- `LineController.update` restituisce zero se `state.found` o `state.confirmed` sono falsi.
- Non esiste ancora uno stato `GAP_CROSS`: nel gap il controller si ferma.
- Nessuna chiamata a `RobotSession.drive` o alla seriale.
- `motor_output=false` nel report.

## Esito

Il controller dry-run e' coerente sui log reali: segue quando la linea e' confermata, si ferma
quando non lo e', e non supera i limiti PWM. **F0-5 dry-run e' coperto**.

Restano da fare:

1. misura del PWM minimo che muove il robot;
2. misura dei cm/s a un PWM noto;
3. taratura di `cruise`, guadagni e deadband;
4. integrazione con `RobotSession.drive` solo dopo gate di sicurezza, ruote sollevate e
   autorizzazione dell'operatore;
5. stato `GAP_CROSS` F1 con timeout e riacquisizione.
