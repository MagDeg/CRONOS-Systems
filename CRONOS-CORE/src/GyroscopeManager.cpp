#include "GyroscopeManager.h"

bool GyroscopeManager::init() {
    Wire.begin();
    if (gyro.begin() == false) {
        Serial.println("BNO085 konnte nicht initialisiert werden!");
        return false;
    }
    gyro.enableAccelerometer();
    gyro.enableGravity();
    gyro.enableMagnetometer();
    gyro.enableLinearAccelerometer();
    gyro.enableRotationVector();     // Gravitation
};

AxisValues GyroscopeManager::getAcceleration() {
    AxisValues data; 
    data.x = gyro.getAccelX();
    data.y = gyro.getAccelY();
    data.z = gyro.getAccelZ();
    return data;
};

AxisValues GyroscopeManager::getGyro() {
    AxisValues data;
    data.x = gyro.getGyroX();
    data.y = gyro.getGyroY();
    data.z = gyro.getGyroZ();
    return data;
};

AxisValues GyroscopeManager::getMag() {
    AxisValues data;
    data.x = gyro.getMagX();
    data.y = gyro.getMagY();
    data.z = gyro.getMagZ();
    return data;
}

Euler GyroscopeManager::getEuler() {
    Euler data;
    data.pitch = gyro.getPitch();
    data.roll = gyro.getRoll();
    data.yaw = gyro.getYaw();
    return data;
}

Quaternion GyroscopeManager::getQuat() {
    Quaternion data;
    data.i = gyro.getQuatI();
    data.j = gyro.getQuatJ();
    data.k = gyro.getQuatK();
    data.real = gyro.getQuatReal();
    return data;
}

float GyroscopeManager::getLinearAcceleration() {
    float linX = gyro.getLinAccelX();
    float linY = gyro.getLinAccelY();
    float linZ = gyro.getLinAccelZ();
    return sqrt(linX*linX + linY*linY + linZ*linZ);

}

int GyroscopeManager::getLinearAccuracy() {
    return gyro.getLinAccelAccuracy();
    
}

int GyroscopeManager::getQuatRadianAccuracy() {
    return gyro.getQuatRadianAccuracy();
}

int GyroscopeManager::getAccelerationAccuracy() {
    return gyro.getAccelAccuracy();
}

int GyroscopeManager::getMagnetometerAccuracy() {
    return gyro.getMagAccuracy();
}

int GyroscopeManager::getGyroAccuracy() {
    return gyro.getGyroAccuracy();
}

int GyroscopeManager::getQuatAccuracy() {
    return gyro.getQuatAccuracy();
}

bool GyroscopeManager::isSensorConnected() {
    return gyro.isConnected();
}

