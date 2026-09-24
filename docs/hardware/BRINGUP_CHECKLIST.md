# Checklist di bring-up hardware

Usare in ordine, con alimentazione controllata e un operatore che possa fermare il robot.

- [ ] Fotografare il montaggio completo e i connettori.
- [ ] Verificare batterie, tensione, polarità e protezioni.
- [ ] Verificare massa, stabilita' e centro di massa.
- [ ] Collegare Raspberry e Arduino con alimentazione e messa a terra definite.
- [ ] Testare comunicazione senza motori collegati.
- [ ] Verificare heartbeat, stop e watchdog.
- [ ] Collegare un motore alla volta con ruote sollevate.
- [ ] Verificare verso, freno e limite PWM.
- [ ] Collegare IMU, sonar e servo solo dopo il safety test.
- [ ] Eseguire il primo test sul campo con batteria annotata.
- [ ] Registrare ogni esito nel `MEASUREMENT_LOG.md` e nel report della run.
