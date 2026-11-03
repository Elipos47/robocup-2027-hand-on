# Test F0-4 - gap reale da 7 cm

**ID:** F0-4 (tentativo 1)
**Data:** 2026-11-03
**Software:** `line_vision.py`, `line-live`, `line_live.py`
**Hardware:** Raspberry Pi 5 + CSI IMX708, 1280x720 full-fov

## Setup

Gap disponibile: **7 cm**, unico nastro a disposizione. La linea e' nera su piano bianco, con
due segmenti separati dal vuoto. La telecamera e' vicina alla tile: la ROI e' una finestra di
near-field e il gap puo' occuparla tutta.

## Acquisizione

| Voce | Valore |
|---|---:|
| Run | `f0-gap-7-20261103T180449` |
| Frame | 513 |
| Durata | 28,47 s |
| FPS | 18,0 |
| Frame grezzi trovati | 251/513 (48,9%) |
| Frame accettati per larghezza | 251 |
| Frame rifiutati per larghezza | 0 |
| Frame confermati | 266 (51,8%) |
| Riprese | 6 |
| Perdita massima | 57 frame |
| Offset | -176,6..71,4 px |
| Heading | -2,5..0,95 deg |
| Confidenza massima | 0,976 |
| Startup | 2,19 s |

La bassa percentuale globale e' attesa: il gap occupa la ROI e la linea non c'e'. Per un test
di gap contano la sequenza perdita/ripresa e l'assenza di falsi, non `found_ratio`.

## Sequenza

| Frame | Esito | Note |
|---:|---|---|
| 0-66 | FOUND | segmento prima del gap |
| 67-123 | LOST | gap in ROI |
| 124-149 | FOUND | riacquisizione |
| 150-193 | LOST | gap/linea fuori ROI |
| 194-211 | FOUND | riacquisizione |
| 212-267 | LOST | gap |
| 268-287 | FOUND | riacquisizione |
| 288-334 | LOST | gap |
| 337-364 | FOUND | riacquisizione |
| 365-391 | LOST | gap |
| 392-404 | FOUND | riacquisizione |
| 405-434 | LOST | gap |
| 435-512 | FOUND | segmento finale stabile |

Nei tratti FOUND offset, heading e larghezza sono stabili; non ci sono falsi confermati
evidenti nei tratti LOST. Le 6 riprese mostrano che il tracker riacquisisce la linea dopo il
gap.

## Anomalia trovata

Al frame 150 la linea era visibile nella ROI ma il rilevatore ha dato `few_rows` con
`valid_rows=1`: un piccolo run isolato in cima alla ROI veniva preso come seme, poi lo stop sul
gap fermava la scansione prima del segmento vero. Inoltre il filtro di larghezza rifiutava
l'aumento di larghezza del segmento che entrava.

Correzioni:

- lo stop sul gap scatta solo dopo aver agganciato almeno `min_valid_rows` righe;
- il filtro di larghezza ammette un aumento graduale e rifiuta solo un restringimento brusco;
- aggiunto il test sintetico `speck_then_line_frame`.

Queste correzioni non sono ancora state provate in una nuova run live sul gap.

## Esito

- Il comportamento qualitativo del gap e' corretto: FOUND sui segmenti, LOST nel vuoto, nessun
  falso, ripresa dopo.
- La run non chiude F0-4 per l'anomalia di frame 150 e perche' la nuova correzione va validata
  live.
- Il gap da 7 cm e' dentro il limite 2026 (massimo 20 cm); non servono altre misure se non
  disponibili.

## Prossima run

1. Ripetere con lo stesso gap da 7 cm e il codice aggiornato.
2. Registrare un passaggio pulito: linea prima del gap, gap in ROI, linea dopo.
3. Verificare che non ci siano FOUND dentro il vuoto e che la ripresa avvenga quando il
   segmento rientra.
4. Conservare il report e gli annotati.
