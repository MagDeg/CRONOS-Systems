#pragma once

#include <OneWire.h>
#include <DallasTemperature.h>
#include "Arduino.h"
#include "Diagnostics.h"

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
    Diagnostics* diagnostics;

  public:
    TemperatureSensorControl(const DeviceAddress& sensor_motor,  const DeviceAddress& sensor_battery);
    void init(int wire_pin, Diagnostics* _diagnostics);
    float* getTemperatureOfSensors();
    float getChipTemperature();
    SensorStatus checkSensorStatus(); 
};