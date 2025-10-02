#include "TemperatureSensorControl.h"
#include "Communication.h"
#include "ElectricalMeasurements.h"
#include "SpeedSensor.h"

#include <Wire.h>

//Defining Pins for all Sensors and Devices

int wire_pin = 0;
int sd_pin = 5;
int ce_pin = 6;
int csn_pin = 7;
int scl_pin = 22;
int sda_pin = 21;
int hall_sensor_pin = 0;

DeviceAddress engine_temperature_sensor = {0x28, 0x55, 0x9A, 0x5B, 0x41, 0x24, 0x0B, 0xDD};
DeviceAddress battery_temperature_sensor = {0x28, 0x61, 0x64, 0x35, 0xF9, 0x7F, 0x26, 0x7E};

TemperatureSensorControl temperatureController(engine_temperature_sensor, battery_temperature_sensor); 
Communication com;
ElectricalMeasurements electrics;
SpeedSensor speedSensor(5, 5.0);

unsigned long lastWriteTime = 0;

void setup() {


  Serial.begin(9600);
 
  Serial.print("\033[2J");  // Clear Screen
  Serial.print("\033[H");   // Cursor nach Home (oben links)
  Serial.println("Do you want to start the Self-Checkup-Mode? Y/N");
  
  unsigned long startTime = millis();

  while (millis() - startTime < 10000) {
    if (Serial.available()) {
      String input = Serial.readStringUntil('\n');
      input.trim();
      Serial.println(input);

      if (input.equalsIgnoreCase("Y")) {
        Serial.println("Starting Self-Checkup-Mode...");
        startSelfCheckup();    
        
      }

      break; // Abbruch, Eingabe erhalten
    }
  }
  Serial.println("[============================]");
  Serial.println("Starting Operating-Mode...");

  /*
  com.initRadio(&Serial, ce_pin, csn_pin);
  com.initSD(sd_pin);
  com.openSDFile("Test2.txt");
  Wire.begin(sda_pin, scl_pin);
  electrics.init(&Wire, &Serial);
  temperatureController.init(wire_pin);
  speedSensor.init(hall_sensor_pin);

  


  */
}

void loop() {
  
  //TransmissionData data;
  //data = {1,1,1.0,10,50,30,1.0,9.0,1.0};

  /*
  data.voltage = electrics.getVoltage();
  data.current = electrics.getCurrent();

  data.drive = speedSensor.getDriveRPM()
  
  data.temperature_battery = temperatureController.getTemperatureOfSensors()[1];
  data.temperature_engine = temperatureController.getTemperatureOfSensors()[0];
  data.temperature_chip = temperatureController.getChipTemperature();
  */
  //com.sendData(data);
  

  //com.saveDataForSDBuffered(data);

  /*if (millis() - lastWriteTime > 5000) {
    com.writeBufferToSD();
    lastWriteTime = millis();
  }
  */
/*
  if (Bedingung zum Abchluss des Programs -> Tasterdruck) {
    com.writeBufferToSD();
    com.closeSDFile();
  }
*/


}

void checkupMessage(bool status, String pos_msg, String neg_msg) {
  if (status) {
    Serial.print("\033[32m[OK]\033[0m ");
    Serial.println(pos_msg);
  } else {
    Serial.print("\033[31m[FAIL]\033[0m ");
    Serial.println(neg_msg);
  }
}


void startSelfCheckup() {

  Serial.println(" Self-Checkup-Mode successfully started!");
  Serial.println();

  Serial.println(">>>Checking Communication - Radio<<<");
  checkupMessage(com.initRadio(&Serial, ce_pin, csn_pin), "Radio is successfully initialized!", "Radio could not be initialized!");
  checkupMessage(com.checkRadioConnection(), "Data Transmission over Radio successfull!", "Data Transmission over Radio failed!");
  checkupMessage(com.checkRadioSignalstrength(), "Good Radio-Signalstrength", "Bad Radio-Signalstrength");
  
  Serial.println(">>>Checking Communication - SD-Card<<<");
  checkupMessage(com.initSD(sd_pin), "SD-Card is successfully initialized!", "Could not initialized SD-Card!");
  checkupMessage(com.openSDFile("Checkup.txt"), "Successfully opened file on SD-Card!", "Could not open file on SD-Card");
  checkupMessage(com.checkWritingToSD(), "Writing to SD-Card was successfull!", "Could not write to SD-Card!");
  com.closeSDFile();
  com.removeSDFile("Checkup.txt");

  Serial.print(">>>Checking Temperature Sensors<<<");
  SensorStatus s = temperatureController.checkSensorStatus();
  checkupMessage(s.engineFound, "Engine sensor found!", "Enige sensor not found!");
  checkupMessage(s.batteryFound, "Battery sensor found!", "Battery sensor not found!");
  float* value = temperatureController.getTemperatureOfSensors();
  checkupMessage(!isnan(value[0]), "Receiced valid values from engine sensor!", "Received invalid values from engine sensor!");
  checkupMessage(!isnan(value[1]), "Receiced valid values from battery sensor!", "Received invalid values from battery sensor!");
  checkupMessage(!isnan(temperatureController.getChipTemperature()), "Receiced valid values from chip sensor!", "Received invalid values from chip sensor!");
  
  Serial.println(">>>Checking Electrical Measurements<<<");
  Wire.begin();
  checkupMessage(electrics.init(&Wire, &Serial), "INA219 successfully initialized!" , "INA219 could not be initialized!");
  checkupMessage(!isnan(electrics.getCurrent()), "Received valid values for Current!", "Received invalid values for current!");
  checkupMessage(!isnan(electrics.getVoltage()), "Received valid values for voltage!", "Received invalid values for current!");

  
  //To be continued!

  



  
  return;
}