# Calibrazioni telecamere

Questi JSON contengono le matrici intrinseche e i coefficienti di distorsione
prodotti da `python3 -m rcj2027.diagnostics camera-calibrate`.

## File

- `usb_640x480.json` - camera USB 5MP, risoluzione 640x480, 2026-11-01.
  - 15 immagini, pattern 9x6, lato reale 23.75 mm.
  - RMS 0.523 px, copertura media 22.7% (min 20.0%, max 31.3%).
  - Focale ~248 px, centro ottico ~(298, 240).
  - Calibrazione accettata, ma migliorabile con un target piu' grande nel frame.

La calibrazione e' legata alla camera, alla risoluzione e al montaggio. Se la camera
viene spostata o la risoluzione cambia, va rifatta. Le immagini sorgente non sono
versionate: restano in `software/calib/` e sono ignorate da git.
