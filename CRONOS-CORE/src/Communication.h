#pragma once

#include <Arduino.h>
#include <SPI.h>
#include <SD.h>
#include "RF24.h"
#include "Diagnostics.h"

class Diagnostics; 

#pragma pack(push, 1)
struct DataToMaster {
  //uint8_t identifier;
  //Just for received Data

  uint8_t packet_number;
  uint16_t timestamp; 
  //-----------------------
  uint8_t status;
  float drive;
  uint8_t temperature_engine;
  uint8_t temperature_battery;
  uint8_t temperature_chip;
  float lin_accel_x;
  float lin_accel_y;
  float euler;
  float gyro_z;
  float voltage;
  float current;
  uint8_t temperature_5;
  uint8_t temperature_4;

};
#pragma pack(pop)

//pack to ensure, there is no alignment from the processor which would result in manipulation the data
#pragma pack(push, 1)
struct DataFromMaster {
  uint8_t identifier;
  uint8_t deactivateListeningToMaster;
  uint8_t startDiagnostic;
  uint8_t activateDriftCorrection;
  int32_t intervalForStoringDataOnSD;
};
#pragma pack(pop)


class Communication {
  protected:
  HardwareSerial& m_serial;
  //data to access files on sd
  File file;
  int ce_pin;
  int csn_pin;
  RF24* radio;
  uint8_t unit_address[6] = {'T','X','1','2','3',0};
  uint8_t link_address[6] = {'R','X','1','2','3',0};
  String dataBuffer;
  uint8_t packet_number_counter = 0; 

  Diagnostics* diagnostics;

  void addMakersToData(const DataToMaster& data, uint8_t* buffer, size_t packet_size);
  void convertBytesToStruct(DataToMaster& data, const uint8_t* buffer, size_t length);
  bool checkDataIntegrity(uint8_t* buffer, size_t length);
  size_t extractDatapacketAsBytestring(uint8_t identifier, uint8_t* buffer, DataToMaster* data);


  public:
  Communication(HardwareSerial& serial) : m_serial(serial) {}; 
  bool initRadio(int ce_pin, int csn_pin, int module, Diagnostics* _diagnostics, bool auto_ack = false);
  
  //TODO: Implement Functions
  void startAsReceiver();
  void startAsSender();
  
  bool initSD(int sd_pin);
  bool checkRadioConnection();
  bool checkRadioSignalstrength();
  bool checkWritingToSD();
  void removeSDFile(String file);
  void saveDataForSDBuffered(DataToMaster data);
  void sendDataToMaster(DataToMaster data);
  
  //TODO: IMPLEMENT SEND TO SLAVE
  void sendDataToSlave(DataFromMaster &data);

  bool receiveDataFromSlaveDynPayload(DataToMaster &data);
  bool receiveDataFromMasterDynPayload(DataFromMaster &data);

  bool receiveDataFromSlaveNoDynPayload(DataToMaster &data);
  bool receiveDataFromMasterNoDynPayload(DataFromMaster &data);

  uint16_t generateCrc16(const uint8_t *data, size_t len);

  void appendHash(uint8_t *buffer, size_t packet_size);

  bool openSDFile(String file_name);
  void writeBufferToSD();
  void closeSDFile();

};