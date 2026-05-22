#pragma once

#include <Adafruit_BNO08x.h>
#include <Wire.h>
#include <Arduino.h>
#include <Diagnostics.h>

struct BNOData {
    float lin_x = 0;
    float lin_y = 0;
    float mag_z = 0;
    float yaw = 0;
};

class GyroscopeManager {
public:
    bool begin(TwoWire* wire, Diagnostics* _diagnostics);
    void update();

    BNOData getData();


private:
    Adafruit_BNO08x bno;
    TwoWire* i2c = nullptr;

    BNOData data;
    Diagnostics* _diagnostics; 

    portMUX_TYPE mux = portMUX_INITIALIZER_UNLOCKED;
    int lastValidEvent;
    bool isInitialized; 
    int lastInitAttempt;

    void handleEvent(sh2_SensorValue_t& sv);
    void reinit();
};