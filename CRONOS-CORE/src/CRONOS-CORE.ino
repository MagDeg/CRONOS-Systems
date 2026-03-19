#include "TemperatureSensorControl.h"
#include "Communication.h"
#include "ElectricalMeasurements.h"
#include "SpeedSensor.h"
#include "Pins.h"
#include "Diagnostics.h"

#include <Wire.h>
#include <queue>

//Defining Pins for all Sensors and Devices



DeviceAddress engine_temperature_sensor = {0x28, 0x55, 0x9A, 0x5B, 0x41, 0x24, 0x0B, 0xDD};
DeviceAddress battery_temperature_sensor = {0x28, 0x61, 0x64, 0x35, 0xF9, 0x7F, 0x26, 0x7E};

QueueHandle_t sensorQueue;
TemperatureSensorControl temperatureController(engine_temperature_sensor, battery_temperature_sensor); 
Communication com;
ElectricalMeasurements electrics;
SpeedSensor speedSensor();
Diagnostics diagnostics(&Serial, com, temperatureController, electrics);

unsigned long lastWriteTime = 0;

void sensorTask(void* pvParameters) {
  TransmissionData data;
  while(true) {

    //calling of sensordata
    xQueueOverwrite(sensorQueue, &data);
    // minimaler Yield, sonst CPU 100% ohne Pause
    taskYIELD();
  }

}

void communicationTask(void* pvParameters) {
  TransmissionData sendData;
  /*new data type for receiving data*/ TransmissionData receivedData;
  while(true) {  
    if(xQueueReceive(sensorQueue, &sendData, 0)) {
      //send data
    }
    //receive data
    taskYIELD();
  }
}


void setup() {


  Serial.begin(115200);
 
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

  // Queue für 1 Datensatz (Overwrite sorgt dafür, dass immer neuester Wert)
  sensorQueue = xQueueCreate(1, sizeof(TransmissionData));

  //sämtliche inits aller Klassen

  // Tasks auf zwei Cores starten
  xTaskCreatePinnedToCore(sensorTask, "SensorTask", 4096, NULL, 3, NULL, 1); // Core 1
  xTaskCreatePinnedToCore(communicationTask, "CommTask", 4096, NULL, 2, NULL, 0);     // Core 0

  
}

void loop() {
}



