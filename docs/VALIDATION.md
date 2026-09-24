# Validazione iniziale del progetto

**Data:** 24/09/2026

## Controllo

```sh
bash scripts/check_context.sh
```

Il controllo verifica la presenza di hardware, regole, obiettivi, architettura, protocollo,
piano test, registro misure e provenienza. Rifiuta la presenza delle directory legacy `src/` e
`simulation/` e di file applicativi Python/C++/Arduino nella baseline documentale.

## Criterio

La baseline e' pronta per la raccolta delle misure hardware quando il controllo termina con
`context validation: OK`. Non implica che hardware, firmware o software siano gia' verificati.
