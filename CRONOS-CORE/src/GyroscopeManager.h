#pragma once
#include <Adafruit_BNO08x.h>
#include <Wire.h>
#include <math.h>
#include "Diagnostics.h"

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

        AxisValues gyroCache{};
        AxisValues magCache{};
        AxisValues linearCache{};
        Quaternion gameQuatCache{};
        Quaternion quatCache{};
        Euler eulerCache{};
        int accelStatus = 0;
        int gyroStatus = 0;
        int magStatus = 0;
        bool connected = false;
        void setReports();
        void updateEulerAndQuat();

        Diagnostics* diagnostics;
        
    public:

        bool init(Diagnostics* _diagnostics);
        void update();
        bool isSensorConnected() {return connected;};


        AxisValues getGyro();
        AxisValues getMag();
        AxisValues getLinearAcceleration();
        Euler getEuler();
        Quaternion getQuat();
        Quaternion getGameQuat();

        int getLinearAccuracy();
        int getAccelerationAccuracy();
        int getGyroAccuracy();
        int getMagnetometerAccuracy();
        int getQuatAccuracy();
       



};