# Firmware Arduino

Codice C++/Arduino per Arduino Mega 2560.

## Layout

- `firmware/test/<nome>/<nome>.ino`: sketch di banco, ognuno con il suo `README.md`.
- Gli sketch applicativi futuri staranno in `firmware/`; per ora esiste solo il codice di test.

## Regole

- Compilare con `bash scripts/build.sh` prima di ogni upload.
- Ogni sketch di test ha un README con cablaggio, comandi e risultato atteso.
- Upload e prove di movimento con ruote sollevate e alimentazione controllata.
- Nessun codice del progetto precedente viene importato.

## Sketch presenti

- `test/motor_direction_test/`: verifica lato e verso dei due motori con L298N.
