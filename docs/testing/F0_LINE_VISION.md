# Test F0-1 - primo pipeline di visione della linea

**ID:** F0-1
**Data:** 2026-11-01
**Firmware:** nessun comando ai motori; firmware sicuro o di banco non usato
**Software:** `software/rcj2027/line_vision.py`, `software/rcj2027/diagnostics.py`
**Hardware:** Raspberry Pi 5 Model B + telecamera CSI IMX708
**Condizioni:** robot fermo, movimento disabilitato, immagini acquisite con la CSI a
1280x720 full-fov; linea nera su piano bianco che termina sul bordo del tavolo.

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
   larghezza (dispari) e `C=10`; se i pixel sotto 140 non superano il 45% della ROI, vengono
   aggiunti per riempire una linea larga o scura; apertura 3x3 e chiusura 5x5.
5. **Scanline**: 60 righe dall'alto verso il basso; per ogni riga si scelgono i run neri di
   larghezza plausibile, si uniscono le run separate da pochi pixel e si segue quella piu'
   vicina alla posizione precedente. La larghezza deve restare entro il 50% di quella attesa;
   dopo il 6% di righe senza linea la scansione si ferma. La discesa dall'alto evita di
   agganciare il bordo del tavolo o il pavimento sotto la linea.
6. **Fit robusto**: parabola `x(y)` con due passate di rimozione degli outlier. La copertura
   e' calcolata sul tratto effettivamente rilevato, non sull'intera ROI; offset e heading sono
   valutati sull'ultima riga valida e sul 25% superiore del tratto, senza extrapolare oltre la
   linea. Il residuo RMS e la regolarita' della larghezza entrano nella confidenza.
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
- linea larga vicino alla camera e linea che termina sul bordo di un tavolo;
- fondo uniforme e fondo scuro senza linea;
- rumore, debug, annotazione e risoluzione sbagliata;
- conferma, perdita e ripresa del tracker;
- validazione dell'undistort su viste checkerboard sintetiche;
- comando `line` con report JSON.

I frame sintetici verificano il codice, non sostituiscono la prova su una linea reale.
La suite completa e' a **176 test**, tutti verdi.

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

### Linea reale F0-1

**Acquisizione:** 30 frame in `software/calib/linea-f0-001/`, CSI a 1280x720 full-fov,
autofocus con warm-up 2 s. Linea nera su un piano bianco, che termina sul bordo del tavolo;
sotto il bordo si vede il pavimento in legno. Robot fermo, nessun comando motore.

**Primo tentativo:** 0/30 frame trovati. Il rilevatore partiva dal basso, agganciava il bordo
del tavolo o il pavimento e otteneva residui di 5,5-45 px. Il caso ha esposto tre problemi:
scansione dal lato sbagliato, nessun limite dopo un tratto senza linea e nessun controllo di
continuita' della larghezza.

**Correzioni:** scansione dall'alto, stop dopo il 6% di righe senza linea, larghezza entro il
50% di quella attesa, soglia scura a 140 e copertura calcolata sul tratto rilevato.

**Secondo tentativo:** report `software/logs/f0-linea-001/report.json`, exit code `0`.

| Voce | Valore |
|---|---:|
| Frame con linea | 30/30 |
| Found ratio | 1,00 |
| Frame confermati dal tracker | 28/30 (i primi 2 non ancora) |
| Perdite | 0 |
| Offset | da -46,04 a -45,87 px (mediana -45,98) |
| Heading | da 3,88 a 4,01 deg (mediana 3,95) |
| Confidenza | da 0,9455 a 0,9542 (mediana 0,9511) |
| Residuo fit | da 0,297 a 0,369 px (mediana 0,321) |
| Larghezza linea | 139-140 px |
| Righe valide | 37/60 (la linea finisce sul bordo del tavolo) |
| Tempo per frame | mediana 38,4 ms (34,0-45,0) |

La linea e' stabile e viene rilevata per tutta la sequenza; l'offset e' circa 46 px a sinistra
dell'asse ottico della calibrazione (`cx=653,8`) e l'heading e' circa 4 gradi a destra. Sono
misure in pixel, non una prova di inseguimento: il robot non si e' mosso e il controller non
e' collegato.

### Frame senza linea

Un frame reale della scrivania, senza linea, e' stato analizzato con la calibrazione CSI:
`found=false`, `confidence=0.0`, `residual_px=67,4`, `reason=low_confidence`. Il rilevatore
ha seguito una venatura del legno ma l'ha rifiutata. E' un solo frame negativo: non e' una
prova di robustezza.

### Prestazioni

Sulla sequenza reale F0-1 (30 frame 1280x720, mappe di undistort gia' calcolate):

| Pipeline | Mediana | Min | Max |
|---|---:|---:|---:|
| Con undistort, 30 frame reali | 38,4 ms | 34,0 ms | 45,0 ms |
| Senza undistort, 10 ripetizioni | 27,9 ms | 25,5 ms | 30,3 ms |

Il tempo comprende lettura del frame in memoria, undistort, soglia, scanline e fit. Non
comprende l'acquisizione dalla telecamera. In una run precedente il primo frame ha misurato
73,2 ms per la costruzione delle mappe. Il valore e' sufficiente per un primo test a bassa
velocita', non e' ancora un requisito di controllo.

## Limiti

- Prova positiva solo su una linea retta, con robot fermo e una sola illuminazione.
- Offset e heading sono in pixel; non c'e' ancora la trasformazione al piano del pavimento.
- L'offset e' riferito all'asse ottico della calibrazione (`cx=653,8`), non al centro
  meccanico del robot: l'allineamento camera-telaio resta da misurare.
- Non sono gestiti incroci, gap ampi, linea argentata, marker o linee multiple.
- Il pipeline analizza sequenze salvate; il loop live con la CSI e il controller sono il
  passo successivo.
- Le soglie della confidenza vanno tarate su linee reali con illuminazione e superfici
  diverse.
- Il gate F0 resta aperto: servono curvature, gap, disturbi e movimento.

## Prossima prova

1. Ripetere la sequenza con linea spostata a destra/sinistra, inclinata e curva.
2. Provare un'ombra sulla linea e una superficie con venature o riflessi.
3. Registrare found ratio, offset, heading, confidenza e tempo per ogni condizione.
4. Solo dopo collegare il controller ai motori, con ruote sollevate e gate di sicurezza.
5. Chiudere F0 quando tutte le condizioni hanno una prova ripetibile e un report.
