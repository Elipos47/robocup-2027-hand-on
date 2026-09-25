# Robocup2027HandOn

## Scopo

Repository di contesto e sviluppo hardware-first per **RoboCupJunior Rescue Line 2027**.
L'obiettivo e' costruire e validare sul robot reale un sistema Raspberry Pi 5 + Arduino Mega
capace di seguire la linea, gestire ostacoli e terreni, riconoscere vittime e completare il
percorso con evidenze raccolte in laboratorio e sul campo.

Il progetto precedente resta intatto e non viene importato qui: niente Webots, niente
controller, niente log di simulazione e niente codice funzionale gia' sviluppato.

## Stato

- Fase corrente: definizione del contratto hardware minimo e raccolta dei pochi dati necessari
  per iniziare il software.
- Le quote degli ingombri gia raccolte in `docs/hardware/Misure Robotica.pdf` sono per il CAD e
  non sono trattate come parametri del controller senza conferma.
- Simulazione: non e' un gate di sviluppo per questa linea di lavoro.
- Avanzamento: una funzione software viene considerata pronta solo dopo una prova ripetibile
  sul banco o sul campo, con sicurezza e diagnostica associate.
- Regolamento: RCJ Rescue Line 2026 e' la base provvisoria; la versione 2027 deve sostituirla
  quando pubblicata.

## Mappa dei documenti

| Area | Documento |
|---|---|
| Obiettivi e regole | `docs/objectives/DEVELOPMENT_PLAN.md`, `docs/rules/` |
| Inventario hardware | `docs/hardware/INVENTORY.md` |
| Dati minimi per il software | `docs/hardware/MINIMUM_HARDWARE_DATA.md` |
| Misure e TODO | `docs/MEASUREMENT_LOG.md` |
| Riferimento CAD | `docs/hardware/CAD_REFERENCE.md` |
| Bring-up e calibrazione | `docs/hardware/BRINGUP_CHECKLIST.md`, `docs/hardware/CALIBRATION.md` |
| Architettura | `docs/architecture/SYSTEM_ARCHITECTURE.md` |
| Protocollo seriale (proposta) | `docs/architecture/SERIAL_PROTOCOL.md` |
| Test sul campo | `docs/testing/FIELD_TEST_PLAN.md` |
| Decisioni aperte | `docs/DECISIONS.md` |
| Provenienza e scelte di importazione | `docs/SOURCE_MAP.md` |

## Hardware di riferimento

- Raspberry Pi 5 4GB: visione, logica di alto livello e interfaccia operatore.
- Arduino Mega 2560: motori, PWM, sensori rapidi, servo e watchdog.
- Due telecamere: camera linea e camera stanza/vittime.
- HC-SR04, BNO085, L298N, UPS, schermo, batterie e servo sono presenti sull'hardware ma
  alcuni dettagli restano da verificare a banco.

L'inventario, il contratto minimo e le limitazioni sono in
`docs/hardware/INVENTORY.md` e `docs/hardware/MINIMUM_HARDWARE_DATA.md`.

## Regole d'uso

1. Non cambiare hardware o cablaggi senza approvazione.
2. Non dichiarare una misura affidabile se non ha data, strumento e condizione di prova.
3. Non usare un test statico o una simulazione al posto di una prova reale.
4. Ogni modifica deve avere una prova, un test, un log e una spiegazione per l'operatore.
5. I segreti e le credenziali non vanno nel repository.

## Prossimo lavoro

1. Compilare il blocco prioritario di `docs/MEASUREMENT_LOG.md` con i dati minimi per il
   software, usando `docs/hardware/MINIMUM_HARDWARE_DATA.md` come checklist.
2. Proporre e approvare la mappa dei pin e la configurazione seriale senza modificare i
   cablaggi per istinto.
3. Definire il primo contratto seriale e il logger strutturato mantenendo il movimento
   disabilitato finche i parametri di sicurezza non sono confermati.
4. Eseguire il primo test controllato sul campo della linea, senza dichiarare il percorso
   completo.

La validazione documentale iniziale si esegue con:

```sh
bash scripts/check_context.sh
```
