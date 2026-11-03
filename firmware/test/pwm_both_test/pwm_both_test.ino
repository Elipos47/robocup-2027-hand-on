/*
  Robocup2027HandOn - test di banco: entrambi i canali a PWM 255
  Arduino Mega 2560 + L298N

  RUOTE SOLLEVATE. Il test parte automaticamente 3 s dopo il reset e non
  richiede comandi seriali.

  Sequenza:
    - entrambi i motori avanti a 255 per 4 s;
    - stop 2 s;
    - entrambi i motori indietro a 255 per 4 s;
    - stop 2 s;
    - ripete per REPEATS cicli e termina con stop.

  Mappa:
    ENA = 12   IN1 = 22   IN2 = 23   (canale A = ruota destra)
    ENB = 13   IN3 = 24   IN4 = 25   (canale B = ruota sinistra)

  La polarita' e' quella verificata a banco: IN1/IN2 basso/alto = avanti per A,
  IN3/IN4 basso/alto = avanti per B.
*/

const uint8_t PIN_ENA = 12;
const uint8_t PIN_ENB = 13;
const uint8_t PIN_IN1 = 22;
const uint8_t PIN_IN2 = 23;
const uint8_t PIN_IN3 = 24;
const uint8_t PIN_IN4 = 25;

const uint8_t TEST_PWM = 255;
const unsigned long HOLD_MS = 4000;
const unsigned long PAUSE_MS = 2000;
const uint8_t REPEATS = 2;

void stopMotors() {
  analogWrite(PIN_ENA, 0);
  analogWrite(PIN_ENB, 0);
  digitalWrite(PIN_IN1, LOW);
  digitalWrite(PIN_IN2, LOW);
  digitalWrite(PIN_IN3, LOW);
  digitalWrite(PIN_IN4, LOW);
}

void bothForward() {
  digitalWrite(PIN_IN1, LOW);
  digitalWrite(PIN_IN2, HIGH);
  digitalWrite(PIN_IN3, LOW);
  digitalWrite(PIN_IN4, HIGH);
  analogWrite(PIN_ENA, TEST_PWM);
  analogWrite(PIN_ENB, TEST_PWM);
}

void bothBackward() {
  digitalWrite(PIN_IN1, HIGH);
  digitalWrite(PIN_IN2, LOW);
  digitalWrite(PIN_IN3, HIGH);
  digitalWrite(PIN_IN4, LOW);
  analogWrite(PIN_ENA, TEST_PWM);
  analogWrite(PIN_ENB, TEST_PWM);
}

void setup() {
  pinMode(PIN_ENA, OUTPUT);
  pinMode(PIN_ENB, OUTPUT);
  pinMode(PIN_IN1, OUTPUT);
  pinMode(PIN_IN2, OUTPUT);
  pinMode(PIN_IN3, OUTPUT);
  pinMode(PIN_IN4, OUTPUT);

  stopMotors();
  Serial.begin(115200);
  delay(300);

  Serial.println(F("=== Test entrambi i canali a 255 ==="));
  Serial.println(F("RUOTE SOLLEVATE. Avvio tra 3 s."));
  delay(3000);

  for (uint8_t cycle = 0; cycle < REPEATS; cycle++) {
    Serial.print(F("Ciclo "));
    Serial.print(cycle + 1);
    Serial.println(F(": avanti 255 per 4 s"));
    bothForward();
    delay(HOLD_MS);
    stopMotors();
    Serial.println(F("Stop 2 s"));
    delay(PAUSE_MS);

    Serial.print(F("Ciclo "));
    Serial.print(cycle + 1);
    Serial.println(F(": indietro 255 per 4 s"));
    bothBackward();
    delay(HOLD_MS);
    stopMotors();
    Serial.println(F("Stop 2 s"));
    delay(PAUSE_MS);
  }

  stopMotors();
  Serial.println(F("FINE: motori fermi"));
}

void loop() {
  // Test automatico: nessuna azione nel loop.
}
