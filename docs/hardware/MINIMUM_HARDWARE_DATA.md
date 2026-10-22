# Dati hardware minimi per il software

**Scopo:** definire il minimo insieme di dati hardware necessario per scrivere il software
senza pretendere un inventario completo di tutto l'hardware.

**Regola:** un dato non confermato resta `TODO`. Non si inseriscono valori inventati nella
configurazione. I parametri che proteggono i motori devono essere confermati prima di abilitare
il movimento reale.

**Questionario operativo:** `docs/hardware/MINIMUM_HARDWARE_QUESTIONS.md`.

## Principio di lavoro

- Si può scrivere subito il protocollo, il logger e la struttura del software anche se alcuni
  parametri sono ancora `TODO`.
- Un parametro non critico può rimanere configurabile e non blocca lo scaffolding del software.
- Un parametro di sicurezza mancante deve disabilitare i comandi dei motori, non produrre un
  valore di fallback.
- La mappa dei pin è una scelta progettuale, non una misura: può essere proposta dall'agente e
  deve essere confermata prima di modificare cablaggi.
- Le quote riportate nel PDF delle misure servono al CAD e al posizionamento fisico; non sono
  automaticamente parametri del controller.

## Priorita 1 - contratto minimo

### M1 - movimento e sicurezza

| Campo | Valore | Uso | Stato |
|---|---|---|---|
| `battery_nominal_v` | `11.1` | scala tensione e limite motori | confermato da etichetta 2026-10-22 (2 pacchi in parallelo); da misurare a vuoto |
| `motor_side_map` | `TODO` | distingue sinistro e destro | obbligatorio per muovere |
| `motor_direction_polarity` | `TODO` | inverte avanti/indietro | obbligatorio per muovere |
| `pwm_max` | `TODO` | limita il duty dei motori | obbligatorio per muovere |
| `stop_brake_behavior` | `TODO` | definisce freno, coast e stop | obbligatorio per muovere |
| `wheel_effective_diameter_mm` | `TODO` | cinematica e velocita lineare | obbligatorio per muovere |
| `rpm_reference` | `TODO` | converte PWM in velocita | opzionale per il primo raw-PWM |

Se `rpm_reference` non e disponibile, si puo scrivere una prima versione a PWM grezzo con
calibrazione successiva, senza dichiarare la velocita nota.

### Alimentazione - dato acquisito (2026-10-22)

Due pacchi **Li-Ion 3S in parallelo**, dato dichiarato sull'etichetta:

| Grandezza | Singolo pacco | Due in parallelo |
|---|---:|---:|
| Tensione nominale | 11.1 V | **11.1 V** (invariata) |
| Capacita' | 2.6 Ah | **5.2 Ah** |
| Energia | 28.86 Wh | **57.72 Wh** |

In parallelo la tensione non si somma: si sommano capacita' ed energia (e la corrente
disponibile, se i due pacchi hanno protezioni compatibili). 11.1 V corrisponde a 3 celle Li-Ion
in serie (3 x 3.7 V).

Per il **software** serve solo la tensione nominale: scala i limiti dei motori e permette di
leggere la batteria. Il resto non e' un requisito del contratto:

- la corrente di scarica la limita il BMS del pacco; se il robot si spegne sotto sforzo si
  misura allora, non prima;
- la soglia di batteria scarica si sceglie con una misura di tensione sotto carico, quando il
  robot cammina;
- connettore e fusibile sono scelte di cablaggio, non parametri del controller.

11.1 V e' il valore dichiarato sull'etichetta: la misura a vuoto serve solo a confermare che i
pacchi sono carichi, non a sbloccare il software.

### M2 - comunicazione

| Campo | Valore | Uso | Stato |
|---|---|---|---|
| `arduino_pi_link` | `TODO` | distingue USB, UART o altro | obbligatorio per la comunicazione |
| `serial_device` | `TODO` | percorso stabile del dispositivo | configurabile |
| `serial_baud` | `115200` proposta | parametro iniziale del protocollo | da verificare sul collegamento |

Il percorso della porta puo essere risolto a runtime; non e una misura che blocca la scrittura
del software.

### M3 - percezione minima

| Campo | Valore | Uso | Stato |
|---|---|---|---|
| `line_camera_height_mm` | `TODO` | scala della camera linea | obbligatorio per la geometria di linea |
| `line_camera_tilt_deg` | `TODO` | correzione prospettica | obbligatorio per la geometria di linea |
| `line_camera_offset_forward_mm` | `TODO` | posizione della camera sul robot | opzionale per il primo F0 |
| `imu_axis_mapping` | `TODO` | orientamento del BNO085 | obbligatorio se usato |
| `sonar_mount` | `TODO` | altezza e angolo HC-SR04 | obbligatorio se usato nel primo test |

La camera verde e gia identificata come camera linea e quella nera come camera vittime.

## Priorita 2 - dati differiti

Questi dati non sono richiesti per iniziare a scrivere il software:

- ingombri dettagliati di ogni scheda, fori e connettori;
- massa dei singoli componenti, massa totale e baricentro;
- lunghezza e percorso dei cavi;
- capacita e durata della batteria;
- larghezza di ruote, cinghie e rapporto di trasmissione completo;
- rumore e accuratezza dettagliata di HC-SR04 e BNO085;
- campo visivo delle telecamere e calibrazione finale;
- corsa, corrente e limiti del servo;
- misure termiche e cadute di tensione esaustive del driver.

Questi dati restano utili per B0, per il CAD e per le prove sul campo, ma non devono bloccare
la creazione del contratto software.

## Mappa dei pin

La mappa dei pin viene trattata come una decisione progettuale separata. Deve includere:

- `ENA`, `ENB`, `IN1..IN4` per L298N, se confermati;
- pin del segnale servo;
- pin trigger ed echo di HC-SR04, se usato;
- pin I2C o altra interfaccia del BNO085, se usato;
- pin di led e interruttore, se usati;
- eventuali pin di debug o heartbeat.

Nessun cablaggio va modificato prima dell'approvazione esplicita della mappa.

## Dimensioni gia documentate nel PDF

Le seguenti dimensioni sono presenti in `docs/hardware/Misure Robotica.pdf` e possono essere
usate per il disegno 3D. Non sono ancora parametri del controller e la loro data, strumento e
incertezza vanno completati nel registro misure quando confermati.

| Componente | Dimensione riportata | Note |
|---|---:|---|
| Batterie | `55 x 67 x 46 mm` | numero di batterie da confermare |
| Arduino Mega 2560 | `53 x 108 x 15 mm`, M3 | ordine da uniformare come larghezza x lunghezza x altezza |
| Raspberry Pi 5 | `57 x 90 x 20 mm`, M3 | ordine da uniformare come larghezza x lunghezza x altezza |
| UPS | `71 x 90 x 35 mm`, M3 | ordine da uniformare come larghezza x lunghezza x altezza |
| HC-SR04 | `6 + 20 x 45 x 15 mm`, M1 | chiarire il significato del prefisso `6` |
| BNO085 | `23 x 25 x 12 mm`, M2 | modello e ruolo da confermare |
| L298N | `43,4 x 43,4 x 28 mm`, M3 | chiarire `28` rispetto alle quote della figura |
| Step-down | `21 x 43 x 13 mm`, M3 | alimentazione e output da verificare |

## Modello di raccolta

L'utente puo completare questo blocco con i soli dati disponibili:

```text
battery_nominal_v = 11.1
motor_side_map =
motor_direction_polarity =
pwm_max =
stop_brake_behavior =
wheel_effective_diameter_mm =
rpm_reference =
arduino_pi_link =
line_camera_height_mm =
line_camera_tilt_deg =
imu_axis_mapping =
sonar_mount =
```

Il software deve poter essere generato anche con campi `TODO`, mantenendo il movimento reale
disabilitato finche i campi di sicurezza obbligatori non sono confermati.
