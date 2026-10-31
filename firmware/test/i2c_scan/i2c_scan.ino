/*
  Scanner I2C di banco per il Mega 2560.
  SDA=20, SCL=21. Non comanda motori.
*/

#include <Arduino.h>
#include <Wire.h>

void scanBus() {
  Serial.println("I2C_SCAN_BEGIN");
  uint8_t found = 0;

  for (uint8_t address = 1; address < 127; ++address) {
    Wire.beginTransmission(address);
    if (Wire.endTransmission() == 0) {
      Serial.print("I2C_FOUND 0x");
      if (address < 16) {
        Serial.print('0');
      }
      Serial.println(address, HEX);
      ++found;
    }
  }

  Serial.print("I2C_FOUND_COUNT ");
  Serial.println(found);
  Serial.println("I2C_SCAN_END");
}

void setup() {
  Serial.begin(115200);
  Wire.begin();
  delay(1000);
}

void loop() {
  scanBus();
  delay(2000);
}
