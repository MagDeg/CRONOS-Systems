#pragma once

#include <Arduino.h>
#include <Wire.h>
#include <DallasTemperature.h>


class Diagnostics;

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
    void init(int wire_pin);
    void linkDiagnostics(Diagnostics* _diagnostics);
    float* getTemperatureOfSensors();
    float getChipTemperature();
    SensorStatus checkSensorStatus(); 
};