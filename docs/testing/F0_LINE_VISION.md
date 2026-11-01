# Test F0-1 - primo pipeline di visione della linea

**ID:** F0-1
**Data:** 2026-11-01
**Firmware:** nessun comando ai motori; firmware sicuro o di banco non usato
**Software:** `software/rcj2027/line_vision.py`, `software/rcj2027/diagnostics.py`
**Hardware:** Raspberry Pi 5 Model B + telecamera CSI IMX708
**Condizioni:** robot fermo, movimento disabilitato, immagini acquisite con la CSI a
1280x720 full-fov.

## Obiettivo

Aprire il gate F0 con un primo pipeline ripetibile che, da un frame della telecamera linea:

- applichi la calibrazione intrinseca e l'undistort;
- isoli la linea nera nella regione davanti al robot;
- misuri offset e direzione con una convenzione esplicita;
- rifiuti i frame senza una linea credibile;
- produca un report e frame annotati per l'operatore.

Il pipeline non comanda i motori e non usa coordinate di percorso. Non e' ancora un
controller di inseguimento: e' la misura che il controller usera' in F0.

## Convenzioni

- `offset_px` positivo: la linea in basso e' a destra dell'asse ottico.
- `heading_deg` positivo: la linea, guardando avanti, piega a destra.
- I valori sono in pixel immagine. La conversione in millimetri richiede l'altezza e
  l'inclinazione della telecamera, non ancora misurate.
- `found=false` significa che il frame non supera i controlli di continuita', fit o
  confidenza. I campi numerici restano nel report per diagnostica ma non vanno usati come
  misura valida.

## Pipeline

1. **Undistort**: mappe calcolate da `csi_1280x720.json` con la stessa matrice intrinseca
   come nuova matrice. La calibrazione e' legata alla risoluzione: un frame di dimensione
   diversa viene rifiutato.
2. **ROI**: dal 55% al 98% dell'altezza, dal 2% al 98% della larghezza.
3. **Pretrattamento**: grayscale, CLAHE, blur gaussiano 5x5.
4. **Soglia**: adaptive threshold inversa con blocco automatico circa il 12% della
   larghezza (dispari) e `C=10`; se i pixel sotto 80 non superano il 25% della ROI, vengono
   aggiunti per riempire una linea molto larga vicino alla camera; apertura 3x3 e chiusura 5x5.
5. **Scanline**: 60 righe dal basso verso l'alto; per ogni riga si scelgono i run neri di
   larghezza plausibile, si uniscono le run separate da pochi pixel e si segue quella piu'
   vicina alla posizione precedente.
6. **Fit robusto**: parabola `x(y)` con due passate di rimozione degli outlier; il residuo
   RMS e la regolarita' della larghezza entrano nella confidenza.
7. **Tracker**: conferma dopo 3 frame consecutivi con linea, perdita dello stato confermato
   dopo 5 frame senza linea, conteggio delle riprese.

## Comandi

Verifica dell'undistort sulle immagini checkerboard gia' acquisite:

```sh
cd software
python3 -m rcj2027.diagnostics line-undistort \
  --images "calib/csi/*.jpg" \
  --json-out logs/f0-undistort.json \
  --save-dir /tmp/f0-undistort
```

Acquisizione di una sequenza reale con la CSI (la numerazione dei nodi non si usa):

```sh
cd software
python3 -m rcj2027.diagnostics camera-capture --csi --camera-num 0 \
  --size 1280x720 --full-fov --warmup 2 \
  --count 30 --interval 0.3 --output-dir calib/linea-f0-001
```

Analisi della sequenza, con frame annotati e maschere:

```sh
python3 -m rcj2027.diagnostics line \
  --images "calib/linea-f0-001/*.jpg" \
  --annotated-dir logs/f0-linea-001/annotated \
  --mask-dir logs/f0-linea-001/mask \
  --json-out logs/f0-linea-001/report.json
```

Per un confronto senza calibrazione:

```sh
python3 -m rcj2027.diagnostics line \
  --images "calib/linea-f0-001/*.jpg" --no-undistort \
  --json-out logs/f0-linea-001/report-raw.json
```

Exit code: `0` se la frazione di frame con linea e' almeno `--min-found-ratio` (default
0.8), `1` se sotto soglia, `2` per errore di configurazione o immagine. La soglia e' un
criterio software provvisorio, non una misura di campo.

## Test host

I test host coprono:

- caricamento e validazione della calibrazione;
- linea centrata, a destra, a sinistra, inclinata e curva su frame sintetici;
- fondo uniforme e fondo scuro senza linea;
- rumore, debug, annotazione e risoluzione sbagliata;
- conferma, perdita e ripresa del tracker;
- validazione dell'undistort su viste checkerboard sintetiche;
- comando `line` con report JSON.

I frame sintetici verificano il codice, non sostituiscono la prova su una linea reale.
La suite completa e' a **175 test**, tutti verdi.

## Risultato disponibile

### Undistort

`line-undistort` sulle 15 immagini CSI in `calib/csi/`:

| Voce | Valore |
|---|---:|
| Immagini con checkerboard | 14/15 |
| Errore omografia grezzo | 0,4392 px |
| Errore omografia dopo undistort | 0,4287 px |
| Miglioramento | 2,39% |
| Spostamento medio dei corner | 0,717 px |
| Spostamento massimo di un corner | 3,622 px |
| Esito | PASS tecnico |

Il PASS significa che la mappa non peggiora il modello e resta sotto 1 px di errore medio.
Le immagini sono le stesse usate per la calibrazione e il checkerboard copre solo il 16,3%
del frame: la verifica non dimostra la bonta' dell'undistort ai bordi ne' su una linea reale.

### Frame senza linea

Un frame reale della scrivania, senza linea, e' stato analizzato con la calibrazione CSI:
`found=false`, `confidence=0.0`, `residual_px=7,7`, `reason=low_confidence`. Il rilevatore
ha seguito una venatura del legno ma l'ha rifiutata. E' un solo frame negativo: non e' una
prova di robustezza.

### Prestazioni

Su 10 ripetizioni dello stesso frame reale 1280x720, con mappe di undistort gia' calcolate:

| Pipeline | Mediana | Min | Max |
|---|---:|---:|---:|
| Con undistort | 37,6 ms | 36,0 ms | 44,6 ms |
| Senza undistort | 27,9 ms | 25,5 ms | 30,3 ms |

Il tempo comprende lettura del frame in memoria, undistort, soglia, scanline e fit. Non
comprende l'acquisizione dalla telecamera. Il valore e' sufficiente per un primo test a
bassa velocita', non e' ancora un requisito di controllo.

## Limiti

- Nessuna prova positiva su una linea reale: il gate F0 resta aperto.
- Offset e heading sono in pixel; non c'e' ancora la trasformazione al piano del pavimento.
- Non sono gestiti incroci, gap, linea argentata, marker o linee multiple.
- Il pipeline analizza sequenze salvate; il loop live con la CSI e il controller sono il
  passo successivo.
- Le soglie della confidenza vanno tarate su linee reali con illuminazione e superfici
  diverse.

## Prossima prova

1. Posare una linea nera reale (nastro o linea di prova) davanti alla CSI, con il robot
   fermo e i motori disabilitati.
2. Acquisire 30 frame a 1280x720 full-fov con `camera-capture`.
3. Eseguire `line` e conservare report, frame annotati e maschere.
4. Ripetere con linea centrata, spostata a destra/sinistra, inclinata e con un'ombra.
5. Registrare found ratio, offset, heading, confidenza e tempo; solo dopo questa prova si
   puo' dichiarare F0-1 chiuso.
