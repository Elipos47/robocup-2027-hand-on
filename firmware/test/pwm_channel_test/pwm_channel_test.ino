/*
  Robocup2027HandOn - test di banco: canali A e B separati a PWM 255
  Arduino Mega 2560 + L298N

  RUOTE SOLLEVATE. Il test parte 3 s dopo il reset e non richiede comandi.

  Sequenza:
    A avanti 255 per 4 s, stop 2 s
    B avanti 255 per 4 s, stop 2 s
    A indietro 255 per 4 s, stop 2 s
    B indietro 255 per 4 s, stop finale

  Mappa:
    ENA=12 IN1=22 IN2=23  (canale A, atteso ruota destra)
    ENB=13 IN3=24 IN4=25  (canale B, attesa ruota sinistra)
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

void stopMotors() {
  analogWrite(PIN_ENA, 0);
  analogWrite(PIN_ENB, 0);
  digitalWrite(PIN_IN1, LOW);
  digitalWrite(PIN_IN2, LOW);
  digitalWrite(PIN_IN3, LOW);
  digitalWrite(PIN_IN4, LOW);
}

void channelAForward() {
  digitalWrite(PIN_IN1, LOW);
  digitalWrite(PIN_IN2, HIGH);
  analogWrite(PIN_ENA, TEST_PWM);
}

void channelABackward() {
  digitalWrite(PIN_IN1, HIGH);
  digitalWrite(PIN_IN2, LOW);
  analogWrite(PIN_ENA, TEST_PWM);
}

void channelBForward() {
  digitalWrite(PIN_IN3, LOW);
  digitalWrite(PIN_IN4, HIGH);
  analogWrite(PIN_ENB, TEST_PWM);
}

void channelBBackward() {
  digitalWrite(PIN_IN3, HIGH);
  digitalWrite(PIN_IN4, LOW);
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

  Serial.println(F("=== Test canali separati A/B a 255 ==="));
  Serial.println(F("RUOTE SOLLEVATE. Avvio tra 3 s."));
  delay(3000);

  Serial.println(F("A avanti 255 per 4 s (ENA=12, IN1=L, IN2=H)"));
  channelAForward();
  delay(HOLD_MS);
  stopMotors();
  delay(PAUSE_MS);

  Serial.println(F("B avanti 255 per 4 s (ENB=13, IN3=L, IN4=H)"));
  channelBForward();
  delay(HOLD_MS);
  stopMotors();
  delay(PAUSE_MS);

  Serial.println(F("A indietro 255 per 4 s (IN1=H, IN2=L)"));
  channelABackward();
  delay(HOLD_MS);
  stopMotors();
  delay(PAUSE_MS);

  Serial.println(F("B indietro 255 per 4 s (IN3=H, IN4=L)"));
  channelBBackward();
  delay(HOLD_MS);
  stopMotors();

  Serial.println(F("FINE: motori fermi"));
}

void loop() {
}
