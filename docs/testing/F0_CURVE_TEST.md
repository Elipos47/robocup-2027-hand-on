# Test F0-2 - curva reale

**ID:** F0-2 (tentativo 1)
**Data:** 2026-11-03
**Software:** `software/rcj2027/line_vision.py`, `line-live`, script `software/line_live.py`
**Hardware:** Raspberry Pi 5 + CSI IMX708, 1280x720 full-fov
**Condizioni:** curva nera su piano bianco, bordo del tavolo visibile, robot spostato a mano;
movimento disabilitato.

## Setup

La curva e' un nastro nero largo, ripreso da vicino. Il raggio non e' stato misurato in questa
run: resta un `TODO` per la prossima prova. La telecamera non e' stata spostata durante la
sequenza.

## Acquisizione

| Voce | Valore |
|---|---:|
| Run | `f0-curva-20261103T171259` |
| Frame | 1584 |
| Durata | 89,29 s |
| FPS | 17,7 |
| Frame con linea | 899 (56,8%) |
| Perdite/riprese | 6 riprese |
| Perdita massima | 317 frame |

La percentuale complessiva non descrive il rilevamento: la run contiene **317 frame iniziali
senza linea** (17,1 s, prima del posizionamento), **223 frame di perdita centrale** (circa 12,6 s,
riposizionamento) e altri tratti in cui la curva esce dalla ROI. Escludendo i frame iniziali e
la perdita centrale: 899/1044 = **86,1%**.

## Tratti utili

Tratti continui con almeno 20 frame trovati:

| Frame | Frame | Offset mediano | Heading mediano | Confidenza | Larghezza |
|---:|---:|---:|---:|---:|---:|
| 324-427 | 104 | -43,2 px | 8,6 deg | 0,92 | 188 px |
| 558-650 | 93 | -331,8 px | 9,1 deg | 0,88 | 176 px |
| 656-701 | 46 | -6,6 px | -10,6 deg | 0,89 | 174 px |
| 710-805 | 96 | 29,1 px | 4,0 deg | 0,93 | 180 px |
| 809-867 | 59 | 62,1 px | 20,6 deg | 0,91 | 189 px |
| 873-903 | 31 | -23,9 px | 20,2 deg | 0,86 | 179 px |
| 1192-1234 | 43 | -31,2 px | 2,7 deg | 0,93 | 184 px |
| 1236-1399 | 164 | -58,9 px | 4,4 deg | 0,965 | - |
| 1400-1583 | 184 | -73,9 px | 11,8 deg | 0,439 | 183 px |

I frame annotati mostrano il fit blu che segue correttamente l'arco, anche quando la linea e'
spostata a sinistra o a destra nella ROI. Quando la linea esce dalla ROI, il tracker passa a
`LOST` e non viene forzato: e' il comportamento atteso.

## Avvio

Nella run il primo evento `line` e' arrivato **18,73 s** dopo `session_start`; il primo frame
con linea **35,84 s** dopo l'avvio. Il ritardo iniziale non e' normale: dopo l'aggiunta della
strumentazione, una run di prova ha misurato:

| Fase | Tempo |
|---|---:|
| `camera_start_s` | 0,06-0,17 s |
| `warmup_s` | 2,06-2,19 s |
| `first_frame_s` | 2,08-2,19 s |

Il valore di 18,7 s della prima run e' quindi un'anomalia di inizializzazione (camera/AF o stato
precedente), non il comportamento atteso. I nuovi report includono `camera_start_s`,
`warmup_s` e `first_frame_s` per distinguere avvio, warm-up e posizionamento.

I 317 frame iniziali a vuoto non sono un errore del rilevatore: la linea non era nell'inquadratura.
Per le prossime run conviene iniziare a registrare solo quando la linea e' dentro la ROI.

## Esito

- Il rilevamento della curva e' corretto nei tratti in cui la linea e' nella ROI.
- La run **non chiude F0-2**: non e' continua, il raggio non e' misurato e la linea esce piu'
  volte dall'inquadratura.
- Non ci sono falsi confermati evidenti nei tratti senza linea.

## Prossima run

1. Posizionare la curva in modo che resti dentro la ROI arancione per tutta la durata.
2. Misurare il raggio con un metro e annotarlo.
3. Registrare 10 s fermo in tre posizioni, poi 15-20 s muovendo a mano senza far uscire la linea.
4. Se la linea esce, fermare la run e riposizionare: non continuare fuori ROI.
5. Ripetere con `CONDITION = "curva"` e conservare il nuovo report.
