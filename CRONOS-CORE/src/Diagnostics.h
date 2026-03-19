#pragma once

#include <Arduino.h>
#include "Communication.h"
#include "Pins.h"
#include "TemperatureSensorControl.h"
#include "ElectricalMeasurements.h"
#include "SystemStateQueue.h"
#include <Wire.h>

class Communication;
class TemperatureSensorControl; 
class ElectricalMeasurements;


class Diagnostics {
    protected:
        HardwareSerial* serial{};
        Communication& com;
        TemperatureSensorControl& temp_sensor;
        ElectricalMeasurements& electrical_measurement;

        SystemStateQueue system_state_queue; 
        void sendDiagnosticsMessage(bool status, String pos_msg, String neg_msg);
    public:
        Diagnostics(HardwareSerial* m_serial, Communication& m_com, TemperatureSensorControl& temp, ElectricalMeasurements& electrics)  : serial(m_serial), com(m_com), temp_sensor(temp), electrical_measurement(electrics) {};
        void startDiagnostics();
        uint8_t getSystemStateFromQueue();
        void addSystemStateToQueue(uint8_t state);

};


/* 
Global System State represents errors an problems with the system coded into a number as following:

0 -- everything OK, no isses
1 -- Radio could not be initialized
2 -- Data Transmission over Radio Failed
3 -- Bad Radio-Signalstrength
4 -- Could not initialize SD-Card
5 -- Could not open file on SD-Card
6 -- Could not write to SD-Card
7 -- Engine sensor not found
8 -- Battery sensor not found
9 -- Recieived invalid values from engine sensor
10 -- Received invalid values from battery sensor
11 -- Received invalid values from chip sensor
12 -- INA219 could not be initialized
13 -- Received invalid values for current
14 -- Received invalid values for voltage

*/