#pragma once

#include <Arduino.h>
#include <SPI.h>
#include <SD.h>
#include "RF24.h"
#include "Diagnostics.h"

class Diagnostics; 

#pragma pack(push, 1)
struct DataToMaster_complete {
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
  uint8_t battery_voltage;
  uint8_t battery_percentage;

};
#pragma pack(pop)

#pragma pack(push, 1)
struct DataToMasterHeader {
  uint32_t seq;
  uint16_t timestamp; 
  uint8_t type; //(serves as an package identifier 1,2,3 for the packages)
};
#pragma pack(pop)

#pragma pack(push, 1)
struct DataToMaster_P1 {
  uint8_t status;
  float drive;
  float temp_engine;
  float temp_battery;
  float temp_chip;
};

struct DataToMaster_P2 {
  float ax;
  float ay;
  float yaw;
  float gyro_z;
};

struct DataToMaster_P3 {
  float voltage;
  float current;
  float battery_voltage;
  float battery_percentage;
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
  uint32_t packet_number_counter = 0; 
  unsigned long last_flush_time = 0;
  const unsigned long FLUSH_INTERVAL = 30000;

  Diagnostics* diagnostics;

  DataToMasterHeader hdr;

  void addMakersToData(const DataToMaster_complete& data, uint8_t* buffer, size_t packet_size);
  void convertBytesToStruct(DataToMaster_complete& data, const uint8_t* buffer, size_t length);
  bool checkDataIntegrity(uint8_t* buffer, size_t length);
  size_t extractDatapacketAsBytestring(uint8_t identifier, uint8_t* buffer, DataToMaster_complete* data);


  public:
  Communication(HardwareSerial& serial) : m_serial(serial) {}; 
  bool initRadio(int ce_pin, int csn_pin, int channel, bool autoack, Diagnostics* _diagnostics);
  
  bool initSD(int sd_pin);
  bool checkRadioConnection();
  bool checkRadioSignalstrength();
  bool checkWritingToSD();
  void removeSDFile(String file);
  void saveDataForSDBuffered(DataToMaster_complete data);
  void sendDataToMaster(DataToMaster_complete data);
  bool sendSimpleData();
  bool receiveSimpleData(uint8_t* buffer, uint8_t& len);  

  void sendDataToSlave(DataFromMaster &data);

  bool receiveDataFromSlaveDynPayload(DataToMaster_complete &data);
  bool receiveDataFromMasterDynPayload(DataFromMaster &data);

  bool receiveDataFromSlaveNoDynPayload(DataToMaster_complete &data);
  bool receiveDataFromMasterNoDynPayload(DataFromMaster &data);

  uint16_t generateCrc16(const uint8_t *data, size_t len);

  void appendHash(uint8_t *buffer, size_t packet_size);

  bool openSDFile(String file_name);
  void writeBufferToSD();
  void closeSDFile();

  uint16_t crc16(const uint8_t *data, size_t len);

  template<typename T> 
  bool sendDataPacketToMaster(uint8_t type, const T& payload, size_t len) {
    uint8_t buf[32];

    hdr.seq = packet_number_counter;
    hdr.timestamp = millis();
    hdr.type = type; 

    memcpy(buf, &hdr, sizeof(DataToMasterHeader));
    memcpy(buf + sizeof(DataToMasterHeader), &payload, len);

    size_t total_len = sizeof(DataToMasterHeader) + len; 

    uint16_t crc = crc16(buf, total_len);

    buf[total_len] = crc & 0xFF;
    buf[total_len +1] = crc >> 8;

    return radio->write(buf, total_len + 2);

    
  }

  void increase_packet_counter() {
    packet_number_counter++;
  }

};