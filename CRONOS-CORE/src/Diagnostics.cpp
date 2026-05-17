

#include "Diagnostics.h"

void Diagnostics::startDiagnostics() {

    Serial.println(" Self-Checkup-Mode successfully started!");
    Serial.println();

    // -------------------- RADIO --------------------
    Serial.println(">>>Checking Communication - Radio<<<");
    sendDiagnosticsMessage(
        com.initRadio(CE_PIN, CSN_PIN, MODE, this, true),
        "Radio is successfully initialized!",
        "Radio could not be initialized!"
    );

    yield();
    delay(5);

    sendDiagnosticsMessage(
        com.checkRadioConnection(),
        "Data Transmission over Radio successfull!",
        "Data Transmission over Radio failed!"
    );

    yield();
    delay(5);

    sendDiagnosticsMessage(
        com.checkRadioSignalstrength(),
        "Good Radio-Signalstrength",
        "Bad Radio-Signalstrength"
    );

    yield();
    delay(5);

    // -------------------- SD CARD --------------------
    Serial.println(">>>Checking Communication - SD-Card<<<");

    sendDiagnosticsMessage(
        com.initSD(SD_PIN),
        "SD-Card is successfully initialized!",
        "Could not initialize SD-Card!"
    );

    sendDiagnosticsMessage(
        com.openSDFile("/Checkup.txt"),
        "Successfully opened file on SD-Card!",
        "Could not open file on SD-Card"
    );

    sendDiagnosticsMessage(
        com.checkWritingToSD(),
        "Writing to SD-Card was successfull!",
        "Could not write to SD-Card!"
    );

    com.closeSDFile();
    com.removeSDFile("/Checkup.txt");

    // -------------------- TEMPERATURE --------------------
    /*Serial.println(">>>Checking Temperature Sensors<<<");

    SensorStatus s = temp_sensor.checkSensorStatus();

    sendDiagnosticsMessage(s.engineFound, "Engine sensor found!", "Engine sensor not found!");
    sendDiagnosticsMessage(s.batteryFound, "Battery sensor found!", "Battery sensor not found!");

    float* value = temp_sensor.getTemperatureOfSensors();

    sendDiagnosticsMessage(!isnan(value[0]), "Received valid values from engine sensor!", "Received invalid values from engine sensor!");
    sendDiagnosticsMessage(!isnan(value[1]), "Received valid values from battery sensor!", "Received invalid values from battery sensor!");
    sendDiagnosticsMessage(!isnan(temp_sensor.getChipTemperature()), "Received valid values from chip sensor!", "Received invalid values from chip sensor!");
    */
    // -------------------- ELECTRICAL --------------------
    Serial.println(">>>Checking Electrical Measurements<<<");

    Wire.begin(SDA_PIN, SCL_PIN);

    bool ina_ok = electrical_measurement.initINA(&Wire, &Serial, this);
    bool max_ok = electrical_measurement.initMAX(&Wire, this);

    sendDiagnosticsMessage(
        ina_ok,
        "INA219 successfully initialized!",
        "INA219 could not be initialized!"
    );


    sendDiagnosticsMessage(
        max_ok,
        "MAX17048 successfully initialized!",
        "MAX17048 could not be initialized!"
    );

    if (ina_ok) {

        sendDiagnosticsMessage(
            !isnan(electrical_measurement.getCurrent()),
            "Received valid values for Current!",
            "Received invalid values for Current!"
        );
        //Serial.println(electrical_measurement.getCurrent());

        sendDiagnosticsMessage(
            !isnan(electrical_measurement.getVoltage()),
            "Received valid values for Voltage!",
            "Received invalid values for Voltage!"
        );
        //Serial.println(electrical_measurement.getVoltage());
    }

    if (max_ok) {

        float batt_v = electrical_measurement.getBatteryVoltage();
        float batt_p = electrical_measurement.getBatteryPercentage();

        sendDiagnosticsMessage(
            !isnan(batt_v),
            "Received valid battery voltage!",
            "Received invalid battery voltage!"
        );
        //Serial.println(batt_v);

        sendDiagnosticsMessage(
            !isnan(batt_p) && batt_p >= 0.0f && batt_p <= 100.0f,
            "Received valid battery percentage!",
            "Received invalid battery percentage!"
        );
        //Serial.println(batt_p);
    }

    // -------------------- BNO085 --------------------
    Serial.println(">>>Checking BNO085<<<");

    bool bnoInitialized = gyro_manager.init(this, &Wire);

    sendDiagnosticsMessage(
        bnoInitialized,
        "BNO085 successfully initialized!",
        "BNO085 could not be initialized!"
    );

    if (bnoInitialized) {

        for (int i = 0; i< 20; i++) {
            gyro_manager.update();
            delay(5);
        }

        AxisValues gyro = gyro_manager.getGyro();
        sendDiagnosticsMessage(
            !isnan(gyro.x) && !isnan(gyro.y) && !isnan(gyro.z),
            "Gyroscope values valid!",
            "Gyroscope values invalid!"
        );
        //Serial.println(gyro.x);
        //Serial.println(gyro.y);
        //Serial.println(gyro.z);

        AxisValues mag = gyro_manager.getMag();
        sendDiagnosticsMessage(
            !isnan(mag.x) && !isnan(mag.y) && !isnan(mag.z),
            "Magnetometer values valid!",
            "Magnetometer values invalid!"
        );
        //Serial.println(mag.x);
        //Serial.println(mag.y);
        //Serial.println(mag.z);

        AxisValues linAcc = gyro_manager.getLinearAcceleration();
        sendDiagnosticsMessage(
            !isnan(linAcc.x) && !isnan(linAcc.y) && !isnan(linAcc.z),
            "Linear acceleration values valid!",
            "Linear acceleration values invalid!"
        );
        //Serial.println(linAcc.x);
        //Serial.println(linAcc.y);
        //Serial.println(linAcc.z);

        Quaternion quat = gyro_manager.getQuat();
        sendDiagnosticsMessage(
            !isnan(quat.r) && !isnan(quat.i) && !isnan(quat.j) && !isnan(quat.k),
            "Rotation vector (quaternion) values valid!",
            "Rotation vector (quaternion) values invalid!"
        );
        //Serial.println(quat.r);
        //Serial.println(quat.i);
        //Serial.println(quat.j);
        //Serial.println(quat.k);
    }
    // -------------------- HALL SENSOR --------------------
    Serial.println(">>> Checking Hall / Speed Sensor <<<");

    /*
    speed_sensor.init(serial, HALL_SENSOR_PIN, this);
    sendDiagnosticsMessage(true,
        "Hall sensor initialized!",
        "Hall sensor could not be initialized!"
    );
    */

    Wire.end(); 
    Serial.println("Self-Checkup has terminated! Proceeding to start in Operating-Mode!");
}  

void Diagnostics::sendDiagnosticsMessage(bool status, String pos_msg, String neg_msg){
  if (status) {
    Serial.print("\033[32m[OK]\033[0m ");
    Serial.println(pos_msg);
  } else {
    Serial.print("\033[31m[FAIL]\033[0m ");
    Serial.println(neg_msg);
  }
};

uint8_t Diagnostics::getSystemStateFromQueue(){
  uint8_t state;
  if (system_state_queue.pop(state) == false) {
    return 0;
  } 
  return state; 
}

void Diagnostics::addSystemStateToQueue(SystemState state) {
  system_state_queue.push(state); 
}