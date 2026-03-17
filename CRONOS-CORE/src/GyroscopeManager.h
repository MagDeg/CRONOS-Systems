#include <SparkFun_BNO08x_Arduino_Library.h>
#include <Wire.h>

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
    float i;
    float j;
    float k; 
    float real;
};


class GyroscopeManager {
    protected:
        BNO08x gyro;
        
    public:
        bool init();
        AxisValues getAcceleration();
        AxisValues getGyro();
        AxisValues getMag();
        Euler getEuler();
        Quaternion getQuat();
        float getLinearAcceleration();
        int getLinearAccuracy();
        int getQuatRadianAccuracy();
        int getAccelerationAccuracy();
        int getGyroAccuracy();
        int getMagnetometerAccuracy();
        int getQuatAccuracy();
        bool isSensorConnected();




};