# Robocup2027HandOn

## Scopo

Repository di sviluppo hardware-first per **RoboCupJunior Rescue Line 2027**.
L'obiettivo e' costruire e validare sul robot reale un sistema Raspberry Pi 5 + Arduino Mega
capace di seguire la linea, gestire ostacoli e terreni, riconoscere vittime e completare il
percorso con evidenze raccolte in laboratorio e sul campo.

Il progetto precedente resta intatto e non viene importato qui: niente Webots, niente controller
del progetto precedente, niente log di simulazione e niente codice funzionale gia' sviluppato.

## Stato

- Fase corrente: avvio dello sviluppo codice. Il firmware di banco e il software Raspberry
  entrano nel repository; il primo sketch ha verificato lati e verso dei motori.
- Fatto: package `software/rcj2027/` con protocollo v1.1, trasporto finto, logger e gate di
  sicurezza; test unittest verdi e demo fake disponibile. Il movimento reale resta disabilitato.
- Fatto: firmware Arduino del protocollo v1.1 in `firmware/rcj2027/`, compilato; default con
  movimento disabilitato e watchdog da misurare.
- Fatto: protocollo verificato sul Mega senza movimento (test P1): handshake, status, stop e
  gate `MOTION_DISABLED`.
- Fatto: B0 parziale: stop X con ack 3,7-3,9 ms e watchdog a 1007-1008 ms; a 150 i motori
  ronzavano senza ruotare, a 255 la rotazione e' da confermare. Freno/coast ancora aperti.
- Contratto minimo completo: batteria 11.1 V da etichetta; A = ruota destra, B = ruota
  sinistra; polarita' invertita corretta nel software. La mappa dei pin e' in
  `docs/hardware/MINIMUM_HARDWARE_DATA.md`.
- Le quote degli ingombri gia raccolte in `docs/hardware/Misure Robotica.pdf` sono per il CAD e
  non sono trattate come parametri del controller senza conferma.
- Simulazione: non e' un gate di sviluppo per questa linea di lavoro.
- Avanzamento: una funzione software viene considerata pronta solo dopo una prova ripetibile
  sul banco o sul campo, con sicurezza e diagnostica associate.
- Regolamento: RCJ Rescue Line 2026 e' la base provvisoria; la versione 2027 deve sostituirla
  quando pubblicata.

## Mappa del progetto

| Area | Percorso |
|---|---|
| Firmware Arduino | `firmware/`, `firmware/test/`, `firmware/rcj2027/` |
| Software Raspberry Pi | `software/rcj2027/`, `software/tests/` |
| Build e test | `scripts/build.sh`, `scripts/test.sh`, `scripts/check_context.sh` |
| Obiettivi e regole | `docs/objectives/DEVELOPMENT_PLAN.md`, `docs/rules/` |
| Inventario hardware | `docs/hardware/INVENTORY.md` |
| Dati minimi per il software | `docs/hardware/MINIMUM_HARDWARE_DATA.md` |
| Questionario hardware minimo | `docs/hardware/MINIMUM_HARDWARE_QUESTIONS.md` |
| Misure e TODO | `docs/MEASUREMENT_LOG.md` |
| Riferimento CAD | `docs/hardware/CAD_REFERENCE.md` |
| Bring-up e calibrazione | `docs/hardware/BRINGUP_CHECKLIST.md`, `docs/hardware/CALIBRATION.md` |
| Architettura | `docs/architecture/SYSTEM_ARCHITECTURE.md` |
| Protocollo seriale v1.1 | `docs/architecture/SERIAL_PROTOCOL.md` |
| Test di banco | `docs/testing/PROTOCOL_BENCH_TEST.md`, `docs/testing/B0_BENCH_TEST.md` |
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

1. Completare B0: conferma visiva, freno/coast e ripetizione del test.
2. Integrare Raspberry e Arduino con il trasporto reale e registrare i log (B1).
3. Scegliere `pwm_max` e timeout watchdog definitivi; misurare diametro ruota e RPM.
4. Eseguire il primo test controllato della linea sul campo.

La validazione e la build si eseguono con:

```sh
bash scripts/test.sh
```
