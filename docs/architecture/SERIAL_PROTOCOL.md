# Protocollo seriale Raspberry Pi ↔ Arduino — proposta v1

**Stato:** proposta tecnica; nessun firmware o cablaggio è stato modificato.

## Obiettivi

- Trasferire comandi motori e servo dal Raspberry Pi all'Arduino.
- Restituire sensori e stato dell'Arduino al Raspberry.
- Rendersi leggibile nel log e facile da testare senza hardware.
- Impedire comandi invalidi e arrestare il robot se il Raspberry smette di parlare.
- Permettere una simulazione con un trasportatore finto.

## Parametri

- Seriale: 115200 baud, 8 bit dati, nessuna parità, 1 bit di stop.
- Encodifica: ASCII.
- Separatore messaggi: newline `\n`.
- Versione iniziale: `1`.
- I valori dei motori sono duty interi con segno, range `-255..255`.
- Il protocollo non sostituisce ancora i comandi legacy `M1`, `M2` e `S?`: la migrazione avverrà solo dopo il test su banco.

## Messaggi Raspberry Pi → Arduino

### `V,1\n`

Handshake e richiesta della versione del firmware.

Risposta prevista:

```text
V,1,ARDUINO_MEGA,1\n
```

### `H,<sequence>\n`

Heartbeat. L'Arduino lo usa per capire che il Raspberry è ancora vivo.

Il numero di sequenza torna a zero dopo il valore massimo del tipo scelto.

### `D,<sequence>,<left>,<right>\n`

Comando dei due motori.

Esempio:

```text
D,17,90,-90\n
```

L'Arduino deve:

1. validare che `left` e `right` siano interi nel range `-255..255`;
2. applicare i limiti di sicurezza;
3. aggiornare il timestamp dell'ultimo heartbeat/comando;
4. rispondere con un ack o aggiornare il contatore di errori.

### `X,<sequence>\n`

Stop immediato e cancellazione della modalità movimento. Deve avere priorità su qualsiasi altro comando.

### `Z,<angle>\n`

Comando servo, in gradi, con range definito nella configurazione meccanica. Non inviare `Z` finché il meccanismo non è stato verificato a banco.

## Messaggi Arduino → Raspberry

### `A,<sequence>,<distance_mm>,<yaw_mdeg>,<pitch_mdeg>,<roll_mdeg>,<status>\n`

Stato periodico dei sensori.

- `sequence`: numero del campione;
- `distance_mm`: distanza HC-SR04, `-1` se non valida;
- `yaw_mdeg`, `pitch_mdeg`, `roll_mdeg`: valori IMU in milligradi per evitare troppi decimali;
- `status`: bitmask o codice documentato, non testo libero.

Esempio:

```text
A,18,145,-1200,35,0,OK\n
```

### `E,<code>\n`

Errore. Il codice sarà una tabella fissa, per esempio:

- `E,UNKNOWN_COMMAND`;
- `E,BAD_RANGE`;
- `E,BAD_CHECKSUM`;
- `E,WATCHDOG_STOP`.

Il testo dell'errore può essere aggiunto solo nei log del Raspberry, non nel protocollo motore.

## Sicurezza

- Ogni comando motori deve avere un numero di sequenza.
- Un valore fuori range non deve essere eseguito: l'Arduino deve fermarsi e inviare `E,BAD_RANGE`.
- Se non arrivano heartbeat per il timeout configurato, l'Arduino ferma entrambi i motori.
- `X` deve fermare i motori anche se un comando di movimento è in coda.
- Il Raspberry deve considerare non valida qualsiasi risposta con struttura sbagliata.
- Il log deve riportare ogni cambio di stato e ogni stop di sicurezza.
- La soglia del watchdog non viene scelta qui: sarà un parametro misurato e documentato prima dell'uso sul robot.

## Test previsti

1. handshake e versione;
2. comando avanti/indietro;
3. comando invalido;
4. stop immediato;
5. heartbeat;
6. watchdog;
7. risposta sensori valida;
8. risposta troncata o rumorosa;
9. perdita del cavo;
10. stesso test con Arduino finto e con Arduino reale.

## Stato dell'implementazione

- La specifica è ora documentata.
- Il parser e il backend finto saranno implementati dopo l'approvazione di questo formato.
- Il firmware Arduino reale non viene modificato prima della verifica del protocollo con l'utente.
