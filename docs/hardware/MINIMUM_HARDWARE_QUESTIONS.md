# Questionario hardware minimo

**Scopo:** raccogliere il minimo necessario per scrivere il software e per distinguere i dati che
possono restare `TODO` da quelli che devono bloccare il movimento reale.

Il contratto tecnico associato e' `docs/hardware/MINIMUM_HARDWARE_DATA.md`. Le dimensioni delle
schede gia presenti in `docs/hardware/Misure Robotica.pdf` non sono richieste in questo
questionario: servono al CAD, non al controller.

## Come rispondere

- Rispondi solo alle domande del Blocco A-C.
- Se un dato non e' stato misurato, scrivi `TODO` oppure `non misurato`: non e' un errore.
- Se un collegamento non e' ancora stato scelto, scrivi `da scegliere`.
- Per ogni valore dimensionale indica sempre l'unita' in millimetri.
- Non e' necessario rispondere alle domande del Blocco D per iniziare lo scaffolding del software.
- Un dato di sicurezza lasciato `TODO` verra' trattato dal software come movimento disabilitato,
  non come valore da indovinare.

## Blocco A - movimento e sicurezza

### Q1. Batteria

Qual e' la tensione nominale della batteria?

```text
tensione_nominale_v = 11.1    # 2 pacchi Li-Ion 3S in parallelo, 2026-10-22
```

Risposta: due pacchi Li-Ion da 11.1 V 2.6 Ah 28.86 Wh in parallelo. In parallelo la tensione
resta 11.1 V; capacita' ed energia raddoppiano (5.2 Ah, 57.72 Wh). Restano da confermare:

```text
corrente_scarica_continua_a =
corrente_scarica_picco_a =
bms_per_pacco =            # si/no, modello
tensione_fine_scarica_v =
tensione_carica_completa_v =
connettore_e_fusibile =
```

### Q2. Identificazione dei motori

Quale motore e' il sinistro e quale e' il destro? Se non esistono etichette, basta una sigla
temporanea (`M1`, `M2`).

```text
motore_sinistro =
motore_destro =
```

### Q3. Verso del motore sinistro

Quando il software comanda "avanti", il motore sinistro deve girare:

- avanti;
- indietro;
- non ancora verificato.

```text
verso_sinistro =
```

### Q4. Verso del motore destro

Quando il software comanda "avanti", il motore destro deve girare:

- avanti;
- indietro;
- non ancora verificato.

```text
verso_destro =
```

### Q5. Limite PWM

Qual e' il duty massimo considerato sicuro per i motori?

```text
pwm_massimo_sicuro = 0-255 / TODO
```

Se non e' ancora noto, lascialo `TODO`: non viene usato alcun fallback automatico.

### Q6. Arresto e freno

All'arresto, il driver deve:

- frenare;
- lasciar scorrere (`coast`);
- altro da descrivere;
- non ancora verificato.

```text
comportamento_stop =
```

### Q7. Ruota

Qual e' il diametro effettivo della ruota di locomozione?

```text
diametro_ruota_mm =
```

Se non e' disponibile, possiamo iniziare con una versione a PWM grezzo, senza dichiarare la
velocita' lineare.

### Q8. Riferimento velocita' (opzionale)

Se e' disponibile, indicare RPM o velocita' lineare misurati a un PWM noto:

```text
riferimento_velocita =
pwm_usato =
```

Questa risposta non blocca la prima versione del software.

## Blocco B - comunicazione e pin

### Q9. Collegamento Arduino-Pi

Come sono collegati Raspberry Pi e Arduino?

- USB;
- UART diretta;
- USB-serial converter;
- altro da descrivere;
- non ancora deciso.

```text
collegamento_arduino_pi =
```

### Q10. Mappa dei pin

I pin sono gia' cablati?

- si', inviare la mappa usata;
- no, proporre una mappa e attendere approvazione;
- parzialmente cablati, descrivere cosa e' collegato.

```text
pin_ena_left =
pin_enb_right =
pin_in1_left =
pin_in2_left =
pin_in3_right =
pin_in4_right =
pin_servo =
pin_sonar_trig =
pin_sonar_echo =
pin_imu_sda =
pin_imu_scl =
pin_led =
pin_interruttore =
```

La mappa non e' una misura: puo' essere proposta dall'agente, ma non si modifica il cablaggio senza
approvazione esplicita.

## Blocco C - percezione minima

### Q11. Camera linea

Per la camera che segue la linea (quella verde), indicare:

- altezza della lente dal suolo;
- inclinazione avanti/indietro in gradi;
- eventuale offset longitudinale, se noto.

```text
camera_linea_altezza_mm =
camera_linea_inclinazione_deg =
camera_linea_offset_avanti_mm = opzionale
```

### Q12. IMU

Il BNO085 verra' usato nella prima versione?

- si';
- no;
- non ancora deciso.

Se si', indicare quale asse e' rivolto verso la parte anteriore del robot:

```text
imu_asse_avanti =
imu_orientamento_note =
```

### Q13. Sensore di distanza

HC-SR04 verra' usato nella prima versione?

- si';
- no;
- non ancora deciso.

Se si', indicare altezza e inclinazione approssimative:

```text
sonar_altezza_mm =
sonar_inclinazione_deg =
```

## Blocco D - non serve rispondere ora

Non bloccano la scrittura del primo software:

- massa dei componenti e baricentro;
- ingombri delle telecamere, del servo, dei motori e dello schermo;
- lunghezza dei cavi;
- capacita' e durata della batteria;
- larghezza ruote, cinghie e pulegge;
- taratura dettagliata di HC-SR04 e BNO085;
- campo visivo e calibrazione finale delle telecamere;
- limiti di corrente e termici esaustivi del driver;
- ruolo definitivo del servo, dello schermo e delle luci.

Questi dati sono utili per CAD, sicurezza, tuning e prove sul campo, ma vengono raccolti in una
fase successiva.

## Risposta rapida

Se preferisci, copia e completa solo questo blocco:

```text
tensione_nominale_v =
motore_sinistro =
motore_destro =
verso_sinistro =
verso_destro =
pwm_massimo_sicuro =
comportamento_stop =
diametro_ruota_mm =
riferimento_velocita =
collegamento_arduino_pi =
pin_ena_left =
pin_enb_right =
pin_in1_left =
pin_in2_left =
pin_in3_right =
pin_in4_right =
pin_servo =
pin_sonar_trig =
pin_sonar_echo =
pin_imu_sda =
pin_imu_scl =
pin_led =
pin_interruttore =
camera_linea_altezza_mm =
camera_linea_inclinazione_deg =
imu_asse_avanti =
sonar_altezza_mm =
sonar_inclinazione_deg =
```
