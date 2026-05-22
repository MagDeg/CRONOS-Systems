#include "TemperatureSensorControl.h"

TemperatureSensorControl::TemperatureSensorControl(const DeviceAddress& sensor_engine, const DeviceAddress& sensor_battery) {
  memcpy(_sensor_engine, sensor_engine, sizeof(DeviceAddress));
  memcpy(_sensor_battery, sensor_battery, sizeof(DeviceAddress));
}

void TemperatureSensorControl::init(int wire_pin) {

  if (initialized) return;

  oneWire = new OneWire(wire_pin);
  if (!oneWire) {
    if (diagnostics) diagnostics->addSystemStateToQueue(SENSOR_INIT_FAILED);
    return;
  }

  sensors = new DallasTemperature(oneWire);
  if (!sensors) {
    if (diagnostics) diagnostics->addSystemStateToQueue(SENSOR_INIT_FAILED);
    return;
  }

  sensors->begin();

  initialized = true;
}

void TemperatureSensorControl::linkDiagnostics(Diagnostics* _diagnostics) {
  diagnostics = _diagnostics;
}


float* TemperatureSensorControl::getTemperatureOfSensors() {

  static float data[2];
    if (!sensors) {
    data[0] = NAN;
    data[1] = NAN;
    return data;
  }
  sensors->requestTemperatures();
  for (int i = 0; i < 2; i++) {
    if (i == 0) {
      data[0] = sensors->getTempC(_sensor_engine);
    }
    if (i == 1) {
      data[1] = sensors->getTempC(_sensor_battery);
    }
  }
  return data;
}

float TemperatureSensorControl::getChipTemperature() {
  return temperatureRead();
}

SensorStatus TemperatureSensorControl::checkSensorStatus() {
  SensorStatus status;

  //alle Sensoren auf dem Bus zählen
  int sensorCount = sensors->getDeviceCount();

  status.engineFound = false;
  status.batteryFound = false;

  DeviceAddress found;
  for (int i = 0; i < sensorCount; i++) {
    if (sensors->getAddress(found, i)) {
      if (memcmp(found, _sensor_engine, sizeof(DeviceAddress)) == 0) {
        status.engineFound = true;
      }
      if (memcmp(found, _sensor_battery, sizeof(DeviceAddress)) == 0) {
        status.batteryFound = true;
      }
    }
  }
  return status;
}