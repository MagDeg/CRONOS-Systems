#include "TemperatureSensorControl.h"
#include "Communication.h"
#include "ElectricalMeasurements.h"
#include "SpeedSensor.h"
#include "Pins.h"
#include "Diagnostics.h"
#include "GyroscopeManager.h"

#include <Wire.h>
#include <queue>

#define SD_FILE_NAME "/SensorData"


DeviceAddress engine_temperature_sensor = {0x28, 0x61, 0x64, 0x35, 0xD5, 0xA6, 0x15, 0x67};
DeviceAddress battery_temperature_sensor = {0x28, 0x61, 0x64, 0x35, 0xF9, 0x6E, 0x2C, 0x28};

bool radioAutoAck = true;
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
  DataToMaster_complete data;
  while(true) {
    gyro_manager.update();
    data.current = electrics.getCurrent();
    //Serial.println("Current works");
    data.voltage = electrics.getVoltage();
    //Serial.println("Voltage works");
    data.drive = speedSensor.getDriveRPM();
    //Serial.println("Drive works");
    data.gyro_z = gyro_manager.getData().mag_z;
    //Serial.print("gyro z:");
    //Serial.print(data.gyro_z);
    data.lin_accel_x = gyro_manager.getData().lin_x;
    //Serial.print(" lin x:");
    //Serial.print(data.lin_accel_x);
    //Serial.println("Linaccel x works");
    data.lin_accel_y = gyro_manager.getData().lin_y;
    //Serial.print(" lin y:");
    //Serial.println(data.lin_accel_y);
    //Serial.println("Linaccel y works");
    data.euler = gyro_manager.getData().yaw;
    //Serial.print(" yaw:");
    //Serial.println(data.euler);
    //Serial.println("euler works");
    data.status = diagnostics.getSystemStateFromQueue();
    //Serial.println("system state works");
    uint16_t txTimeStamp = (uint16_t)(millis() - lastTxTime);
    lastTxTime = millis();
    data.timestamp = txTimeStamp;
    data.temperature_chip = temperatureController.getChipTemperature();
    //Serial.println("chip temp works");
    data.temperature_battery = temperatureController.getTemperatureOfSensors()[1];
    //Serial.println("batt works");
    data.temperature_engine = temperatureController.getTemperatureOfSensors()[0];
    //Serial.println("Engine works");
    data.packet_number = packet_number;
    
    data.battery_percentage = electrics.getBatteryPercentage();
    data.battery_voltage = electrics.getBatteryVoltage();

    Serial.print("Yaw: ");
    Serial.println(data.euler);

    com.saveDataForSDBuffered(data);
    if(millis() - lastWriteTime > storing_interval) {
    
      com.writeBufferToSD();
      lastWriteTime = millis();
    }
    delay(10);

    xQueueOverwrite(sensorQueue, &data);
    
    vTaskDelay(1);

  }

}

void communicationTask(void* pvParameters) {
  DataToMaster_complete data_to_master;

  DataToMaster_P1 p1;
  DataToMaster_P2 p2;
  DataToMaster_P3 p3;


  while(true) {  
    if(xQueueReceive(sensorQueue, &data_to_master, portMAX_DELAY)) {

      
      p1.status = data_to_master.status;
      p1.drive = data_to_master.drive;
      p1.temp_engine = data_to_master.temperature_engine;
      p1.temp_battery = data_to_master.temperature_battery;
      p1.temp_chip = data_to_master.temperature_chip;

      com.sendDataPacketToMaster(1, p1, sizeof(p1));

      p2.ax = data_to_master.lin_accel_x;
      p2.ay = data_to_master.lin_accel_y;
      p2.yaw = data_to_master.euler;
      p2.gyro_z = data_to_master.gyro_z;

      com.sendDataPacketToMaster(2, p2, sizeof(p2));

      p3.voltage = data_to_master.voltage;
      p3.current = data_to_master.current;

      p3.battery_voltage = data_to_master.battery_voltage;
      p3.battery_percentage = data_to_master.battery_percentage;

      com.sendDataPacketToMaster(3, p3, sizeof(p3));

      com.increase_packet_counter();

    }

    vTaskDelay(pdMS_TO_TICKS(5));
  }

}


void setup() {


  Serial.begin(115200);
 
  Serial.print("\033[2J");  // Clear Screen
  Serial.print("\033[H");   // Cursor nach Home (oben links)
  Serial.println("Do you want to start the Self-Checkup-Mode? Y/N");
  
  unsigned long startTime = millis();
  bool checkup_finished = false;
  /*
  while (millis() - startTime < 10000 || checkup_finished == true) {
    if (Serial.available()) {
      String input = Serial.readStringUntil('\n');
      input.trim();
      Serial.println(input);

      if (input.equalsIgnoreCase("Y")) {
        Serial.println("Starting Self-Checkup-Mode...");
        diagnostics.startDiagnostics();
        continue;
  
        
      }
      if(input.equalsIgnoreCase("q")) ESP.restart(); // Abbruch, Eingabe erhalten
    }
  }
  */
  Serial.println("[============================]");
  Serial.println("Starting Operating-Mode...");

  // Queue für 1 Datensatz (Overwrite sorgt dafür, dass immer neuester Wert)
  sensorQueue = xQueueCreate(1, sizeof(DataToMaster_complete));

  //sämtliche inits aller Klassen
  com.initRadio(CE_PIN, CSN_PIN, 76, radioAutoAck, &diagnostics);
  com.initSD(SD_PIN);
  com.openSDFile(SD_FILE_NAME);
  Wire.begin(SDA_PIN, SCL_PIN);
  Wire.setClock(100000);
  electrics.initINA(&Wire, &Serial, &diagnostics);
  electrics.initMAX(&Wire, &diagnostics);
  speedSensor.init(&Serial, HALL_SENSOR_PIN, &diagnostics);
  temperatureController.init(WIRE_PIN);
  gyro_manager.begin(&Wire, &diagnostics);
  Serial.println("INIT COMPLETED");
  // Tasks auf zwei Cores starten
  
  xTaskCreatePinnedToCore(sensorTask, "SensorTask", 8192, NULL, 1, NULL, 1); // Core 1
  xTaskCreatePinnedToCore(communicationTask, "CommTask", 4096, NULL, 1, NULL, 0);     // Core 0
  
  
}

void loop() {
}



