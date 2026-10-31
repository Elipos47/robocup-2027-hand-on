# Provenienza e perimetro del nuovo progetto

## Documenti riordinati

- `docs/hardware/INVENTORY.md` deriva dall'inventario hardware preliminare disponibile nel
  progetto precedente, con rimozione del contesto di simulazione.
- `docs/hardware/CAD_REFERENCE.md` deriva dall'analisi dell'assieme STEP, mantenendo solo
  geometria, scala, componenti e limiti di verifica.
- `docs/architecture/SERIAL_PROTOCOL.md` e' la specifica del protocollo v1.1, implementata lato
  Raspberry in `software/rcj2027/`; il firmware Arduino del protocollo e' da scrivere.
- `docs/rules/` contiene i PDF di riferimento 2026 copiati come materiale di studio.

## Escluso intenzionalmente

- mondi e ambienti di simulazione;
- controller e referee;
- log di run simulate;
- codice Python/C++/Arduino del progetto precedente;
- documentazione storica che descriveva il percorso simulato;
- copie locali del file CAD o di immagini non verificate.

## Codice nuovo

Il firmware in `firmware/` e il software in `software/` sono scritti ex novo in questo
repository. Non derivano dal progetto precedente e non contengono log o mondi di simulazione.

## Progetto precedente

Il repository `robocup` resta intatto e separato. Non è una directory padre di questo progetto
e non viene modificato durante lo sviluppo.
