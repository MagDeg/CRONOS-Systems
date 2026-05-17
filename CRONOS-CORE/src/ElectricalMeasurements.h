#pragma once

#include <Wire.h>
#include <Arduino.h>
#include <Adafruit_INA219.h>
#include "Diagnostics.h"
#include <Adafruit_MAX1704X.h>


class ElectricalMeasurements {
  protected:
    TwoWire* i2c = nullptr;
    HardwareSerial* m_serial{};
    Adafruit_INA219 ina219;
    Adafruit_MAX17048 max17048;
    Diagnostics* diagnostics;

    bool ina_ok = false;
    bool max_ok = false;

  public:
    bool initINA(TwoWire* wire, HardwareSerial* serial, Diagnostics* _diagnostics);
    bool initMAX(TwoWire* wire, Diagnostics* _diagnostics);
    float getVoltage();
    float getCurrent();
    float getPower();
    float getBatteryVoltage();
    float getBatteryPercentage();

};