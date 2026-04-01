#include "GyroscopeManager.h"


void GyroscopeManager::setReports() {
    bno.enableReport(SH2_ACCELEROMETER);
    bno.enableReport(SH2_GYROSCOPE_CALIBRATED);
    bno.enableReport(SH2_MAGNETIC_FIELD_CALIBRATED);
    bno.enableReport(SH2_LINEAR_ACCELERATION);
    bno.enableReport(SH2_ROTATION_VECTOR);
}

void GyroscopeManager::updateEulerAndQuat() {
    float r = sensorValue.un.rotationVector.real;
    float i = sensorValue.un.rotationVector.i;
    float j = sensorValue.un.rotationVector.j;
    float k = sensorValue.un.rotationVector.k;

    quatCache = { r, i, j, k };

    // Quaternion → Euler (Grad)
    eulerCache.roll  = atan2(2*(r*i + j*k), 1 - 2*(i*i + j*j)) * 180.0 / PI;
    eulerCache.pitch = asin(2*(r*j - k*i)) * 180.0 / PI;
    eulerCache.yaw   = atan2(2*(r*k + i*j), 1 - 2*(j*j + k*k)) * 180.0 / PI;
}

bool GyroscopeManager::init(Diagnostics* _diagnostics) {
    Wire.begin(SDA_PIN, SCL_PIN);
    diagnostics = _diagnostics;
    connected = bno.begin_I2C();
    if (!connected) {
        diagnostics->addSystemStateToQueue(BNO_INIT_FAILED);
        return false;
    }

    setReports();
    return true;
}

void GyroscopeManager::update() {
    if (!connected) return;

    while (bno.getSensorEvent(&sensorValue)) {
        switch (sensorValue.sensorId) {
            case SH2_GYROSCOPE_CALIBRATED:
                gyroCache = {sensorValue.un.gyroscope.x,
                             sensorValue.un.gyroscope.y,
                             sensorValue.un.gyroscope.z};
                gyroStatus = sensorValue.status;
                break;
            case SH2_MAGNETIC_FIELD_CALIBRATED:
                magCache = {sensorValue.un.magneticField.x,
                            sensorValue.un.magneticField.y,
                            sensorValue.un.magneticField.z};
                magStatus = sensorValue.status;
                break;
            case SH2_LINEAR_ACCELERATION:
                linearCache = {sensorValue.un.linearAcceleration.x,
                               sensorValue.un.linearAcceleration.y,
                               sensorValue.un.linearAcceleration.z};
                accelStatus = sensorValue.status;               
                break;
            case SH2_GAME_ROTATION_VECTOR:
                gameQuatCache = {sensorValue.un.gameRotationVector.real,
                            sensorValue.un.gameRotationVector.i,
                            sensorValue.un.gameRotationVector.j,
                            sensorValue.un.gameRotationVector.k};
                break;
            case SH2_ROTATION_VECTOR:
                updateEulerAndQuat();
                break;
        
        }
    }
}

AxisValues GyroscopeManager::getGyro() { return gyroCache; }
AxisValues GyroscopeManager::getMag() { return magCache; }
AxisValues GyroscopeManager::getLinearAcceleration() { return linearCache; }
Quaternion GyroscopeManager::getQuat() { return quatCache; }
Quaternion GyroscopeManager::getGameQuat() { return gameQuatCache;}
