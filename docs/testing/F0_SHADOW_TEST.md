# Test F0-3 - ombra parziale e totale

**ID:** F0-3 (tentativi 1 e 2)
**Data:** 2026-11-03
**Software:** `line_vision.py`, `line-live`, `line_live.py`
**Hardware:** Raspberry Pi 5 + CSI IMX708, 1280x720 full-fov

## Ombra parziale - run 174441

| Voce | Valore |
|---|---:|
| Frame | 608 |
| Durata | 35,29 s |
| FPS | 17,2 |
| Frame trovati | 608/608 |
| Confermati | 606 |
| Perdite | 0 |
| Offset | -114,7..186,0 px |
| Heading | -3,3..6,8 deg |
| Confidenza | 0,663-0,978 (mediana 0,974) |
| Startup | 5,6 s |

L'ombra non e' chiaramente visibile nei frame annotati: era probabilmente leggera. Il test
dimostra che la linea resta trovata, ma non e' una prova severa. Una seconda run breve
(`175015`, 41 frame) ha dato 41/41 trovati con confidenza 0,967-0,969.

## Ombra totale - run 175031

| Voce | Valore |
|---|---:|
| Frame | 900 |
| Durata | 54,92 s |
| FPS | 16,4 |
| Frame grezzi trovati | 765 (85%) |
| Confermati (tracker precedente) | 794 |
| Perdite/riprese | 5 riprese; perdita massima 31 frame |
| Startup | 2,18 s |

La scena e' stata scurita e la linea era ancora visibile a tratti: e' un test di **bassa
luce**, non una vera occlusione. Il dato importante e' un falso aggancio: nella fase buia il
rilevatore ha seguito un **bordo sottile** della linea, con larghezza 10-31 px contro 188-190 px
della linea intera, e offset circa +48 px invece di -46 px. La confidenza era 0,4-0,6, quindi
il tracker lo confermava.

### Correzione: continuita' di larghezza

`LineTracker` ora rifiuta un **restringimento brusco** della larghezza rispetto alla linea
confermata. Un aumento graduale e' ammesso (la linea entra nel campo o si avvicina).

Replay della stessa run con il nuovo tracker:

| Voce | Valore |
|---|---:|
| Frame grezzi trovati | 765 |
| Frame accettati per larghezza | 433 |
| Frame rifiutati per larghezza | 332 |
| Frame confermati | 426 |
| `control_passed` | false (426/900 = 47,3%) |

Nella fase 450-650 il falso bordo non viene piu' confermato. Quando la linea intera ritorna,
il tracker la riaccetta. La correzione e' verificata sui dati registrati, ma serve una nuova
run live per confermarla sul robot.

## Report live

Il riepilogo `line-live` ora contiene:

- `found` / `found_ratio`: frame grezzi con linea;
- `tracked_found` / `tracked_found_ratio`: frame accettati dal tracker;
- `width_rejected_frames`: trovati ma scartati per larghezza incompatibile;
- `confirmed_frames` / `confirmed_ratio`: frame confermati;
- `passed`: solo il criterio grezzo `found_ratio`;
- `control_passed`: criterio di controllo basato sui frame confermati.

Per un test di occlusione non usare `passed`: conta `confirmed_ratio`, `width_rejected_frames`
e la sequenza perdita/ripresa.

## Esito

- **Parziale:** PASS tecnico, ma con ombra leggera; da ripetere con ombra netta su 1/3-2/3.
- **Totale/bassa luce:** NON chiuso. Il falso bordo e' stato identificato e il tracker ora lo
  rifiuta in replay; serve una nuova run live.
- **Occlusione vera:** ancora da provare con un oggetto opaco che copra la linea.
