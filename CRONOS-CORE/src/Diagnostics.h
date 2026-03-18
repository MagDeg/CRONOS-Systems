#pragma once

#include <Arduino.h>
#include "Communication.h"
#include "Pins.h"
#include "TemperatureSensorControl.h"
#include "ElectricalMeasurements.h"
#include <Wire.h>

class Diagnostics {
    protected:
        HardwareSerial* serial{};
        Communication& com;
        TemperatureSensorControl& temp_sensor;
        ElectricalMeasurements& electrical_measurement;
        void sendDiagnosticsMessage(bool status, String pos_msg, String neg_msg);
    public:
        Diagnostics(HardwareSerial* m_serial, Communication& m_com, TemperatureSensorControl& temp, ElectricalMeasurements& electrics)  : serial(m_serial), com(m_com), temp_sensor(temp), electrical_measurement(electrics) {};
        void startDiagnostics();

};
