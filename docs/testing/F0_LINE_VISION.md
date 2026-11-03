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

Loop live dalla CSI, senza comandi ai motori:

```sh
python3 -m rcj2027.diagnostics line-live --camera-num 0 \
  --size 1280x720 --warmup 2 --duration 10 \
  --annotated-dir logs/f0-live/annotated --save-every 15 \
  --json-out logs/f0-live/report.json
```

Vista live durante la raccolta:

```sh
# finestra locale sul display del Raspberry
python3 -m rcj2027.diagnostics line-live --preview --duration 15

# stream browser per telefono/PC sulla stessa rete
python3 -m rcj2027.diagnostics line-live --http-port 8080 --duration 15
# aprire http://<ip-del-raspberry>:8080/

# durata illimitata fino a q/ESC, con maschera di segmentazione
python3 -m rcj2027.diagnostics line-live --preview --debug-overlay --duration 0
```

Da Thonny si apre `software/line_live.py`, si modifica `CONDITION` e si preme Run. Lo script
usa `DURATION_S = 0` (fino a `q`/`ESC`), salva log, report e frame annotati in
`software/logs/f0-<condizione>/` e puo' attivare la maschera con `DEBUG_OVERLAY = True`.

La finestra live mostra sempre ROI, punti di scansione, fit, asse ottico e barra dell'offset.
`--debug-overlay` aggiunge la maschera di segmentazione in verde trasparente: possono comparire
anche bordo tavolo o pavimento, che il filtro di larghezza e lo stop sul gap scartano; la linea
scelta e' il fit blu con i punti verdi.

Lo stream MJPEG mostra il frame annotato (linea, offset, heading, confidenza). E' pensato per
la rete locale: non ha autenticazione e non va esposto su Internet. La pagina ha un pulsante
**Ferma acquisizione** che chiude la run e salva il report; nella finestra locale si usa
`q`/`ESC`.

Il live usa sempre il sensore intero 2304x1296 (full-fov), come la calibrazione. Salva il log
JSONL in `logs/<run-id>.jsonl` e stampa un riepilogo alla fine.

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
- comando `line`, `line-undistort` e parser `line-live`;
- server MJPEG: indice HTML, aggiornamento frame e validazione parametri.

I frame sintetici verificano il codice, non sostituiscono la prova su una linea reale.
La suite completa e' a **187 test**, tutti verdi.

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

### Loop live F0-2

La stessa linea e' stata elaborata in tempo reale dalla CSI con `line-live`, senza salvare i
frame prima dell'analisi. La calibrazione e' applicata a ogni frame e il log JSONL contiene
offset, heading, confidenza e stato del tracker.

| Voce | Valore |
|---|---:|
| Durata | 5,04 s |
| Frame elaborati | 100 |
| FPS | 19,8 |
| Frame con linea | 100/100 |
| Frame confermati | 98/100 (i primi 2 non ancora) |
| Perdite | 0 |
| Offset | mediana -46,52 px (-47,61..-46,41) |
| Heading | mediana 4,14 deg (4,06..4,66) |
| Confidenza | mediana 0,955 (0,919..0,962) |
| Tempo di elaborazione | mediana 39,9 ms (35,7..56,7) |
| Frame annotati salvati | 7 |

Report locale: `software/logs/f0-live-001/report.json`; log JSONL:
`software/logs/f0-live-001/f0-live-001.jsonl`.

Il loop live e' quindi utilizzabile per prove a bassa velocita'. Il limite di 19,8 FPS e' il
risultato di acquisizione (circa 30 FPS) piu' elaborazione (circa 40 ms); non e' ancora un
requisito del controller.

La vista live e' stata verificata in entrambe le modalita': finestra locale sul display del
Raspberry (`--preview`, 18 frame in 1 s) e stream MJPEG via browser (`--http-port`, indice HTML
e flusso JPEG valido). Verificata anche la combinazione `--preview --debug-overlay --http-port`
con 26 frame in 2 s. Lo stream non ha autenticazione: va usato solo sulla rete locale.

Il report `line-live` ora include `startup.camera_start_s`, `startup.warmup_s` e
`startup.first_frame_s`. Due run strumentate danno primo frame a 2,08-2,19 s; un ritardo molto
maggiore va annotato e investigato.

### Curva F0-2

Il primo tentativo su curva reale e' in `docs/testing/F0_CURVE_TEST.md`: nei tratti in cui la
linea entra nella ROI viene seguita con confidenza 0,86-0,965, con 6 riprese e nessun falso
confermato evidente nei tratti vuoti. La telecamera e' volutamente vicina alla tile, quindi la
curva puo' uscire dalla ROI. **F0-2 e' coperto sul banco** con il nastro disponibile, che e'
piu' largo di 1-2 cm; resta una prova di compatibilita' con la linea regolamentare quando sara'
disponibile. Il raggio fisico non e' un parametro del test.

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

- Prova positiva su retta e su curva di banco con nastro proxy piu' largo di 1-2 cm.
  La compatibilita' con la linea regolamentare resta da provare.
- Offset e heading sono in pixel; non c'e' ancora la trasformazione al piano del pavimento.
- L'offset e' riferito all'asse ottico della calibrazione (`cx=653,8`), non al centro
  meccanico del robot: l'allineamento camera-telaio resta da misurare.
- Non sono gestiti incroci, gap ampi, linea argentata, marker o linee multiple.
- Il controller non e' collegato: il live misura la linea ma non comanda i motori.
- Le soglie della confidenza vanno tarate su linee reali con illuminazione e superfici
  diverse.
- Il gate F0 resta aperto: servono gap, disturbi, movimento e compatibilita' con la linea
  1-2 cm.

## Protocollo F0-2 / F0-3 / F0-4

I criteri seguenti sono provvisori: vanno confermati con l'operatore prima di dichiarare
chiuso il gate. Ogni run usa `software/line_live.py` con `DURATION_S = 0` e viene fermata con
`q`/`ESC` o con il pulsante nel browser.

### F0-2 curva

- **Setup:** nastro disponibile (anche piu' largo di 1-2 cm, da annotare come proxy); un arco e
  una S se possibile. La telecamera e' vicina alla tile: la ROI e' una finestra di near-field e
  la curva puo' uscire. Non serve misurare il raggio.
- **Run:** `CONDITION = "curva"`, prima 10 s con robot fermo in tre posizioni, poi 15-20 s
  spostando il robot o la linea a mano.
- **Misure:** found ratio nei tratti in cui la linea e' nella ROI, heading (curvatura in spazio
  immagine), perdite e riprese, falsi confermati quando la linea e' fuori.
- **Criterio provvisorio:** nei tratti in ROI la linea deve essere trovata senza perdite; quando
  esce deve passare a `lost` senza falsi confermati; ripresa entro 5 frame quando rientra. Il
  raggio fisico e l'intera curva in ROI non sono richiesti.

### F0-3 ombra

- **Parziale:** un'ombra con bordo netto che copre circa 1/3 e poi 2/3 della larghezza della
  linea, lasciando la linea visibile. Non basta scurire genericamente la scena: serve un'ombra
  che tolga contrasto a una parte della linea.
- **Totale:** un oggetto opaco o un'ombra che rende la linea non distinguibile dal fondo. Se la
  linea resta visibile, e' una prova di illuminazione, non di occlusione.
- **Run:** `CONDITION = "ombra-parziale"` e `"ombra-totale"`.
- **Misure:** copertura dell'ombra, found ratio, confidenza, falsi positivi, frame di perdita e
  ripresa.
- **Criterio provvisorio:** parziale >= 0,95; totale → `lost` entro 5 frame, zero falsi
  confermati, ripresa entro 5 frame.

Il dettaglio delle run e' in `docs/testing/F0_SHADOW_TEST.md`. Il report live distingue
`found` (grezzo), `tracked_found` (larghezza compatibile) e `confirmed_frames`; per
l'occlusione conta `confirmed_ratio`, non `passed`. Il tracker rifiuta un restringimento brusco
della larghezza, tipico di un bordo agganciato al posto della linea.

### F0-4 gap

- **Setup:** gap disponibili, misurati con righello (es. 7 cm); la regola 2026 ammette fino a
  20 cm. Non servono tutte le misure 5/10/20 se il gap disponibile e' uno solo.
- **Run:** `CONDITION = "gap-<cm>"`; prima fermo davanti/al gap/dopo, poi passaggio a mano.
- **Misure:** found ratio prima/dopo, frame di perdita, falsi positivi dentro il gap, ripresa.
- **Criterio provvisorio:** nessun falso confermato nel gap; `lost` entro 5 frame; ripresa
  entro 5 frame dopo la linea. L'attraversamento del gap e' F1, non F0.

Il tentativo con gap da 7 cm e' in `docs/testing/F0_GAP_TEST.md`: comportamento qualitativo
corretto (FOUND sui segmenti, LOST nel vuoto, 6 riprese), con un'anomalia di aggancio al
frame 150 corretta nel frattempo. Serve una nuova run live per chiudere F0-4.

Per ogni run vanno registrati data, condizione, misura geometrica, illuminazione e posizione
della telecamera. Se la telecamera viene spostata, la calibrazione `csi_1280x720.json` va
rifatta.

## Prossima prova

1. Eseguire `line-live` mentre l'operatore sposta la linea o il robot a mano lungo il tracciato.
2. Passare a ombra e gap; la curva e' coperta sul banco con il nastro proxy.
3. Registrare found ratio, offset, heading, confidenza, FPS e tempo per ogni condizione.
4. Ripetere la curva con la linea 1-2 cm quando disponibile, senza misurarne il raggio.
5. Solo dopo collegare il controller ai motori, con ruote sollevate e gate di sicurezza.
6. Chiudere F0 quando tutte le condizioni hanno una prova ripetibile e un report.
