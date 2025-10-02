#pragma once

#include <Arduino.h>

class SpeedSensor {
  protected:
  int _sensor_pin;
  HardwareSerial* _serial;
  int _BUFFER_SIZE;
  float _SLOPE_THRESHOLD;

  unsigned long timeLastTrigger;
  unsigned long timeSinceLastTrigger;

  bool triggered = false;

  float* buffer;

  float rawValue = 0.0;
  int bufferIndex = 0;
  int bufferCount = 0;

  float alpha = 0.2;
  float filteredValue = 0.0;
  float lastFilteredValue = 0.0;
  
  void addValueToBuffer(float value);
  float getBufferAverage();
  void checkSensorTrigger();

  public:
  SpeedSensor(const int BUFFER_SIZE, const float SLOPE_THRESHOLD);
  void init(HardwareSerial* serial, int sensor_pin); 
  float getDriveRPM();


};