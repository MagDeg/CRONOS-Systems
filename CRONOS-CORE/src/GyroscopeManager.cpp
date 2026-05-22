#include "GyroscopeManager.h"

bool GyroscopeManager::begin(TwoWire* wire, Diagnostics* diagnostics) {
    i2c = wire;
    _diagnostics = diagnostics;

    if (!bno.begin_I2C(0x4A, i2c)) {
        Serial.println("BNO not found!");
        return false;
    }

    delay(100);

    bno.enableReport(SH2_LINEAR_ACCELERATION);
    bno.enableReport(SH2_MAGNETIC_FIELD_CALIBRATED);
    bno.enableReport(SH2_ROTATION_VECTOR);

    delay(100);

    lastValidEvent = millis();
    isInitialized = true;

    return true;
}

void GyroscopeManager::update() {

    if (!isInitialized) return;

    sh2_SensorValue_t sv;
    bool gotEvent = false;

    while (bno.getSensorEvent(&sv)) {
        gotEvent = true;
        handleEvent(sv);
    }

    if (gotEvent) {
        lastValidEvent = millis();
    }

    // -------------------------
    // WATCHDOG (critical fix)
    // -------------------------
    if (millis() - lastValidEvent > 1000) {
        Serial.println("[BNO085] stream lost → reinit");

        reinit();
    }
}

void GyroscopeManager::reinit() {

    if (millis() - lastInitAttempt < 2000) return;
    lastInitAttempt = millis();

    isInitialized = false;

    // reset cached values (prevents fake old data)
    data = BNOData();

    // restart I2C safely
    i2c->end();
    delay(50);
    i2c->begin(26, 27);   // your pins
    i2c->setClock(100000);

    delay(100);

    if (bno.begin_I2C(0x4A, i2c)) {

        bno.enableReport(SH2_LINEAR_ACCELERATION);
        bno.enableReport(SH2_MAGNETIC_FIELD_CALIBRATED);
        bno.enableReport(SH2_ROTATION_VECTOR);

        isInitialized = true;
        lastValidEvent = millis();

        Serial.println("[BNO085] reinit OK");
    } else {
        Serial.println("[BNO085] reinit failed");
    }
}

void GyroscopeManager::handleEvent(sh2_SensorValue_t& sv) {

    portENTER_CRITICAL(&mux);

    switch (sv.sensorId) {

        case SH2_LINEAR_ACCELERATION:
            data.lin_x = sv.un.linearAcceleration.x;
            data.lin_y = sv.un.linearAcceleration.y;
            break;

        case SH2_MAGNETIC_FIELD_CALIBRATED:
            data.mag_z = sv.un.magneticField.z;
            break;

        case SH2_ROTATION_VECTOR: {
            float r = sv.un.rotationVector.real;
            float i = sv.un.rotationVector.i;
            float j = sv.un.rotationVector.j;
            float k = sv.un.rotationVector.k;

            // yaw only
            data.yaw = atan2(2.0f * (r * k + i * j),
                             1.0f - 2.0f * (j * j + k * k)) * 180.0f / PI;
            break;
        }

        default:
            break;
    }

    portEXIT_CRITICAL(&mux);
}

BNOData GyroscopeManager::getData() {
    portENTER_CRITICAL(&mux);
    BNOData out = data;
    portEXIT_CRITICAL(&mux);
    return out;
}