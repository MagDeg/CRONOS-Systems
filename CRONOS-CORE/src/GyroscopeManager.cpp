#include "GyroscopeManager.h"



bool GyroscopeManager::setReports() {
    bool success = true; 

    success &= bno.enableReport(SH2_ACCELEROMETER);
    success &= bno.enableReport(SH2_GYROSCOPE_CALIBRATED);
    success &= bno.enableReport(SH2_MAGNETIC_FIELD_CALIBRATED);
    success &= bno.enableReport(SH2_LINEAR_ACCELERATION);
    success &= bno.enableReport(SH2_ROTATION_VECTOR);

    return success; 
}

void GyroscopeManager::updateEulerAndQuat(const sh2_SensorValue_t &sv) {

    float r = sv.un.rotationVector.real;
    float i = sv.un.rotationVector.i;
    float j = sv.un.rotationVector.j;
    float k = sv.un.rotationVector.k;

    quatCache = { r, i, j, k };

    eulerCache.roll =
        atan2(2 * (r*i + j*k),
              1 - 2 * (i*i + j*j)) * 180.0 / PI;

    eulerCache.pitch =
        asin(2 * (r*j - k*i)) * 180.0 / PI;

    eulerCache.yaw =
        atan2(2 * (r*k + i*j),
              1 - 2 * (j*j + k*k)) * 180.0 / PI;
}


bool GyroscopeManager::init(Diagnostics* _diagnostics, TwoWire* wire) {

    i2c = wire;

    diagnostics = _diagnostics;
    connected = bno.begin_I2C();
    if (!connected) {
        diagnostics->addSystemStateToQueue(BNO_INIT_FAILED);
        return false;
    }

    delay(500);

    if (!setReports()) return false;

    delay(500);

    return true;
}

void GyroscopeManager::update() {

    if (!connected) return;

    if(bno.wasReset()) setReports(); 

    sh2_SensorValue_t sv;

    if (bno.getSensorEvent(&sv)) {

        switch (sv.sensorId) {

            case SH2_GYROSCOPE_CALIBRATED:
                gyroCache = {
                    sv.un.gyroscope.x,
                    sv.un.gyroscope.y,
                    sv.un.gyroscope.z
                };
                gyroStatus = sv.status;
                break;

            case SH2_MAGNETIC_FIELD_CALIBRATED:
                magCache = {
                    sv.un.magneticField.x,
                    sv.un.magneticField.y,
                    sv.un.magneticField.z
                };
                magStatus = sv.status;
                break;

            case SH2_LINEAR_ACCELERATION:
                linearCache = {
                    sv.un.linearAcceleration.x,
                    sv.un.linearAcceleration.y,
                    sv.un.linearAcceleration.z
                };
                accelStatus = sv.status;
                break;

            case SH2_ACCELEROMETER:
                linearCache = {
                    sv.un.accelerometer.x,
                    sv.un.accelerometer.y,
                    sv.un.accelerometer.z
                };
                break;

            case SH2_ROTATION_VECTOR:
                updateEulerAndQuat(sv);
                break;

            case SH2_GAME_ROTATION_VECTOR:
                gameQuatCache = {
                    sv.un.gameRotationVector.real,
                    sv.un.gameRotationVector.i,
                    sv.un.gameRotationVector.j,
                    sv.un.gameRotationVector.k
                };
                break;
        }
    }
}

AxisValues GyroscopeManager::getGyro() { return gyroCache; }
AxisValues GyroscopeManager::getMag() {  return magCache; }
AxisValues GyroscopeManager::getLinearAcceleration() { return linearCache; }
Quaternion GyroscopeManager::getQuat() {  return quatCache; }
Euler GyroscopeManager::getEuler() {  return eulerCache; }
Quaternion GyroscopeManager::getGameQuat() {  return gameQuatCache;}
