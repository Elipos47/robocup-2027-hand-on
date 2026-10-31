/*
  Robocup2027HandOn - test manuale delle direzioni dei motori
  Arduino Mega 2560 + L298N

  Mappa usata:
    ENA = 12   IN1 = 22   IN2 = 23   (canale A)
    ENB = 13   IN3 = 24   IN4 = 25   (canale B)

  Comandi dal Serial Monitor a 115200 baud:
    1 = canale A avanti
    2 = canale A indietro
    3 = canale B avanti
    4 = canale B indietro
    0 = stop
    + = aumenta il PWM di test di 10
    - = diminuisce il PWM di test di 10
    ? = aiuto

  Ogni comando muove un solo canale per RUN_MS e poi si ferma da solo.
  Le ruote devono essere sollevate e l'alimentazione dei motori separata
  dall'Arduino, con GND comune.

  Questo e' uno strumento di banco: il PWM usato qui non e' il pwm_max
  definitivo del robot.
*/

const uint8_t PIN_ENA = 12;
const uint8_t PIN_ENB = 13;
const uint8_t PIN_IN1 = 22;
const uint8_t PIN_IN2 = 23;
const uint8_t PIN_IN3 = 24;
const uint8_t PIN_IN4 = 25;

const uint8_t PWM_START = 80;
const uint8_t PWM_LIMIT = 120;
const uint8_t PWM_STEP = 10;
const unsigned long RUN_MS = 3000;

uint8_t testPwm = PWM_START;
bool moving = false;
char activeCommand = '0';
unsigned long moveStartedAt = 0;

void stopMotors() {
  analogWrite(PIN_ENA, 0);
  analogWrite(PIN_ENB, 0);
  digitalWrite(PIN_IN1, LOW);
  digitalWrite(PIN_IN2, LOW);
  digitalWrite(PIN_IN3, LOW);
  digitalWrite(PIN_IN4, LOW);

  moving = false;
  activeCommand = '0';
}

void applyPwm() {
  if (!moving) {
    return;
  }

  if (activeCommand == '1' || activeCommand == '2') {
    analogWrite(PIN_ENA, testPwm);
  } else if (activeCommand == '3' || activeCommand == '4') {
    analogWrite(PIN_ENB, testPwm);
  }
}

void startMove(char command) {
  stopMotors();

  switch (command) {
    case '1':
      digitalWrite(PIN_IN1, HIGH);
      digitalWrite(PIN_IN2, LOW);
      analogWrite(PIN_ENA, testPwm);
      Serial.print(F("Canale A avanti (IN1=H, IN2=L), ENA="));
      break;

    case '2':
      digitalWrite(PIN_IN1, LOW);
      digitalWrite(PIN_IN2, HIGH);
      analogWrite(PIN_ENA, testPwm);
      Serial.print(F("Canale A indietro (IN1=L, IN2=H), ENA="));
      break;

    case '3':
      digitalWrite(PIN_IN3, HIGH);
      digitalWrite(PIN_IN4, LOW);
      analogWrite(PIN_ENB, testPwm);
      Serial.print(F("Canale B avanti (IN3=H, IN4=L), ENB="));
      break;

    case '4':
      digitalWrite(PIN_IN3, LOW);
      digitalWrite(PIN_IN4, HIGH);
      analogWrite(PIN_ENB, testPwm);
      Serial.print(F("Canale B indietro (IN3=L, IN4=H), ENB="));
      break;

    default:
      return;
  }

  Serial.print(testPwm);
  Serial.print(F("/255 per "));
  Serial.print(RUN_MS);
  Serial.println(F(" ms, poi stop automatico."));

  moving = true;
  activeCommand = command;
  moveStartedAt = millis();
}

void printHelp() {
  Serial.println();
  Serial.println(F("=== Test direzioni motori - L298N ==="));
  Serial.println(F("Pin: ENA=12 ENB=13 IN1=22 IN2=23 IN3=24 IN4=25"));
  Serial.print(F("PWM di test: "));
  Serial.print(testPwm);
  Serial.print(F("/255 (limite "));
  Serial.print(PWM_LIMIT);
  Serial.println(F(")"));
  Serial.println(F("1=A avanti  2=A indietro  3=B avanti  4=B indietro"));
  Serial.println(F("0=stop  +=PWM  -=PWM  ?=aiuto"));
  Serial.println(F("Ruote sollevate. Un canale alla volta."));
  Serial.println();
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
  printHelp();
}

void loop() {
  if (moving && (millis() - moveStartedAt >= RUN_MS)) {
    stopMotors();
    Serial.println(F("Stop automatico."));
  }

  if (!Serial.available()) {
    return;
  }

  char c = Serial.read();

  if (c == '\r' || c == '\n' || c == ' ') {
    return;
  }

  switch (c) {
    case '1':
    case '2':
    case '3':
    case '4':
      startMove(c);
      break;

    case '0':
    case 'x':
    case 'X':
      stopMotors();
      Serial.println(F("Stop."));
      break;

    case '+':
      if (testPwm + PWM_STEP <= PWM_LIMIT) {
        testPwm += PWM_STEP;
      } else {
        testPwm = PWM_LIMIT;
      }
      applyPwm();
      Serial.print(F("PWM di test = "));
      Serial.println(testPwm);
      break;

    case '-':
      if (testPwm > PWM_STEP) {
        testPwm -= PWM_STEP;
      } else {
        testPwm = PWM_STEP;
      }
      applyPwm();
      Serial.print(F("PWM di test = "));
      Serial.println(testPwm);
      break;

    case '?':
      printHelp();
      break;

    default:
      Serial.print(F("Comando non valido: "));
      Serial.println(c);
      Serial.println(F("Premi ? per l'aiuto."));
      break;
  }
}
