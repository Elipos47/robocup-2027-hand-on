# Inventario hardware reale

**Stato:** inventario preliminare; gli ingombri di molte schede sono documentati in
`Misure Robotica.pdf`, ma i dati di funzionamento necessari al software non sono ancora stati
verificati a banco.

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
| Batterie | alimentazione | 2 pacchi Li-Ion 3S 11.1 V 2.6 Ah 28.86 Wh in parallelo: 11.1 V, 5.2 Ah, 57.72 Wh dichiarati; corrente, BMS e fusibili da verificare |
| Servo | meccanismo ausiliario | funzione e modello da verificare |
| Ruote/cinghie | locomozione | non ancora identificate |

## Dati minimi per iniziare il software

Non serve completare tutto l'inventario prima di scrivere il software. Il contratto minimo e
descritto in `docs/hardware/MINIMUM_HARDWARE_DATA.md` e comprende:

- tensione nominale della batteria;
- asse e verso dei due motori;
- PWM massimo sicuro e comportamento di freno/arresto;
- diametro effettivo della ruota;
- tipo di collegamento Arduino-Pi e configurazione seriale;
- altezza e inclinazione della camera linea;
- orientamento degli assi del BNO085, se viene usato;
- altezza e inclinazione di HC-SR04, se viene usato nel primo test.

Un dato di questo gruppo che resta `TODO` viene mantenuto tale nel codice. Se manca un
parametro di sicurezza, il movimento reale resta disabilitato.

## Dati differiti

Questi dati sono utili per il CAD, la sicurezza e le prove sul campo, ma non sono prerequisiti
per iniziare lo scaffolding del software:

- quote complete di fori, connettori e cavi delle schede;
- massa dei singoli componenti, massa totale e baricentro;
- composizione, capacita' e durata della batteria;
- RPM a vuoto e sotto carico se non sono necessari per la prima versione a PWM;
- larghezza ruote, cinghie, pulegge e attrito completo;
- taratura e rumore dettagliati di HC-SR04 e BNO085;
- calibrazione ottica completa delle due telecamere;
- caduta di tensione e riscaldamento del L298N;
- meccanismo, corsa e limiti del servo;
- porte seriali effettive, fusibili e alimentazione dedicata.

## Riferimento dimensionale

Il file `Misure Robotica.pdf` raccoglie le dimensioni di batterie, Arduino, Raspberry Pi, UPS,
sensore di distanza, BNO085, driver e step-down. Queste quote sono utili per il disegno 3D,
ma non sostituiscono la mappa dei pin, i parametri di movimento o le prove di sicurezza.

## Regole di sicurezza

- Non cambiare motori, driver, batterie, cablaggi o connettori senza approvazione.
- Usare un supporto e una limitazione di corrente per i primi test.
- Provare sempre i motori con ruote sollevate.
- documentare ogni modifica nello stesso giorno in cui viene eseguita.

## Origine

Questo file riordina l'inventario preliminare disponibile nel progetto precedente, eliminando
il contesto di simulazione e lasciando espliciti i dati non verificati. La provenienza e' in
`docs/SOURCE_MAP.md`.
