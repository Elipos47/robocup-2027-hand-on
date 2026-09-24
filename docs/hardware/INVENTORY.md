# Inventario hardware reale

**Stato:** inventario preliminare; non tutte le voci sono state verificate a banco.

## Mappa funzionale attuale

```text
Camera NERA (vittime) ─────► Raspberry Pi 5
Camera VERDE (linea) ──────► Raspberry Pi 5
UPS ───────────────────────► Raspberry Pi 5
Raspberry Pi 5 ◄──────────► Arduino Mega 2560 (USB/seriale)
Arduino Mega ──────────────► L298N ─► motori DC
HC-SR04 ───────────────────► Arduino
BNO085 / IMU ──────────────► Arduino
Servo ─────────────────────► Arduino (segnale) + alimentazione dedicata
Batterie ──────────────────► stepdown e L298N
Schermo ──────────────────► Raspberry Pi
```

## Componenti confermati come presenti

| Componente | Ruolo | Stato |
|---|---|---|
| Raspberry Pi 5 4GB | elaborazione e visione | presente |
| Arduino Mega 2560 | controllo basso livello | presente |
| Camera linea | imaging della linea | presente |
| Camera vittime | imaging stanza/vittime | presente |
| UPS | continuità alimentazione Pi | presente |
| L298N | driver motori | presente |
| HC-SR04 | distanza frontale | presente |
| Schermo | diagnostica | presente |
| BNO085 | IMU candidato | da confermare modello e ruolo |
| Batterie | alimentazione | tipo e tensione da verificare |
| Servo | meccanismo ausiliario | funzione e modello da verificare |
| Ruote/cinghie | locomozione | non ancora identificate |

## Dati ancora da misurare

- sigla e RPM dei motori a vuoto e sotto carico;
- diametro e larghezza ruote/cinghie, rapporto e attrito;
- massa totale e distribuzione del peso;
- composizione, tensione e capacità delle batterie;
- caduta di tensione del L298N e limiti PWM sicuri;
- posizione e orientamento delle due telecamere;
- taratura e rumore di HC-SR04 e BNO085;
- meccanismo e limiti del servo;
- connettori, fusibili, massa della scocca e centro di massa;
- porte seriali effettive e alimentazione dedicata.

## Regole di sicurezza

- Non cambiare motori, driver, batterie, cablaggi o connettori senza approvazione.
- Usare un supporto e una limitazione di corrente per i primi test.
- Provare sempre i motori con ruote sollevate.
- documentare ogni modifica nello stesso giorno in cui viene eseguita.

## Origine

Questo file riordina l'inventario preliminare disponibile nel progetto precedente, eliminando
il contesto di simulazione e lasciando espliciti i dati non verificati. La provenienza e' in
`docs/SOURCE_MAP.md`.
