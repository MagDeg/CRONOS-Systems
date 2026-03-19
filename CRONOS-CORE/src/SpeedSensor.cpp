#include "SpeedSensor.h"

SpeedSensor::SpeedSensor(const int BUFFER_SIZE) {
  _BUFFER_SIZE = BUFFER_SIZE;
  buffer = new float[_BUFFER_SIZE]();
}

void SpeedSensor::init(HardwareSerial* serial, int sensor_pin, Diagnostics* _diagnostics) {
  _sensor_pin = sensor_pin;
  _serial = serial;
  diagnostics = _diagnostics;

  pinMode(_sensor_pin, INPUT_PULLUP); // wichtig für A3144!

  lastState = digitalRead(_sensor_pin);
}

void SpeedSensor::addValueToBuffer(float value) {
  buffer[bufferIndex] = value;
  bufferIndex = (bufferIndex + 1) % _BUFFER_SIZE;
  if (bufferCount < _BUFFER_SIZE) bufferCount++;
}

float SpeedSensor::getBufferAverage() {
  float sum = 0;
  for (int i = 0; i < bufferCount; i++) sum += buffer[i];
  return (bufferCount != 0) ? sum / bufferCount : 0;
}

float SpeedSensor::getDriveRPM() {
  checkSensorTrigger();
  return getBufferAverage();
}

void SpeedSensor::checkSensorTrigger() {
  bool currentState = digitalRead(_sensor_pin);

  // Flanke erkennen (HIGH → LOW = Magnet erkannt)
  if (lastState == HIGH && currentState == LOW) {

    if (timeLastTrigger != 0) {
      timeSinceLastTrigger = micros() - timeLastTrigger;

      if (timeSinceLastTrigger > 0) {
        float rpm = 60.0 * 1000000.0 / (4.0 * timeSinceLastTrigger);
        addValueToBuffer(rpm);
      }
    }

    timeLastTrigger = micros();
  }

  lastState = currentState;
}