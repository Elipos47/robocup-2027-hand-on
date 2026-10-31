# Protocollo seriale Raspberry Pi ↔ Arduino — v1.1

**Stato:** specifica approvata per l'implementazione. Il firmware di test motori e' separato dal
protocollo; il firmware del protocollo non e' ancora stato scritto. Nessun cablaggio e' stato
modificato per il protocollo.

## Obiettivi

La mappa dei pin e il tipo di collegamento sono in `docs/hardware/MINIMUM_HARDWARE_DATA.md`;
questo documento definisce solo il formato dei messaggi e non autorizza alcun cablaggio.

- Trasferire comandi motori e servo dal Raspberry Pi all'Arduino.
- Restituire sensori e stato dell'Arduino al Raspberry.
- Rendersi leggibile nel log e facile da testare senza hardware.
- Impedire comandi invalidi e arrestare il robot se il Raspberry smette di parlare.
- Permettere test con un trasportatore finto.

## Parametri

- Seriale: 115200 baud, 8 bit dati, nessuna parita', 1 bit di stop.
- Encodifica: ASCII.
- Separatore messaggi: newline `\n`.
- Versione del protocollo: `1` (questa specifica e' la revisione 1.1).
- Checksum: XOR di tutti i byte del payload, due cifre esadecimali maiuscole.
- Sequenza: intero senza segno `0..65535`, riparte da zero dopo il massimo.
- Duty motori: interi con segno, range `-255..255`.
- Servo: angolo in gradi, range di default `0..180`; il range meccanico effettivo e' configurato
  a parte.
- Framing: `<payload>*<HH>\n`, massimo 96 byte compresi checksum e newline.
- Status: bitmask a 16 bit.
- I comandi legacy `M1`, `M2` e `S?` non fanno parte di questa versione.

## Formato del frame

```text
<payload>*<HH>\n
```

- `payload`: testo ASCII senza `*` e senza newline.
- `HH`: XOR di tutti i byte ASCII del payload, scritto con due cifre esadecimali maiuscole.
- Esempio:

```text
payload: D,17,90,-90
XOR:     43
frame:   D,17,90,-90*43\n
```

Un frame con checksum errato viene scartato e produce `E,BAD_CHECKSUM`. Un frame oltre 96 byte
produce `E,LINE_TOO_LONG`. In nessun caso un frame invalido deve muovere i motori.

## Messaggi Raspberry Pi → Arduino

### `V,1*4B\n`

Handshake e richiesta della versione del firmware. Non ha numero di sequenza.

Risposta prevista:

```text
V,1,ARDUINO_MEGA,1*61\n
```

Campi della risposta: versione protocollo, scheda, versione firmware.

### `H,<sequence>*HH\n`

Heartbeat. L'Arduino lo usa per capire che il Raspberry e' ancora vivo. Non produce ack: serve
solo ad aggiornare il timestamp dell'ultimo contatto.

```text
H,18*6D\n
```

### `D,<sequence>,<left>,<right>*HH\n`

Comando dei due motori.

```text
D,17,90,-90*43\n
```

L'Arduino deve:

1. validare il checksum e la struttura;
2. validare che `left` e `right` siano interi nel range `-255..255`;
3. applicare i limiti di sicurezza e il gate di movimento;
4. aggiornare il timestamp dell'ultimo contatto;
5. rispondere `K,<sequence>` se il comando e' accettato, oppure `E,<code>`.

Se il movimento e' disabilitato, non applica il comando e risponde `E,MOTION_DISABLED`.

### `X,<sequence>*HH\n`

Stop immediato e cancellazione della modalita' movimento. Ha priorita' su qualsiasi altro
comando in coda.

```text
X,19*7C\n
```

Risposta: `K,19`.

### `Z,<sequence>,<angle>*HH\n`

Comando servo, in gradi. Il range di default e' `0..180`; il range meccanico effettivo e'
definito nella configurazione e verificato a banco. Non inviare `Z` finche' il meccanismo non e'
stato verificato.

```text
Z,20,90*51\n
```

Risposta: `K,20` oppure `E,SERVO_UNVERIFIED`.

## Messaggi Arduino → Raspberry

### `K,<sequence>*HH\n`

Ack di un comando accettato (`D`, `X`, `Z`). Non viene inviato per `H` e `V`.

```text
K,17*61\n
```

### `A,<sequence>,<distance_mm>,<yaw_mdeg>,<pitch_mdeg>,<roll_mdeg>,<status>*HH\n`

Stato periodico dei sensori.

- `sequence`: numero del campione;
- `distance_mm`: distanza HC-SR04, `-1` se non valida;
- `yaw_mdeg`, `pitch_mdeg`, `roll_mdeg`: valori IMU in milligradi;
- `status`: bitmask a 16 bit, non testo libero.

Esempio:

```text
A,18,145,-1200,35,0,3*53\n
```

Status `3` significa bit 0 e bit 1 attivi: sonar valido e IMU valida.

### Bitmask di `status`

| Bit | Nome | Significato |
|---:|---|---|
| 0 | `SONAR_VALID` | la distanza HC-SR04 e' valida |
| 1 | `IMU_VALID` | i valori IMU sono validi |
| 2 | `MOTORS_ACTIVE` | i motori sono alimentati |
| 3 | `WATCHDOG_TRIPPED` | il watchdog e' scattato |
| 4 | `ESTOP_ACTIVE` | stop di emergenza attivo |
| 5 | `SERVO_READY` | servo verificato e abilitato |
| 6..15 | riservati | devono essere `0` |

### `E,<code>*HH\n`

Errore. Il codice e' una tabella fissa; il testo libero resta solo nei log del Raspberry.

| Codice | Significato |
|---|---|
| `UNKNOWN_COMMAND` | tipo di messaggio non riconosciuto |
| `BAD_FORMAT` | numero di campi o interi non validi |
| `BAD_RANGE` | valore fuori range |
| `BAD_CHECKSUM` | checksum errato |
| `LINE_TOO_LONG` | frame oltre 96 byte |
| `WATCHDOG_STOP` | heartbeat scaduto, motori fermati |
| `MOTION_DISABLED` | gate di sicurezza chiuso |
| `SERVO_UNVERIFIED` | servo non ancora verificato o abilitato |

```text
E,BAD_RANGE*2E\n
```

## Sicurezza

- Ogni comando `D`, `X`, `Z` ha un numero di sequenza; `H` lo ha per il log, `V` no.
- Un valore fuori range non deve essere eseguito: l'Arduino resta fermo e invia `E,BAD_RANGE`.
- Un checksum errato non deve essere eseguito: l'Arduino resta fermo e invia `E,BAD_CHECKSUM`.
- Se non arrivano heartbeat per il timeout configurato, l'Arduino ferma entrambi i motori e
  segnala `WATCHDOG_STOP`.
- `X` deve fermare i motori anche se un comando di movimento e' in coda.
- Il Raspberry considera non valida qualsiasi risposta con struttura o checksum sbagliati.
- Il log riporta ogni cambio di stato e ogni stop di sicurezza.
- La soglia del watchdog non viene scelta qui: e' un parametro misurato e documentato prima
  dell'uso sul robot. Finche' non e' configurata, il movimento resta disabilitato.
- Il gate di movimento richiede batteria, mappa lati, polarita', `pwm_max` e timeout watchdog.

## Test previsti

1. handshake, versione e checksum;
2. comando avanti/indietro e ack;
3. comando con valore fuori range;
4. checksum errato;
5. frame troncato, rumoroso o troppo lungo;
6. stop immediato con comando in coda;
7. heartbeat;
8. watchdog e perdita del cavo;
9. risposta sensori valida e bitmask;
10. stesso test con trasportatore finto e con Arduino reale.

## Stato dell'implementazione

- La specifica v1.1 e' documentata.
- Il package Python `software/rcj2027/` contiene parser, trasporto finto, logger, gate di
  sicurezza e test host.
- Il firmware Arduino del protocollo non e' ancora stato scritto: e' il passo successivo.
- Lo sketch di banco `firmware/test/motor_direction_test/` resta separato dal protocollo.
