

#include "Diagnostics.h"

void Diagnostics::startDiagnostics(){
    Serial.print(" Self-Checkup-Mode successfully started!\n\n");

    Serial.println(">>>Checking Communication - Radio<<<");
    sendDiagnosticsMessage(com.initRadio(serial, CE_PIN, CSN_PIN, MODE, this), "Radio is successfully initialized!", "Radio could not be initialized!");
    sendDiagnosticsMessage(com.checkRadioConnection(), "Data Transmission over Radio successfull!", "Data Transmission over Radio failed!");
    sendDiagnosticsMessage(com.checkRadioSignalstrength(), "Good Radio-Signalstrength", "Bad Radio-Signalstrength");
  
    Serial.println(">>>Checking Communication - SD-Card<<<");
    sendDiagnosticsMessage(com.initSD(SD_PIN), "SD-Card is successfully initialized!", "Could not initialize SD-Card!");
    sendDiagnosticsMessage(com.openSDFile("Checkup.txt"), "Successfully opened file on SD-Card!", "Could not open file on SD-Card");
    sendDiagnosticsMessage(com.checkWritingToSD(), "Writing to SD-Card was successfull!", "Could not write to SD-Card!");
    com.closeSDFile();
    com.removeSDFile("Checkup.txt");

    Serial.print(">>>Checking Temperature Sensors<<<");
    SensorStatus s = temp_sensor.checkSensorStatus();
    sendDiagnosticsMessage(s.engineFound, "Engine sensor found!", "Engine sensor not found!");
    sendDiagnosticsMessage(s.batteryFound, "Battery sensor found!", "Battery sensor not found!");
    float* value = temp_sensor.getTemperatureOfSensors();
    sendDiagnosticsMessage(!isnan(value[0]), "Receivced valid values from engine sensor!", "Received invalid values from engine sensor!");
    sendDiagnosticsMessage(!isnan(value[1]), "Receivced valid values from battery sensor!", "Received invalid values from battery sensor!");
    sendDiagnosticsMessage(!isnan(temp_sensor.getChipTemperature()), "Received valid values from chip sensor!", "Received invalid values from chip sensor!");
    
    Serial.println(">>>Checking Electrical Measurements<<<");
    Wire.begin();
    sendDiagnosticsMessage(electrical_measurement.init(&Wire, &Serial, this), "INA219 successfully initialized!" , "INA219 could not be initialized!");
    sendDiagnosticsMessage(!isnan(electrical_measurement.getCurrent()), "Received valid values for Current!", "Received invalid values for current!");
    sendDiagnosticsMessage(!isnan(electrical_measurement.getVoltage()), "Received valid values for voltage!", "Received invalid values for voltage!");
    
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

void Diagnostics::addSystemStateToQueue(uint8_t state) {
  system_state_queue.push(state); 
}