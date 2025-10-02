#include "SpeedSensor.h"

SpeedSensor::SpeedSensor(const int BUFFER_SIZE, const float SLOPE_THRESHOLD) {
  _BUFFER_SIZE = BUFFER_SIZE;
  _SLOPE_THRESHOLD = SLOPE_THRESHOLD;
  buffer = new float[_BUFFER_SIZE]();
}


void SpeedSensor::init(HardwareSerial* serial, int sensor_pin) {
  _sensor_pin = sensor_pin;
  _serial = serial;

  pinMode(_sensor_pin, INPUT);

  rawValue = analogRead(_sensor_pin);
  filteredValue = rawValue;
  lastFilteredValue = filteredValue;
}

void SpeedSensor::addValueToBuffer(float value) {
  buffer[bufferIndex] = value;
  bufferIndex = (bufferIndex + 1) % _BUFFER_SIZE;
  if (bufferCount < _BUFFER_SIZE) bufferCount++;
}

float SpeedSensor::getBufferAverage() {
  float sum = 0;
  for (int i = 0; i < bufferCount; i++) sum += buffer[i];
  return (bufferCount != 0) ? sum/bufferCount : 0; 
}

float SpeedSensor::getDriveRPM() {
  checkSensorTrigger();

  float drive = getBufferAverage();

  return drive;
}

void SpeedSensor::checkSensorTrigger() {
  rawValue = analogRead(_sensor_pin);

  filteredValue = alpha * rawValue + (1 - alpha) * filteredValue;

  float delta = filteredValue - lastFilteredValue;

  if ((delta > _SLOPE_THRESHOLD) && !triggered) {
    if (timeLastTrigger != 0) {
      timeSinceLastTrigger = micros() - timeLastTrigger;

      if (timeSinceLastTrigger > 0) {
        float rpm = 60.0 * 1000000.0 / (4.0 * timeSinceLastTrigger);
        addValueToBuffer(rpm);
      }
    }
    timeLastTrigger = micros();
    triggered = true;
  }

  if (delta < (_SLOPE_THRESHOLD/2)) {
    triggered = false;
  }

  lastFilteredValue = filteredValue; 

  
}

