# I2C scan di banco

**Scopo:** verificare quali indirizzi I2C rispondono sul bus del Mega (SDA 20, SCL 21).
Non muove motori e non modifica il cablaggio.

## Cablaggio

| Segnale | Pin Mega 2560 |
|---|---:|
| SDA | 20 |
| SCL | 21 |
| VCC | 5 V |
| GND | GND |

Il breakout BNO085 e' atteso a `0x4A` o `0x4B`.

## Comandi

```sh
arduino-cli compile --fqbn arduino:avr:mega firmware/test/i2c_scan
arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:avr:mega firmware/test/i2c_scan
python3 - <<'PY'
import serial, time
with serial.Serial('/dev/ttyACM0', 115200, timeout=0.2) as port:
    time.sleep(1)
    print(port.read(4096).decode('ascii', errors='replace'))
PY
```

Lo scanner stampa `I2C_FOUND 0x..` ogni due secondi. Se non compare `0x4A`/`0x4B`, il BNO085
non risponde: verificare alimentazione e collegamento SDA/SCL prima di modificare il firmware.

## Risultato atteso

```text
I2C_SCAN_BEGIN
I2C_FOUND 0x4A
I2C_FOUND_COUNT 1
I2C_SCAN_END
```

Il risultato reale va annotato nella prova di banco; nessun motore viene comandato.
