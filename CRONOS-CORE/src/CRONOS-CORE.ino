#include "TemperatureSensorControl.h"
#include "Communication.h"
#include "ElectricalMeasurements.h"
#include "SpeedSensor.h"
#include "Pins.h"
#include "Diagnostics.h"

#include <Wire.h>

//Defining Pins for all Sensors and Devices



DeviceAddress engine_temperature_sensor = {0x28, 0x55, 0x9A, 0x5B, 0x41, 0x24, 0x0B, 0xDD};
DeviceAddress battery_temperature_sensor = {0x28, 0x61, 0x64, 0x35, 0xF9, 0x7F, 0x26, 0x7E};

TemperatureSensorControl temperatureController(engine_temperature_sensor, battery_temperature_sensor); 
Communication com;
ElectricalMeasurements electrics;
SpeedSensor speedSensor;
Diagnostics diagnostics(&Serial, com, temperatureController, electrics);

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
        diagnostics.startDiagnostics();    
        
      }

      break; // Abbruch, Eingabe erhalten
    }
  }
  Serial.println("[============================]");
  Serial.println("Starting Operating-Mode...");

  /*
  com.initRadio(&Serial, ce_pin, csn_pin);
  com.initSD(SD_PIN);
  com.openSDFile("Test2.txt");
  Wire.begin(sda_pin, scl_pin);
  electrics.init(&Wire, &Serial);
  temperatureController.init(WIRE_PIN);
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

