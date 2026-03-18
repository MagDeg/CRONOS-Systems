#pragma once

#include <Arduino.h>
#include <SPI.h>
#include <SD.h>
#include "RF24.h"

struct EulerYaw {
  float yaw;
};

struct TransmissionData {
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


class Communication {
  protected:
  HardwareSerial* m_serial{};
  //data to access files on sd
  File file;
  int ce_pin;
  int csn_pin;
  RF24* radio;
  uint8_t address[6] = {'1','N','o','d','e', 0};
  String dataBuffer;
  uint8_t packet_number_counter = 0; 

  void addMakersToData(const TransmissionData& data, uint8_t* buffer, size_t packet_size);
  void convertBytesToStruct(TransmissionData& data, const uint8_t* buffer, size_t length);
  bool checkDataIntegrity(uint8_t* buffer, size_t length);
  size_t extractDatapacketAsBytestring(uint8_t identifier, uint8_t* buffer, TransmissionData* data);


  public:
  bool initRadio(HardwareSerial* serial, int ce_pin, int csn_pin);
  bool initSD(int sd_pin);
  bool checkRadioConnection();
  bool checkRadioSignalstrength();
  bool checkWritingToSD();
  void removeSDFile(String file);
  void saveDataForSDBuffered(TransmissionData data);
  void sendData(TransmissionData data);
  bool openSDFile(String file_name);
  void writeBufferToSD();
  void closeSDFile();

};