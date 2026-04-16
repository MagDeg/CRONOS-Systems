

#include "Diagnostics.h"

void Diagnostics::startDiagnostics(){
    Serial.println(" Self-Checkup-Mode successfully started!");
    Serial.println();
    Serial.println(">>>Checking Communication - Radio<<<");
    sendDiagnosticsMessage(com.initRadio(CE_PIN, CSN_PIN, MODE, this), "Radio is successfully initialized!", "Radio could not be initialized!");
    yield(); // WDT füttern
    delay(5);
    sendDiagnosticsMessage(com.checkRadioConnection(), "Data Transmission over Radio successfull!", "Data Transmission over Radio failed!");
    yield(); // WDT füttern
    delay(5);
    sendDiagnosticsMessage(com.checkRadioSignalstrength(), "Good Radio-Signalstrength", "Bad Radio-Signalstrength");
    yield(); // WDT füttern
    delay(5);
    Serial.println(">>>Checking Communication - SD-Card<<<");
    sendDiagnosticsMessage(com.initSD(SD_PIN), "SD-Card is successfully initialized!", "Could not initialize SD-Card!");
    sendDiagnosticsMessage(com.openSDFile("/Checkup.txt"), "Successfully opened file on SD-Card!", "Could not open file on SD-Card");
    sendDiagnosticsMessage(com.checkWritingToSD(), "Writing to SD-Card was successfull!", "Could not write to SD-Card!");
    com.closeSDFile();
    com.removeSDFile("/Checkup.txt");
    Serial.print(">>>Checking Temperature Sensors<<<");
    SensorStatus s = temp_sensor.checkSensorStatus();
    sendDiagnosticsMessage(s.engineFound, "Engine sensor found!", "Engine sensor not found!");
    sendDiagnosticsMessage(s.batteryFound, "Battery sensor found!", "Battery sensor not found!");
    float* value = temp_sensor.getTemperatureOfSensors();
    sendDiagnosticsMessage(!isnan(value[0]), "Receivced valid values from engine sensor!", "Received invalid values from engine sensor!");
    sendDiagnosticsMessage(!isnan(value[1]), "Receivced valid values from battery sensor!", "Received invalid values from battery sensor!");
    sendDiagnosticsMessage(!isnan(temp_sensor.getChipTemperature()), "Received valid values from chip sensor!", "Received invalid values from chip sensor!");
    Serial.println(">>>Checking Electrical Measurements<<<");
    Wire.begin(SDA_PIN, SCL_PIN);
    sendDiagnosticsMessage(electrical_measurement.init(&Wire, &Serial, this), "INA219 successfully initialized!" , "INA219 could not be initialized!");
    sendDiagnosticsMessage(!isnan(electrical_measurement.getCurrent()), "Received valid values for Current!", "Received invalid values for current!");
    sendDiagnosticsMessage(!isnan(electrical_measurement.getVoltage()), "Received valid values for voltage!", "Received invalid values for voltage!");
    
    Serial.println(">>>Checking BNO085<<<");
    bool bnoInitialized = gyro_manager.init(this);
    sendDiagnosticsMessage(bnoInitialized, "BNO085 successfully initialized!", "BNO085 could not be initialized!");
    if (bnoInitialized) {
      gyro_manager.update();

      AxisValues gyro = gyro_manager.getGyro();
      sendDiagnosticsMessage(!isnan(gyro.x) && !isnan(gyro.y) && !isnan(gyro.z),"Gyroscope values valid!", "Gyroscope values invalid!");

      AxisValues mag = gyro_manager.getMag();
      sendDiagnosticsMessage(!isnan(mag.x) && !isnan(mag.y) && !isnan(mag.z), "Magnetometer values valid!", "Magnetometer values invalid!");

      AxisValues linAcc = gyro_manager.getLinearAcceleration();
      sendDiagnosticsMessage(!isnan(linAcc.x) && !isnan(linAcc.y) && !isnan(linAcc.z), "Linear acceleration values valid!", "Linear acceleration values invalid!");

      Quaternion quat = gyro_manager.getQuat();
      sendDiagnosticsMessage(!isnan(quat.r) && !isnan(quat.i) && !isnan(quat.j) && !isnan(quat.k), "Rotation vector (quaternion) values valid!", "Rotation vector (quaternion) values invalid!");
      }
    // -------------------- Hall / Speed Sensor --------------------
    Serial.println(">>> Checking Hall / Speed Sensor <<<");
    /*
    // Initialisierung des Sensors
    speed_sensor.init(serial, HALL_SENSOR_PIN, this);
    sendDiagnosticsMessage(true, "Hall sensor initialized!", "Hall sensor could not be initialized!"); // Init selbst schlägt kaum fehl
    */


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