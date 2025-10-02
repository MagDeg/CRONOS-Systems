#include "TemperatureSensorControl.h"

TemperatureSensorControl::TemperatureSensorControl(const DeviceAddress& sensor_engine, const DeviceAddress& sensor_battery) {
  memcpy(_sensor_engine, sensor_engine, sizeof(DeviceAddress));
  memcpy(_sensor_battery, sensor_battery, sizeof(DeviceAddress));
}

void TemperatureSensorControl::init(int pin) {
  oneWire = new OneWire(pin);
  sensors = new DallasTemperature(oneWire);
  sensors->begin();
}

float* TemperatureSensorControl::getTemperatureOfSensors() {

  static float data[2];
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
  return 0.0;
  //return temperatureRead();
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