/*
  Robocup2027HandOn - test di banco: canale A avanti a 255 in loop
  Arduino Mega 2560 + L298N

  RUOTE SOLLEVATE. Il test parte 3 s dopo il reset e ripete:
    A avanti 255 per 5 s
    stop per 5 s

  Serve a tenere una fase stabile abbastanza a lungo per misurare con il
  multimetro +12, 5V, ENA, OUT1, OUT2 e temperatura del L298N, senza dover
  premere reset a ogni lettura.

  Per fermare: togli alimentazione ai motori. Il reset fa ripartire il ciclo
  dopo 3 s.

  Mappa:
    ENA=12 IN1=22 IN2=23  (canale A, atteso ruota destra)
    ENB=13 IN3=24 IN4=25  (canale B, tenuto fermo)
*/

const uint8_t PIN_ENA = 12;
const uint8_t PIN_ENB = 13;
const uint8_t PIN_IN1 = 22;
const uint8_t PIN_IN2 = 23;
const uint8_t PIN_IN3 = 24;
const uint8_t PIN_IN4 = 25;

const uint8_t TEST_PWM = 255;
const unsigned long ON_MS = 5000;
const unsigned long OFF_MS = 5000;

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

  Serial.println(F("=== Test A avanti 255 in loop ==="));
  Serial.println(F("RUOTE SOLLEVATE. Avvio tra 3 s."));
  Serial.println(F("Ciclo: 5 s ON, 5 s OFF. Per fermare togli alimentazione motori."));
  delay(3000);
}

void loop() {
  Serial.print(F("A avanti 255 - t="));
  Serial.println(millis());
  channelAForward();
  delay(ON_MS);

  stopMotors();
  Serial.print(F("stop - t="));
  Serial.println(millis());
  delay(OFF_MS);
}
