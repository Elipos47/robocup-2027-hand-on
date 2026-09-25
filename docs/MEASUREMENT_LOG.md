# Registro misure hardware

**Regola:** compilare solo misure realmente eseguite. Un valore non misurato resta `TODO`.

Il registro e' diviso in due priorità per evitare di chiedere un inventario completo prima di
poter scrivere il software. I parametri di sicurezza mancanti devono impedire il movimento
reale, non essere sostituiti con valori inventati.

## Priorita 1 - dati minimi per il software

| Data | Componente | Misura | Valore | Strumento | Condizione | Incertezza | Esito/TODO |
|---|---|---|---:|---|---|---|---|
| TBD | Batterie | tensione nominale | TODO | TODO | TODO | TODO | obbligatorio per muovere |
| TBD | Motori | asse sinistro/destro | TODO | TODO | TODO | TODO | obbligatorio per muovere |
| TBD | Motori | verso avanti/indietro | TODO | TODO | TODO | TODO | obbligatorio per muovere |
| TBD | L298N | PWM massimo sicuro | TODO | TODO | TODO | TODO | obbligatorio per muovere |
| TBD | L298N/motori | comportamento freno e stop | TODO | TODO | TODO | TODO | obbligatorio per muovere |
| TBD | Ruota | diametro effettivo | TODO | TODO | TODO | TODO | obbligatorio per muovere |
| TBD | Motori | RPM o velocita a un PWM noto | TODO | TODO | TODO | TODO | opzionale per il primo raw-PWM |
| TBD | Comunicazione | tipo di collegamento Arduino-Pi | TODO | TODO | TODO | TODO | obbligatorio per comunicare |
| TBD | Camera linea | altezza e inclinazione | TODO | TODO | TODO | TODO | obbligatorio per la geometria di linea |
| TBD | BNO085 | orientamento degli assi | TODO | TODO | TODO | TODO | obbligatorio se usato |
| TBD | HC-SR04 | altezza e inclinazione del montaggio | TODO | TODO | TODO | TODO | obbligatorio se usato nel primo test |

La mappa dei pin non e' una misura: e' una scelta progettuale da proporre e approvare prima di
modificare i cablaggi. I dettagli sono in `docs/hardware/MINIMUM_HARDWARE_DATA.md`; le domande
operative sono in `docs/hardware/MINIMUM_HARDWARE_QUESTIONS.md`.

## Priorita 2 - misure successive

| Data | Componente | Misura | Valore | Strumento | Condizione | Incertezza | Esito/TODO |
|---|---|---|---:|---|---|---|---|
| TBD | Batterie | tensione a vuoto/carico e capacita | TODO | TODO | TODO | TODO | differita |
| TBD | Motori | RPM a vuoto e sotto carico | TODO | TODO | TODO | TODO | differita |
| TBD | Ruote/cinghie | larghezza, rapporto e attrito | TODO | TODO | TODO | TODO | differita |
| TBD | Robot | massa totale e baricentro | TODO | TODO | TODO | TODO | differita |
| TBD | HC-SR04 | range, errore e rumore | TODO | TODO | TODO | TODO | differita |
| TBD | BNO085 | calibrazione e deriva | TODO | TODO | TODO | TODO | differita |
| TBD | Telecamere | posizione completa e calibrazione ottica | TODO | TODO | TODO | TODO | differita |
| TBD | L298N | dropout e riscaldamento | TODO | TODO | TODO | TODO | differita |
| TBD | Servo | modello, corsa e limiti | TODO | TODO | TODO | TODO | differita |
| TBD | Cablaggi | connettori, fusibili e cadute di tensione | TODO | TODO | TODO | TODO | differita |

## Dimensioni gia raccolte

Le quote degli ingombri di Arduino, Raspberry Pi, UPS, HC-SR04, BNO085, L298N, step-down e
batterie sono raccolte in `docs/hardware/Misure Robotica.pdf`. Vanno trasferite in questo
registro solo dopo averne confermato data, strumento, condizione e incertezza; non sono dati
sufficienti per autorizzare il movimento.
