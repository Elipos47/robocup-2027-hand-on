# Architettura di sistema prevista

## Separazione delle responsabilità

```text
Telecamere + IMU + sonar
             │
             ▼
   Raspberry Pi 5: percezione,
   stato, decisione, logging, UI
             │  seriale versionato
             ▼
   Arduino Mega: motori, servo,
   sensori rapidi, heartbeat, watchdog
             │
             ▼
       Batterie e attuatori
```

## Raspberry Pi 5

Responsabilita':

- acquisizione e calibrazione delle due telecamere;
- elaborazione linea, marker, stanza e vittime;
- macchina a stati e logica di recupero;
- interfaccia operatore e telemetria;
- log strutturati e report di run.

Non deve inviare comandi non validati o perdere il controllo di sicurezza in caso di errore.

## Arduino Mega

Responsabilita':

- PWM e direzione dei motori;
- lettura di HC-SR04 e IMU;
- gestione del servo;
- heartbeat e stop watchdog;
- risposte e contatori di errore.

Il firmware parte dagli sketch di banco in `firmware/test/`. Il protocollo v1.1 e' definito in
`SERIAL_PROTOCOL.md` e implementato sia lato Raspberry (`software/rcj2027/`) sia lato Arduino
(`firmware/rcj2027/`). P1, B0, B1-1, B1-2 e B1-3 hanno verificato link, logger, comandi motori,
sonar e IMU; B0 resta parziale per freno/coast, ripetizione, corrente e temperatura.

## Layout del codice

```text
firmware/
  test/<nome>/<nome>.ino   sketch di banco con README
software/
  rcj2027/                 protocollo, trasporto, logger, safety, sessione, diagnostica,
                           visione linea (line_vision.py), stream live (live_view.py)
  tests/                   test host (unittest)
scripts/                   build, test e validazione
```

## Configurazione hardware minima

Il software non deve incorporare valori hardware non confermati. I parametri usati dal
controller sono raccolti in `docs/hardware/MINIMUM_HARDWARE_DATA.md`; quelli non critici
possono restare configurabili, mentre i parametri di sicurezza mancanti disabilitano il
movimento reale.

## Sicurezza

- comandi motori limitati e osservabili;
- `stop` prioritario su ogni altra operazione;
- heartbeat periodico;
- timeout misurato prima di usare il robot;
- fail-safe se Raspberry, sensori o comunicazione non sono sani.

## Decisioni aperte

- ruolo e posizione del servo;
- IMU effettivo e sua necessita' di Gyro;
- contratto dei sensori e frequenze;
- interfaccia operatore e sua alimentazione;
- formato dei log e rotazione sul Raspberry.
