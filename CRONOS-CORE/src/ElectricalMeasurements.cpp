#include "ElectricalMeasurements.h"

bool ElectricalMeasurements::init(TwoWire* wire, HardwareSerial* serial) {
  i2c = wire;
  m_serial = serial;
  if(!ina219.begin()) {
    m_serial->println("[ERROR] Could not initialize INA219!");
    return false;
  }
  return true;

}

float ElectricalMeasurements::getVoltage(){
  if(!i2c) return 0.0;

  float busVoltage = ina219.getBusVoltage_V();
  float shuntVoltage = ina219.getShuntVoltage_mV();

  return busVoltage + (shuntVoltage/1000);
}

float ElectricalMeasurements::getCurrent(){
  if(!i2c) return 0.0;

  return ina219.getCurrent_mA();  
}

float ElectricalMeasurements::getPower() {
  if(!i2c) return 0.0;

  return ina219.getPower_mW();
}