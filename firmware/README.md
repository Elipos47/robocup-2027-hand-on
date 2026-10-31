# Firmware Arduino

Codice C++/Arduino per Arduino Mega 2560.

## Layout

- `firmware/test/<nome>/<nome>.ino`: sketch di banco, ognuno con il suo `README.md`.
- `firmware/rcj2027/`: firmware applicativo del protocollo seriale.

## Dipendenze

- `arduino-cli core install arduino:avr`
- `arduino-cli lib install "Adafruit BNO08x"` (con dipendenze BusIO e Unified Sensor)

## Regole

- Compilare con `bash scripts/build.sh` prima di ogni upload.
- Ogni sketch di test ha un README con cablaggio, comandi e risultato atteso.
- Upload e prove di movimento con ruote sollevate e alimentazione controllata.
- Nessun codice del progetto precedente viene importato.

## Sketch presenti

- `test/motor_direction_test/`: verifica lato e verso dei due motori con L298N.
- `test/i2c_scan/`: scanner del bus I2C (SDA 20, SCL 21), usato per il BNO085.
- `rcj2027/`: firmware del protocollo seriale v1.1 (movimento disabilitato di default).
