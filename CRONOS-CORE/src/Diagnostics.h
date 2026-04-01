#pragma once

#include <Arduino.h>
#include "Communication.h"
#include "Pins.h"
#include "TemperatureSensorControl.h"
#include "ElectricalMeasurements.h"
#include "SystemStateQueue.h"
#include "GyroscopeManager.h"
#include "SpeedSensor.h"
#include <Wire.h>

class Communication;
class TemperatureSensorControl; 
class ElectricalMeasurements;
class GyroscopeManager;
class SpeedSensor;

enum SystemState {
    NO_ISSUES = 0,
    RADIO_INIT_FAILED = 1,
    DATA_TRANSMISSION_FAILED = 2,
    BAD_SIGNAL_STRENGTH = 3,
    SD_INIT_FAILED = 4,
    SD_FILE_OPEN_FAILED = 5,
    SD_WRITE_FAILED = 6,
    ENGINE_SENSOR_NOT_FOUND = 7,
    BATTERY_SENSOR_NOT_FOUND = 8,
    INVALID_ENGINE_SENSOR_VALUES = 9,
    INVALID_BATTERY_SENSOR_VALUES = 10,
    INVALID_CHIP_SENSOR_VALUES = 11,
    INA219_INIT_FAILED = 12,
    INVALID_CURRENT_VALUES = 13,
    INVALID_VOLTAGE_VALUES = 14,
    NO_RADIO_CONNECTION = 15,
    SD_FILE_NOT_OPEN = 16,
    BNO_INIT_FAILED = 17, 
    HALL_SENSOR_NOT_DETECTED = 19,

};



class Diagnostics {
    protected:
        HardwareSerial* serial{};
        Communication& com;
        TemperatureSensorControl& temp_sensor;
        ElectricalMeasurements& electrical_measurement;
        GyroscopeManager& gyro_manager;
        SpeedSensor& speed_sensor;

        SystemStateQueue system_state_queue; 
        void sendDiagnosticsMessage(bool status, String pos_msg, String neg_msg);
    public:
        Diagnostics(HardwareSerial* m_serial, Communication& m_com, TemperatureSensorControl& temp, ElectricalMeasurements& electrics, GyroscopeManager& _gyro_manager, SpeedSensor& _speed_sensor)  : speed_sensor(_speed_sensor), gyro_manager(_gyro_manager), serial(m_serial), com(m_com), temp_sensor(temp), electrical_measurement(electrics) {};
        void startDiagnostics();
        uint8_t getSystemStateFromQueue();
        void addSystemStateToQueue(SystemState state);

};


