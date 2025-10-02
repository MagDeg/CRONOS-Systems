#pragma once

#include <OneWire.h>
#include <DallasTemperature.h>
#include "Arduino.h"

struct SensorStatus {
  bool engineFound;
  bool batteryFound;
};

class TemperatureSensorControl {
  protected:
    DeviceAddress _sensor_engine;
    DeviceAddress _sensor_battery;
    
    OneWire* oneWire;
    DallasTemperature* sensors;

  public:
    TemperatureSensorControl(const DeviceAddress& sensor_motor,  const DeviceAddress& sensor_battery);
    void init(int wire_pin);
    float* getTemperatureOfSensors();
    float getChipTemperature();
    SensorStatus checkSensorStatus(); 
};