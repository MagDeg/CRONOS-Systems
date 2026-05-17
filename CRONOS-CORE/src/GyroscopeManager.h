#pragma once
#include <Adafruit_BNO08x.h>
#include <Wire.h>
#include <math.h>
#include "Diagnostics.h"
#include <Arduino.h>

struct AxisValues {
    float x; 
    float y;
    float z;
};

struct Euler {
    float yaw;
    float pitch;
    float roll;
};

struct Quaternion {
    float r;
    float i;
    float j; 
    float k;
};


class GyroscopeManager {
    protected:
        static constexpr int BNO08X_RESET = -1;  // kein physischer Reset-Pin
        Adafruit_BNO08x bno;
        sh2_SensorValue_t sensorValue;  
        TwoWire* i2c = nullptr;

        AxisValues gyroCache{-1, -1, -1};
        AxisValues magCache{-1, -1, -1};
        AxisValues linearCache{-1, -1, -1};   
        Quaternion gameQuatCache{-1, -1, -1};
        Quaternion quatCache{-1, -1, -1};
        Euler eulerCache{-1, -1, -1};
        int accelStatus = 0;
        int gyroStatus = 0;
        int magStatus = 0;
        bool connected = false;
        bool setReports();
        void updateEulerAndQuat();

        Diagnostics* diagnostics;
        
    public:

        bool init(Diagnostics* _diagnostics, TwoWire* wire);
        void update();
        bool isSensorConnected() {return connected;};
        void reset();


        AxisValues getGyro();
        AxisValues getMag();
        AxisValues getLinearAcceleration();
        Euler getEuler();
        Quaternion getQuat();
        Quaternion getGameQuat();

        void updateEulerAndQuat(const sh2_SensorValue_t &sv);

        int getLinearAccuracy();
        int getAccelerationAccuracy();
        int getGyroAccuracy();
        int getMagnetometerAccuracy();
        int getQuatAccuracy();
       



};