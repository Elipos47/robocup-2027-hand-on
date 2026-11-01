# Calibrazioni telecamere

Questi JSON contengono le matrici intrinseche e i coefficienti di distorsione
prodotti da `python3 -m rcj2027.diagnostics camera-calibrate`.

## File

- `usb_640x480.json` - camera USB 5MP, stanza/vittime/palline, risoluzione 640x480, 2026-11-01.
  - 15 immagini, pattern 9x6, lato reale 23.75 mm.
  - RMS 0.523 px, copertura media 22.7% (min 20.0%, max 31.3%).
  - Focale ~248 px, centro ottico ~(298, 240).
  - Calibrazione accettata, ma migliorabile con un target piu' grande nel frame.
- `csi_1280x720.json` - camera CSI IMX708, linea, risoluzione 1280x720, 2026-11-01.
  - 14 immagini valide su 15, pattern 9x6, lato reale 23.75 mm.
  - RMS 0.542 px, copertura media 16.3% (min 12.6%, max 24.4%).
  - Pose diverse: spread centri 423 px, rapporto dimensioni 1.93.
  - Focale ~960 px, centro ottico ~(654, 373).
  - Modalita' di acquisizione: `--csi --size 1280x720 --full-fov` (sensore intero 2304x1296).
  - Accettata come prima calibrazione della linea; verificare l'undistort in F0.

La calibrazione e' legata alla camera, alla risoluzione, al modo sensore e al montaggio. Se la
camera viene spostata, la risoluzione cambia o si passa dal crop al full-fov, va rifatta. Le
immagini sorgente non sono versionate: restano in `software/calib/` e sono ignorate da git.
