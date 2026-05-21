#include "ElectricalMeasurements.h"


bool ElectricalMeasurements::initINA(TwoWire* wire,
                                    HardwareSerial* serial,
                                    Diagnostics* _diagnostics) {

  i2c = wire;
  m_serial = serial;
  diagnostics = _diagnostics;

  if (!ina219.begin()) {
    m_serial->println("[ERROR] INA219 init failed!");
    diagnostics->addSystemStateToQueue(INA219_INIT_FAILED);
    ina_ok = false;
    return false;
  }
  ina219.setCalibration_32V_2A();

  ina_ok = true;
  return true;
}

bool ElectricalMeasurements::initMAX(TwoWire* wire,
                                    Diagnostics* _diagnostics) {

  i2c = wire;
  diagnostics = _diagnostics;

  if (!max17048.begin()) {
    m_serial->println("[ERROR] MAX17048 init failed!");
    diagnostics->addSystemStateToQueue(MAX17048_INIT_FAILED);
    max_ok = false;
    return false;
  }
  max17048.quickStart();
  delay(10);

  max_ok = true;
  return true;
}


float ElectricalMeasurements::getVoltage(){
  if(!ina_ok) return 0.0;
  return ina219.getBusVoltage_V();
}

float ElectricalMeasurements::getCurrent() {
  if (!ina_ok) return NAN;
  return ina219.getCurrent_mA();
}

float ElectricalMeasurements::getPower() {
  if(!i2c) return 0.0;

  return ina219.getPower_mW();
}

float ElectricalMeasurements::getBatteryVoltage() {
  if (!max_ok) return NAN;
  return max17048.cellVoltage();
}


float ElectricalMeasurements::getBatteryPercentage() {
  if (!max_ok) return NAN;
  return max17048.cellPercent();
}