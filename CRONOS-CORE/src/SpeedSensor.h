#pragma once

#include <Arduino.h>

class SpeedSensor {
protected:
  int _sensor_pin;
  HardwareSerial* _serial;
  int _BUFFER_SIZE;

  unsigned long timeLastTrigger = 0;
  unsigned long timeSinceLastTrigger = 0;

  bool lastState; // für Flankenerkennung

  float* buffer;

  int bufferIndex = 0;
  int bufferCount = 0;

  void addValueToBuffer(float value);
  float getBufferAverage();
  void checkSensorTrigger();

public:
  SpeedSensor(const int BUFFER_SIZE);
  void init(HardwareSerial* serial, int sensor_pin); 
  float getDriveRPM();
};