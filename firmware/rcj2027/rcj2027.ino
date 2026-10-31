/*
  Robocup2027HandOn - firmware del protocollo seriale v1.1
  Arduino Mega 2560 + L298N

  Mappa motori verificata a banco:
    canale A = ruota destra  (ENA=12, IN1=22, IN2=23)
    canale B = ruota sinistra (ENB=13, IN3=24, IN4=25)
    polarita' di entrambi i canali invertita rispetto a "IN alto = avanti"

  Protocollo: frame ASCII <payload>*<HH>\n, checksum XOR.
  Documento: docs/architecture/SERIAL_PROTOCOL.md

  ATTENZIONE: il movimento e' disabilitato per default. Per la prova di
  banco B0 impostare BENCH_MOTION_ENABLED a true e valori espliciti di
  PWM_MAX e WATCHDOG_TIMEOUT_MS. Non sono valori definitivi.
*/

#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_BNO08x.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// ------------------------------ Configurazione ------------------------------

const uint8_t PIN_ENA = 12;
const uint8_t PIN_ENB = 13;
const uint8_t PIN_IN1 = 22;
const uint8_t PIN_IN2 = 23;
const uint8_t PIN_IN3 = 24;
const uint8_t PIN_IN4 = 25;
const uint8_t PIN_TRIG = 27;
const uint8_t PIN_ECHO = 26;

const bool INVERT_A = true;
const bool INVERT_B = true;

// Configurazione di banco. Il default e' movimento disabilitato.
const bool BENCH_MOTION_ENABLED = false;
const uint8_t PWM_MAX = 0;                 // 0 = disabilitato
const unsigned long WATCHDOG_TIMEOUT_MS = 0;  // 0 = disabilitato
const bool SERVO_ENABLED = false;

const unsigned long STATUS_PERIOD_MS = 100;
const uint8_t MAX_FRAME_BYTES = 96;

const unsigned long SONAR_PERIOD_MS = 100;
const unsigned long SONAR_TIMEOUT_US = 30000;
const int SONAR_MIN_MM = 20;
const int SONAR_MAX_MM = 4000;
const unsigned long IMU_REPORT_INTERVAL_US = 50000;
const unsigned long IMU_STALE_MS = 500;
const float RAD_TO_MDEG = 57295.7795f;

// Montaggio IMU: gli assi fisici pitch/roll sono scambiati sul telaio.
// Lo scambio e' una correzione di montaggio, non una calibrazione del sensore.
const bool IMU_SWAP_PITCH_ROLL = true;
const bool IMU_INVERT_PITCH = false;
const bool IMU_INVERT_ROLL = false;

const uint16_t STATUS_SONAR_VALID = 1u << 0;
const uint16_t STATUS_IMU_VALID = 1u << 1;
const uint16_t STATUS_MOTORS_ACTIVE = 1u << 2;
const uint16_t STATUS_WATCHDOG_TRIPPED = 1u << 3;

// ------------------------------ Stato ---------------------------------------

char rxBuffer[MAX_FRAME_BYTES + 1];
uint8_t rxLen = 0;
bool rxOverflow = false;

bool handshakeSeen = false;
bool motorsActive = false;
bool watchdogTripped = false;

Adafruit_BNO08x bno08x;
bool imuReady = false;
bool imuValid = false;
unsigned long lastImuMs = 0;
unsigned long lastImuInitMs = 0;
long imuYawMdeg = 0;
long imuPitchMdeg = 0;
long imuRollMdeg = 0;

bool sonarMeasuring = false;
bool sonarValid = false;
unsigned long sonarLastTriggerMs = 0;
unsigned long sonarTriggerUs = 0;
unsigned long sonarRiseUs = 0;
int sonarDistanceMm = -1;

unsigned long lastPiSeenMs = 0;
unsigned long lastStatusMs = 0;
uint16_t statusSeq = 0;

// ------------------------------ Utility -------------------------------------

uint8_t checksum(const char* payload) {
  uint8_t value = 0;
  while (*payload != '\0') {
    value ^= static_cast<uint8_t>(*payload);
    ++payload;
  }
  return value;
}

void sendFrame(const char* payload) {
  static const char HEX_DIGITS[] = "0123456789ABCDEF";
  const uint8_t value = checksum(payload);

  Serial.print(payload);
  Serial.print('*');
  Serial.write(HEX_DIGITS[(value >> 4) & 0x0F]);
  Serial.write(HEX_DIGITS[value & 0x0F]);
  Serial.write('\n');
}

void sendError(const char* code) {
  char payload[32];
  snprintf(payload, sizeof(payload), "E,%s", code);
  sendFrame(payload);
}

void sendAck(uint16_t sequence) {
  char payload[16];
  snprintf(payload, sizeof(payload), "K,%u", static_cast<unsigned>(sequence));
  sendFrame(payload);
}

void sendVersion() {
  sendFrame("V,1,ARDUINO_MEGA,1");
}

bool parseLongValue(const char* text, long& value) {
  if (text == nullptr || *text == '\0') {
    return false;
  }

  char* end = nullptr;
  const long parsed = strtol(text, &end, 10);
  if (end == text || *end != '\0') {
    return false;
  }

  value = parsed;
  return true;
}

int hexNibble(char c) {
  if (c >= '0' && c <= '9') {
    return c - '0';
  }
  if (c >= 'A' && c <= 'F') {
    return c - 'A' + 10;
  }
  if (c >= 'a' && c <= 'f') {
    return c - 'a' + 10;
  }
  return -1;
}

int parseChecksum(const char* text) {
  if (strlen(text) != 2) {
    return -1;
  }

  const int high = hexNibble(text[0]);
  const int low = hexNibble(text[1]);
  if (high < 0 || low < 0) {
    return -1;
  }
  return (high << 4) | low;
}

long magnitude(long value) {
  return value < 0 ? -value : value;
}

bool motionReady() {
  return BENCH_MOTION_ENABLED && PWM_MAX > 0 && WATCHDOG_TIMEOUT_MS > 0;
}

// ------------------------------ Motori --------------------------------------

void setChannelA(int duty) {
  if (duty == 0) {
    digitalWrite(PIN_IN1, LOW);
    digitalWrite(PIN_IN2, LOW);
    analogWrite(PIN_ENA, 0);
    return;
  }

  const bool forward = duty > 0;
  const bool in1High = INVERT_A ? !forward : forward;

  digitalWrite(PIN_IN1, in1High ? HIGH : LOW);
  digitalWrite(PIN_IN2, in1High ? LOW : HIGH);

  const long value = magnitude(duty);
  analogWrite(PIN_ENA, value > 255 ? 255 : static_cast<uint8_t>(value));
}

void setChannelB(int duty) {
  if (duty == 0) {
    digitalWrite(PIN_IN3, LOW);
    digitalWrite(PIN_IN4, LOW);
    analogWrite(PIN_ENB, 0);
    return;
  }

  const bool forward = duty > 0;
  const bool in3High = INVERT_B ? !forward : forward;

  digitalWrite(PIN_IN3, in3High ? HIGH : LOW);
  digitalWrite(PIN_IN4, in3High ? LOW : HIGH);

  const long value = magnitude(duty);
  analogWrite(PIN_ENB, value > 255 ? 255 : static_cast<uint8_t>(value));
}

void stopMotors() {
  analogWrite(PIN_ENA, 0);
  analogWrite(PIN_ENB, 0);
  digitalWrite(PIN_IN1, LOW);
  digitalWrite(PIN_IN2, LOW);
  digitalWrite(PIN_IN3, LOW);
  digitalWrite(PIN_IN4, LOW);
  motorsActive = false;
}

void setMotors(int left, int right) {
  setChannelB(left);   // canale B = ruota sinistra
  setChannelA(right);  // canale A = ruota destra
  motorsActive = (left != 0 || right != 0);
}

// ------------------------------ Comandi -------------------------------------

void handleDrive(const char* sequenceText, const char* leftText, const char* rightText) {
  long sequenceValue = 0;
  long leftValue = 0;
  long rightValue = 0;

  if (!parseLongValue(sequenceText, sequenceValue) ||
      !parseLongValue(leftText, leftValue) ||
      !parseLongValue(rightText, rightValue)) {
    sendError("BAD_FORMAT");
    return;
  }

  if (sequenceValue < 0 || sequenceValue > 65535 ||
      leftValue < -255 || leftValue > 255 ||
      rightValue < -255 || rightValue > 255) {
    sendError("BAD_RANGE");
    return;
  }

  lastPiSeenMs = millis();
  watchdogTripped = false;

  if (!handshakeSeen) {
    sendError("MOTION_DISABLED");
    return;
  }

  if (!motionReady()) {
    sendError("MOTION_DISABLED");
    return;
  }

  if (magnitude(leftValue) > PWM_MAX || magnitude(rightValue) > PWM_MAX) {
    sendError("BAD_RANGE");
    return;
  }

  setMotors(static_cast<int>(leftValue), static_cast<int>(rightValue));
  sendAck(static_cast<uint16_t>(sequenceValue));
}

void handleFrame(char* frame) {
  const size_t length = strlen(frame);
  if (length == 0) {
    return;
  }

  char* star = strchr(frame, '*');
  if (star == nullptr || strchr(star + 1, '*') != nullptr) {
    sendError("BAD_FORMAT");
    return;
  }

  *star = '\0';
  const char* payload = frame;
  const char* checksumText = star + 1;

  const int receivedChecksum = parseChecksum(checksumText);
  if (receivedChecksum < 0) {
    sendError("BAD_FORMAT");
    return;
  }

  if (static_cast<uint8_t>(receivedChecksum) != checksum(payload)) {
    sendError("BAD_CHECKSUM");
    return;
  }

  char* fields[8];
  uint8_t fieldCount = 0;
  char* cursor = frame;

  while (cursor != nullptr) {
    if (fieldCount >= 8) {
      sendError("BAD_FORMAT");
      return;
    }

    fields[fieldCount++] = cursor;
    char* comma = strchr(cursor, ',');
    if (comma != nullptr) {
      *comma = '\0';
      cursor = comma + 1;
    } else {
      cursor = nullptr;
    }
  }

  if (fieldCount == 0 || strlen(fields[0]) != 1) {
    sendError("BAD_FORMAT");
    return;
  }

  const char kind = fields[0][0];

  if (kind == 'V') {
    if (fieldCount != 2 || strcmp(fields[1], "1") != 0) {
      sendError("BAD_FORMAT");
      return;
    }
    handshakeSeen = true;
    sendVersion();
    return;
  }

  if (kind == 'H') {
    long sequenceValue = 0;
    if (fieldCount != 2 || !parseLongValue(fields[1], sequenceValue)) {
      sendError("BAD_FORMAT");
      return;
    }
    if (sequenceValue < 0 || sequenceValue > 65535) {
      sendError("BAD_RANGE");
      return;
    }
    lastPiSeenMs = millis();
    watchdogTripped = false;
    return;
  }

  if (kind == 'D') {
    if (fieldCount != 4) {
      sendError("BAD_FORMAT");
      return;
    }
    handleDrive(fields[1], fields[2], fields[3]);
    return;
  }

  if (kind == 'X') {
    long sequenceValue = 0;
    if (fieldCount != 2 || !parseLongValue(fields[1], sequenceValue)) {
      sendError("BAD_FORMAT");
      return;
    }
    if (sequenceValue < 0 || sequenceValue > 65535) {
      sendError("BAD_RANGE");
      return;
    }

    stopMotors();
    lastPiSeenMs = millis();
    watchdogTripped = false;
    sendAck(static_cast<uint16_t>(sequenceValue));
    return;
  }

  if (kind == 'Z') {
    long sequenceValue = 0;
    long angleValue = 0;
    if (fieldCount != 3 ||
        !parseLongValue(fields[1], sequenceValue) ||
        !parseLongValue(fields[2], angleValue)) {
      sendError("BAD_FORMAT");
      return;
    }
    if (sequenceValue < 0 || sequenceValue > 65535 ||
        angleValue < 0 || angleValue > 180) {
      sendError("BAD_RANGE");
      return;
    }
    if (!SERVO_ENABLED) {
      sendError("SERVO_UNVERIFIED");
      return;
    }
    sendAck(static_cast<uint16_t>(sequenceValue));
    return;
  }

  sendError("UNKNOWN_COMMAND");
}

// ------------------------------ Ciclo ---------------------------------------

void pollSerial() {
  while (Serial.available() > 0) {
    const char c = static_cast<char>(Serial.read());

    if (c == '\r') {
      continue;
    }

    if (c == '\n') {
      if (rxOverflow) {
        sendError("LINE_TOO_LONG");
        rxOverflow = false;
        rxLen = 0;
        continue;
      }

      rxBuffer[rxLen] = '\0';
      if (rxLen > 0) {
        handleFrame(rxBuffer);
      }
      rxLen = 0;
      continue;
    }

    if (rxOverflow) {
      continue;
    }

    if (rxLen >= MAX_FRAME_BYTES - 1) {
      rxOverflow = true;
      continue;
    }

    rxBuffer[rxLen++] = c;
  }
}

void checkWatchdog() {
  if (!motorsActive) {
    return;
  }
  if (WATCHDOG_TIMEOUT_MS == 0) {
    return;
  }
  if (static_cast<unsigned long>(millis() - lastPiSeenMs) > WATCHDOG_TIMEOUT_MS) {
    stopMotors();
    watchdogTripped = true;
    sendError("WATCHDOG_STOP");
  }
}

void triggerSonar() {
  digitalWrite(PIN_TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(PIN_TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(PIN_TRIG, LOW);

  sonarTriggerUs = micros();
  sonarRiseUs = 0;
  sonarMeasuring = true;
  sonarLastTriggerMs = millis();
}

void serviceSonar() {
  if (!sonarMeasuring) {
    if (static_cast<unsigned long>(millis() - sonarLastTriggerMs) >= SONAR_PERIOD_MS) {
      triggerSonar();
    }
    return;
  }

  const unsigned long nowUs = micros();
  const bool echoHigh = digitalRead(PIN_ECHO) == HIGH;

  if (echoHigh && sonarRiseUs == 0) {
    sonarRiseUs = nowUs;
    return;
  }

  if (!echoHigh && sonarRiseUs != 0) {
    const unsigned long durationUs = nowUs - sonarRiseUs;
    sonarMeasuring = false;
    sonarRiseUs = 0;

    if (durationUs >= 100 && durationUs <= SONAR_TIMEOUT_US) {
      const unsigned long distanceMm = durationUs * 10UL / 58UL;
      if (distanceMm >= SONAR_MIN_MM && distanceMm <= SONAR_MAX_MM) {
        sonarDistanceMm = static_cast<int>(distanceMm);
        sonarValid = true;
        return;
      }
    }

    sonarDistanceMm = -1;
    sonarValid = false;
    return;
  }

  if (sonarRiseUs == 0 && nowUs - sonarTriggerUs > SONAR_TIMEOUT_US) {
    sonarMeasuring = false;
    sonarDistanceMm = -1;
    sonarValid = false;
  } else if (sonarRiseUs != 0 && nowUs - sonarRiseUs > SONAR_TIMEOUT_US) {
    sonarMeasuring = false;
    sonarRiseUs = 0;
    sonarDistanceMm = -1;
    sonarValid = false;
  }
}

void updateImuEuler(float qi, float qj, float qk, float qr) {
  const float sinRoll = 2.0f * (qr * qi + qj * qk);
  const float cosRoll = 1.0f - 2.0f * (qi * qi + qj * qj);
  const float roll = atan2(sinRoll, cosRoll);

  float sinPitch = 2.0f * (qr * qj - qk * qi);
  if (sinPitch > 1.0f) {
    sinPitch = 1.0f;
  } else if (sinPitch < -1.0f) {
    sinPitch = -1.0f;
  }
  const float pitch = asin(sinPitch);

  const float sinYaw = 2.0f * (qr * qk + qi * qj);
  const float cosYaw = 1.0f - 2.0f * (qj * qj + qk * qk);
  const float yaw = atan2(sinYaw, cosYaw);

  long pitchMdeg = lround(pitch * RAD_TO_MDEG);
  long rollMdeg = lround(roll * RAD_TO_MDEG);

  if (IMU_SWAP_PITCH_ROLL) {
    const long temporary = pitchMdeg;
    pitchMdeg = rollMdeg;
    rollMdeg = temporary;
  }
  if (IMU_INVERT_PITCH) {
    pitchMdeg = -pitchMdeg;
  }
  if (IMU_INVERT_ROLL) {
    rollMdeg = -rollMdeg;
  }

  imuPitchMdeg = pitchMdeg;
  imuRollMdeg = rollMdeg;
  imuYawMdeg = lround(yaw * RAD_TO_MDEG);
}

void setupImu() {
  Wire.begin();
  const uint8_t addresses[] = {0x4A, 0x4B};

  for (uint8_t index = 0; index < 2; ++index) {
    Wire.beginTransmission(addresses[index]);
    if (Wire.endTransmission() != 0) {
      continue;
    }

    if (bno08x.begin_I2C(addresses[index], &Wire)) {
      imuReady = bno08x.enableReport(
          SH2_GAME_ROTATION_VECTOR,
          IMU_REPORT_INTERVAL_US);
      return;
    }
  }

  imuReady = false;
}

void serviceImu() {
  if (!imuReady) {
    if (static_cast<unsigned long>(millis() - lastImuInitMs) >= 1000) {
      lastImuInitMs = millis();
      setupImu();
    }
    return;
  }

  sh2_SensorValue_t event;
  while (bno08x.getSensorEvent(&event)) {
    if (event.sensorId != SH2_GAME_ROTATION_VECTOR) {
      continue;
    }

    const sh2_RotationVector_t& quaternion = event.un.gameRotationVector;
    updateImuEuler(quaternion.i, quaternion.j, quaternion.k, quaternion.real);
    imuValid = true;
    lastImuMs = millis();
  }

  if (imuValid && static_cast<unsigned long>(millis() - lastImuMs) > IMU_STALE_MS) {
    imuValid = false;
  }
}

void sendStatus() {
  uint16_t status = 0;
  if (sonarValid) {
    status |= STATUS_SONAR_VALID;
  }
  if (imuValid) {
    status |= STATUS_IMU_VALID;
  }
  if (motorsActive) {
    status |= STATUS_MOTORS_ACTIVE;
  }
  if (watchdogTripped) {
    status |= STATUS_WATCHDOG_TRIPPED;
  }

  char payload[64];
  snprintf(
      payload,
      sizeof(payload),
      "A,%u,%d,%ld,%ld,%ld,%u",
      static_cast<unsigned>(statusSeq++),
      sonarDistanceMm,
      imuYawMdeg,
      imuPitchMdeg,
      imuRollMdeg,
      static_cast<unsigned>(status));
  sendFrame(payload);
}

void sendStatusIfDue() {
  if (!handshakeSeen) {
    return;
  }

  const unsigned long now = millis();
  if (static_cast<unsigned long>(now - lastStatusMs) >= STATUS_PERIOD_MS) {
    lastStatusMs = now;
    sendStatus();
  }
}

void setup() {
  Serial.begin(115200);

  pinMode(PIN_ENA, OUTPUT);
  pinMode(PIN_ENB, OUTPUT);
  pinMode(PIN_IN1, OUTPUT);
  pinMode(PIN_IN2, OUTPUT);
  pinMode(PIN_IN3, OUTPUT);
  pinMode(PIN_IN4, OUTPUT);
  pinMode(PIN_TRIG, OUTPUT);
  pinMode(PIN_ECHO, INPUT);

  digitalWrite(PIN_TRIG, LOW);
  stopMotors();
  setupImu();

  lastPiSeenMs = millis();
  lastStatusMs = millis();
}

void loop() {
  pollSerial();
  serviceSonar();
  serviceImu();
  checkWatchdog();
  sendStatusIfDue();
}
