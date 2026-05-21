

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
    Serial.println(">>>Checking Temperature Sensors<<<");

    temp_sensor.init(WIRE_PIN);

    SensorStatus s = temp_sensor.checkSensorStatus();

    sendDiagnosticsMessage(s.engineFound, "Engine sensor found!", "Engine sensor not found!");
    sendDiagnosticsMessage(s.batteryFound, "Battery sensor found!", "Battery sensor not found!");

    float* value = temp_sensor.getTemperatureOfSensors();

    bool engine_sensor = (value[0] > 0.0) && (value[0] < 100.0);
    bool battery_sensor = (value[1] > 0.0) && (value[1] < 100.0);
    float chip_temperature = temp_sensor.getChipTemperature(); 
    bool chip_sensor = (chip_temperature > 0.0) && (chip_temperature < 100.0);

    sendDiagnosticsMessage(engine_sensor, "Received valid values from engine sensor!", "Received invalid values from engine sensor!");
    Serial.print("Current Engine Temperature: ");
    Serial.print(value[0]);
    Serial.println("°C"); 
    sendDiagnosticsMessage(battery_sensor, "Received valid values from battery sensor!", "Received invalid values from battery sensor!");
    Serial.print("Current Battery Temperature: ");
    Serial.print(value[1]);
    Serial.println("°C"); 
    sendDiagnosticsMessage(chip_sensor, "Received valid values from chip sensor!", "Received invalid values from chip sensor!");
    Serial.print("Current Chip Temperature: ");
    Serial.print(chip_temperature);
    Serial.println("°C"); 


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
    if (ina_ok) {
        auto current = electrical_measurement.getCurrent(); 
        bool current_validated = (current >= 0) && (current < 100); 
        sendDiagnosticsMessage(
            current_validated,
            "Received valid values for Current!",
            "Received invalid values for Current!"
        );
        Serial.print("Current Value for external Battery: ");
        Serial.print(current);
        Serial.println("A");

        auto voltage = electrical_measurement.getVoltage(); 
        bool voltage_validated = (voltage >= 0) && (current < 100);

        sendDiagnosticsMessage(
            current_validated,
            "Received valid values for Voltage!",
            "Received invalid values for Voltage!"
        );
        Serial.print("Battery Voltage Value for external Battery: ");
        Serial.print(voltage);
        Serial.println("V");
    }


    sendDiagnosticsMessage(
        max_ok,
        "MAX17048 successfully initialized!",
        "MAX17048 could not be initialized!"
    );



    if (max_ok) {

        float batt_v = electrical_measurement.getBatteryVoltage();
        float batt_p = electrical_measurement.getBatteryPercentage();

        bool battery_v_validated = (batt_v >= 0.0) && (batt_v < 100.0);
        bool battery_p_validated = (batt_p >= 0.0) && (batt_p < 100.0); 

        sendDiagnosticsMessage(
            battery_v_validated,
            "Received valid battery voltage!",
            "Received invalid battery voltage!"
        );
        Serial.print("Battery Voltage Value for internal Battery: ");
        Serial.print(batt_v);
        Serial.println("V");

        sendDiagnosticsMessage(
            battery_p_validated,
            "Received valid battery percentage!",
            "Received invalid battery percentage!"
        );
        Serial.print("Battery Percentage for internal Battery: ");
        Serial.print(batt_v);
        Serial.println("%");
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
        Serial.print("Gyro Values for x y z: ");
        Serial.print(gyro.x);
        Serial.print(" ");
        Serial.print(gyro.y);
        Serial.print(" ");
        Serial.println(gyro.z);
  

        AxisValues mag = gyro_manager.getMag();
        sendDiagnosticsMessage(
            !isnan(mag.x) && !isnan(mag.y) && !isnan(mag.z),
            "Magnetometer values valid!",
            "Magnetometer values invalid!"
        );
        Serial.print("Magnetometer Values for x y z: ");
        Serial.print(mag.x);
        Serial.print(" ");
        Serial.print(mag.y);
        Serial.print(" ");
        Serial.println(mag.z);

        AxisValues linAcc = gyro_manager.getLinearAcceleration();
        sendDiagnosticsMessage(
            !isnan(linAcc.x) && !isnan(linAcc.y) && !isnan(linAcc.z),
            "Linear acceleration values valid!",
            "Linear acceleration values invalid!"
        );
        Serial.print("Linear Acceleration Values for x y z: ");
        Serial.print(linAcc.x);
        Serial.print(" ");
        Serial.print(linAcc.y);
        Serial.print(" ");
        Serial.println(linAcc.z);

        Quaternion quat = gyro_manager.getQuat();
        sendDiagnosticsMessage(
            !isnan(quat.r) && !isnan(quat.i) && !isnan(quat.j) && !isnan(quat.k),
            "Rotation vector (quaternion) values valid!",
            "Rotation vector (quaternion) values invalid!"
        );
        Serial.print("Quaternion Values for r i j k: ");
        Serial.print(quat.r);
        Serial.print(" ");
        Serial.print(quat.i);
        Serial.print(" ");
        Serial.print(quat.j);
        Serial.print(" ");
        Serial.println(quat.k);
    }
    // -------------------- HALL SENSOR --------------------
    Serial.println(">>> Checking Hall / Speed Sensor <<<");

    
    speed_sensor.init(&Serial, HALL_SENSOR_PIN, this);
    sendDiagnosticsMessage(true,
        "Hall sensor initialized!",
        "Hall sensor could not be initialized!"
    );

    

    Wire.end(); 
    Serial.println("-----------[Tests completed]-----------");
    Serial.print("Errors: ");
    Serial.println(error_count);
    error_count = 0; 
    Serial.println("Self-Checkup has terminated! Press r to restart!");
}  

void Diagnostics::sendDiagnosticsMessage(bool status, String pos_msg, String neg_msg){
  if (status) {
    Serial.print("\033[32m[OK]\033[0m ");
    Serial.println(pos_msg);
  } else {
    Serial.print("\033[31m[FAIL]\033[0m ");
    Serial.println(neg_msg);
    error_count++; 
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