#pragma once

#include <Arduino.h>
#include <SPI.h>
#include <SD.h>
#include "RF24.h"

struct TransmissionData {
  uint8_t identifier;
  uint8_t status;
  float drive;
  uint8_t temperature_engine;
  uint8_t temperature_battery;
  uint8_t temperature_chip;
  float acceleration;
  float voltage;
  float current;
};


class Communication {
  protected:
  HardwareSerial* m_serial{};
  //data to access files on sd
  File file;
  int CE_PIN;
  int CSN_PIN;
  RF24* radio;
  uint8_t address[6] = "1Node";
  String dataBuffer;

  void convertDataToByteWithMarkers(const TransmissionData& data, uint8_t* buffer);
  void convertBytesToStruct(TransmissionData& data, const uint8_t* buffer, size_t length);
  bool checkDataIntegrity(uint8_t* buffer, size_t length);


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