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

Responsabilita' future:

- acquisizione e calibrazione delle due telecamere;
- elaborazione linea, marker, stanza e vittime;
- macchina a stati e logica di recupero;
- interfaccia operatore e telemetria;
- log strutturati e report di run.

Non deve inviare comandi non validati o perdere il controllo di sicurezza in caso di errore.

## Arduino Mega

Responsabilita' future:

- PWM e direzione dei motori;
- lettura di HC-SR04 e IMU;
- gestione del servo;
- heartbeat e stop watchdog;
- risposte e contatori di errore.

Il firmware non verrà implementato in questa fase; il contratto seriale resta una proposta in
`SERIAL_PROTOCOL.md`.

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
