# Calibrazione manuale

Non esiste auto-calibrazione in runtime. Ogni camera e ogni sensore viene calibrato con una
procedura manuale, una condizione di luce registrata e un log salvato.

La calibrazione completa viene dopo il contratto minimo del software. Per iniziare servono solo
i parametri indicati in `docs/hardware/MINIMUM_HARDWARE_DATA.md`; le tarature dettagliate restano
differite.

## Camera linea

1. Fissare la camera nella posizione definitiva.
2. Registrare altezza, inclinazione, focale e distanza dal suolo.
3. Catturare una superficie bianca e una linea nera con luce nota.
4. Salvare i range HSV/ROI e la procedura usata.
5. Ripetere con luce debole, luce forte e ombre.

## Camera vittime

- fotografare la posizione della camera;
- misurare distanza e angolo di visione della stanza;
- definire una procedura di calibrazione solo dopo aver verificato il montaggio;
- non usare un modello o una soglia importati senza dati reali.

## IMU e sonar

- annotare orientamento del modulo e assi;
- misurare rumore a robot fermo;
- verificare la scala e l'orientamento degli assi;
- ripetere la misura dopo il montaggio definitivo.

## Regole

- salvare data, condizione, valori e modifiche hardware;
- non dichiarare una calibrazione valida se i test sul campo peggiorano;
- non inserire immagini o dati sensibili non necessari nel repository.
