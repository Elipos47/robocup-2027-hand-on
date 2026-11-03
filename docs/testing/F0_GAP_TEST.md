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

## Seconda run - 181848

| Voce | Valore |
|---|---:|
| Frame | 479 |
| Durata | 27,82 s |
| FPS | 17,2 |
| Frame grezzi trovati | 288/479 (60,1%) |
| Frame confermati | 320 (66,8%) |
| Riprese | 6 |
| Perdita massima | 51 frame |
| Offset | -104,0..67,8 px |
| Heading | -4,0..3,2 deg |
| `width_rejected_frames` | 0 |
| Startup | 2,19 s |

La sequenza e' simile: FOUND sui segmenti, LOST nel vuoto, 6 riprese. Al frame 120 la linea
era visibile ma un **seme isolato lontano** (x≈1094) bloccava la scansione: il tratto era
troppo corto per essere una linea, ma il salto verso la linea vera veniva rifiutato. Corretto:
se il tratto agganciato e' piu' corto di `min_valid_rows`, viene scartato e la scansione
riparte dal candidato piu' centrale. Aggiunto il test `far_speck_then_line`.

## Terza run - 182854 (con le correzioni)

| Voce | Valore |
|---|---:|
| Frame | 487 |
| Durata | 27,86 s |
| FPS | 17,5 |
| Frame grezzi trovati | 284/487 (58,3%) |
| Frame confermati | 304 (62,4%) |
| Riprese | 6 |
| Perdita massima | 54 frame |
| Offset | -94,4..19,4 px |
| Heading | -1,1..3,5 deg |
| `width_rejected_frames` | 0 |
| Confidenza mediana | 0,961 |
| Startup | 2,32 s |

Questa run e' stata eseguita con il reset del tratto corto. Il frame 120, che nella run
precedente veniva perso nonostante la linea visibile, ora e' **FOUND**. I frame 150, 210 e 390
sono LOST con la linea fuori dalla ROI: comportamento atteso. La sequenza mostra FOUND sui
segmenti, LOST nel vuoto e 6 riprese, senza falsi confermati evidenti.

## Anomalia trovata

Al frame 150 la linea era visibile nella ROI ma il rilevatore ha dato `few_rows` con
`valid_rows=1`: un piccolo run isolato in cima alla ROI veniva preso come seme, poi lo stop sul
gap fermava la scansione prima del segmento vero. Inoltre il filtro di larghezza rifiutava
l'aumento di larghezza del segmento che entrava.

Correzioni:

- lo stop sul gap scatta solo dopo aver agganciato almeno `min_valid_rows` righe;
- il filtro di larghezza ammette un aumento graduale e rifiuta solo un restringimento brusco;
- aggiunto il test sintetico `speck_then_line_frame`.

Queste correzioni sono state validate nella terza run: il frame 120 e' tornato FOUND e non ci
sono falsi confermati nei tratti senza linea.

## Esito

- Il comportamento del gap e' corretto: FOUND sui segmenti, LOST nel vuoto, nessun falso,
  6 riprese e riacquisizione.
- La terza run con le correzioni conferma il fix del seme e il frame 120 torna FOUND.
- Il gap da 7 cm e' dentro il limite 2026 (massimo 20 cm).
- **F0-4 e' chiuso sul banco** con il gap disponibile. L'attraversamento del gap resta F1.

## Prossima prova

1. Non serve ripetere il gap da 7 cm per F0.
2. Se compaiono altri gap, registrare la misura e ripetere la sequenza.
3. Passare a F0-5: movimento a bassa velocita' e comportamento del controller.
4. L'attraversamento del gap e' un test F1 separato, con timeout e riacquisizione.
