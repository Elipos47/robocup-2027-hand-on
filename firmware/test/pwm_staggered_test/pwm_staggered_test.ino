/*
  Robocup2027HandOn - test di banco: avvio scaglionato dei due canali
  Arduino Mega 2560 + L298N

  RUOTE SOLLEVATE. Il test parte 3 s dopo il reset.

  Sequenza:
    A avanti 255 da solo per 2 s;
    aggiungo B avanti 255 per 4 s (entrambi attivi);
    stop 2 s;
    B avanti 255 da solo per 2 s;
    aggiungo A avanti 255 per 4 s (entrambi attivi);
    stop finale.

  Serve a distinguere:
    - se fallisce sempre il secondo motore aggiunto -> alimentazione/corrente;
    - se fallisce sempre lo stesso canale -> canale/motore/cablaggio.

  Mappa:
    ENA=12 IN1=22 IN2=23  (canale A)
    ENB=13 IN3=24 IN4=25  (canale B)
*/

const uint8_t PIN_ENA = 12;
const uint8_t PIN_ENB = 13;
const uint8_t PIN_IN1 = 22;
const uint8_t PIN_IN2 = 23;
const uint8_t PIN_IN3 = 24;
const uint8_t PIN_IN4 = 25;

const uint8_t TEST_PWM = 255;
const unsigned long ALONE_MS = 2000;
const unsigned long BOTH_MS = 4000;
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

void channelBForward() {
  digitalWrite(PIN_IN3, LOW);
  digitalWrite(PIN_IN4, HIGH);
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

  Serial.println(F("=== Test avvio scaglionato A/B a 255 ==="));
  Serial.println(F("RUOTE SOLLEVATE. Avvio tra 3 s."));
  delay(3000);

  Serial.println(F("A da solo, avanti 255 per 2 s"));
  channelAForward();
  delay(ALONE_MS);

  Serial.println(F("aggiungo B, entrambi avanti 255 per 4 s"));
  channelBForward();
  delay(BOTH_MS);
  stopMotors();
  Serial.println(F("stop 2 s"));
  delay(PAUSE_MS);

  Serial.println(F("B da solo, avanti 255 per 2 s"));
  channelBForward();
  delay(ALONE_MS);

  Serial.println(F("aggiungo A, entrambi avanti 255 per 4 s"));
  channelAForward();
  delay(BOTH_MS);
  stopMotors();

  Serial.println(F("FINE: motori fermi"));
}

void loop() {
}
