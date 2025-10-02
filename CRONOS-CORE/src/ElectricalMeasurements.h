#pragma once

#include <Wire.h>
#include <Arduino.h>
#include <Adafruit_INA219.h>


class ElectricalMeasurements {
  protected:
    TwoWire* i2c = nullptr;
    HardwareSerial* m_serial{};
    Adafruit_INA219 ina219;

  public:
    bool init(TwoWire* wire, HardwareSerial* serial);
    float getVoltage();
    float getCurrent();
    float getPower();

};