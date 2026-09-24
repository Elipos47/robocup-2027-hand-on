# Riferimento CAD esterno

## Scopo

Il CAD e' un riferimento hardware esterno e read-only. Non viene copiato nel repository e non
costituisce ancora una base autorizzata per il software.

**File sorgente:**

```text
/home/elipos/Omarchy Shared/AssiemeWebots.step
```

Il nome del file conserva il nome storico dell'assieme; il suo contenuto e' un assembly CAD,
non un modulo di simulazione.

## Analisi disponibile

- formato STEP ISO-10303-21, schema AP214;
- contesto geometrico principale in millimetri;
- 64 prodotti e 84 occorrenze di assemblaggio;
- 146 solidi B-rep e 176 shell chiuse;
- 16.173 facce avanzate e 144.343 punti cartesiani;
- importazione OCCT preliminare: 157 solidi geometrici;
- ingombro trasformato preliminare: circa 156,1 × 194,6 × 136,6 mm.

## Limiti

Non sono ancora determinati e non vanno dedotti senza verifica:

- asse longitudinale del robot;
- origine e punto a terra tra le ruote;
- posizione/orientamento delle telecamere e dei sensori;
- massa dei componenti e centro di massa;
- corrispondenza tra i nomi CAD e le parti stampate/montate;
- geometria delle ruote, cinghie e organi di trasmissione.

## Regole d'uso

1. Non modificare il file sorgente.
2. Prima di un export derivato, misurare un'altezza nota e verificare scala e orientamento.
3. Usare il CAD per supportare le decisioni hardware, non per dichiarare un test software.
4. Registrare ogni export e ogni misura in `docs/MEASUREMENT_LOG.md`.
5. Una mesh non sostituisce la massa reale, il contatto delle ruote o la calibrazione dei sensori.
