#include "TemperatureSensorControl.h"
#include "Communication.h"
#include "ElectricalMeasurements.h"
#include "SpeedSensor.h"
#include "Pins.h"
#include "Diagnostics.h"
#include "GyroscopeManager.h"

#include <Wire.h>
#include <queue>




DeviceAddress engine_temperature_sensor = {0x28, 0x55, 0x9A, 0x5B, 0x41, 0x24, 0x0B, 0xDD};
DeviceAddress battery_temperature_sensor = {0x28, 0x61, 0x64, 0x35, 0xF9, 0x7F, 0x26, 0x7E};

QueueHandle_t sensorQueue;
TemperatureSensorControl temperatureController(engine_temperature_sensor, battery_temperature_sensor); 
Communication com(Serial);
ElectricalMeasurements electrics;
SpeedSensor speedSensor(10);
GyroscopeManager gyro_manager;
Diagnostics diagnostics(Serial, com, temperatureController, electrics, gyro_manager, speedSensor);

unsigned long lastWriteTime = 0;
uint16_t lastTxTime = 0; 
uint8_t packet_number = 0;

int32_t storing_interval = 5000;

void sensorTask(void* pvParameters) {
  DataToMaster data;
  while(true) {
    data.current = electrics.getCurrent();
    data.voltage = electrics.getVoltage();
    data.drive = speedSensor.getDriveRPM();
    data.gyro_z = gyro_manager.getGyro().z;
    data.lin_accel_x = gyro_manager.getLinearAcceleration().x;
    data.lin_accel_y = gyro_manager.getLinearAcceleration().y;
    data.euler = gyro_manager.getEuler().yaw;
    data.status = diagnostics.getSystemStateFromQueue();
    uint16_t txTimeStamp = (uint16_t)(millis() - lastTxTime);
    lastTxTime = millis();
    data.timestamp = txTimeStamp;
    data.temperature_chip = temperatureController.getChipTemperature();
    data.temperature_battery = temperatureController.getTemperatureOfSensors()[1];
    data.temperature_engine = temperatureController.getTemperatureOfSensors()[0];
    data.packet_number = packet_number;
    packet_number++;
    com.saveDataForSDBuffered(data);
    if(millis() - lastWriteTime > storing_interval) {
      com.writeBufferToSD();
      lastWriteTime = millis();
    }

    xQueueOverwrite(sensorQueue, &data);
    // minimaler Yield, sonst CPU 100% ohne Pause
    taskYIELD();
  }

}

void communicationTask(void* pvParameters) {
  DataToMaster data_to_master;
  DataFromMaster data_from_master;
  while(true) {  
    if(xQueueReceive(sensorQueue, &data_to_master, 0)) {
      com.sendDataToMaster(data_to_master);
    }
    com.receiveDataFromMasterDynPayload(data_from_master);
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
  sensorQueue = xQueueCreate(1, sizeof(DataToMaster));

  //sämtliche inits aller Klassen
  com.initRadio(CE_PIN, CSN_PIN, 1, &diagnostics, true);
  com.initSD(SD_PIN);
  electrics.init(&Wire, &Serial, &diagnostics);
  speedSensor.init(&Serial, HALL_SENSOR_PIN, &diagnostics);
  temperatureController.init(WIRE_PIN);
  gyro_manager.init(&diagnostics);

  // Tasks auf zwei Cores starten
  xTaskCreatePinnedToCore(sensorTask, "SensorTask", 4096, NULL, 3, NULL, 1); // Core 1
  xTaskCreatePinnedToCore(communicationTask, "CommTask", 4096, NULL, 2, NULL, 0);     // Core 0

  
}

void loop() {
}



