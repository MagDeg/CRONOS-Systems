#include "Communication.h"

bool Communication::initRadio(HardwareSerial* serial, int ce_pin, int csn_pin) {
  m_serial = serial;

  CE_PIN = ce_pin;
  CSN_PIN = csn_pin;

  radio = new RF24(ce_pin, csn_pin);

  if (!radio->begin()) {
    Serial.println(F("[ERROR] Could not initialize Radiotransmitter!"));
    return false;
  }

  radio->setPALevel(RF24_PA_HIGH);  // starke, aber sichere Sendeleistung
  radio->setDataRate(RF24_1MBPS);   // stabiler als 2 Mbps
  radio->setChannel(90);            // außerhalb üblicher WLAN-Kanäle
  radio->setAutoAck(true);          // Bestätigungen an
  radio->enableDynamicPayloads();   // nur nötige Bytes senden
  radio->setRetries(3, 15);         // 3 Versuche, max. Wartezeit

  radio->openWritingPipe(address);
  radio->stopListening();

  return true;
}

bool Communication::initSD(int sd_pin) {
    bool status = SD.begin(sd_pin);

    if (!status) {
    m_serial->println("[ERROR] Failed to initialize SD-Card!");
  }

  return status;

}

bool Communication::checkRadioConnection() {
  const char data[] = "Ping";

  if (radio->write(data, sizeof(data))) {
    return true;
  } else {
    return false;
  }
}

bool Communication::checkRadioSignalstrength() {
  return radio->testRPD();
}


bool Communication::openSDFile(String file_name) {
  file = SD.open(file_name, FILE_WRITE);
  if (!file) {
    m_serial->println("[ERROR] There was an error while reading file!");
  }
  return file;
}

void Communication::saveDataForSDBuffered(TransmissionData data) {
  char buffer[256];
  char buf_drive[10], buf_acc[10], buf_volt[10], buf_curr[10];


  //Arduino libaries do not support floats with the snprintf, so a work-around is needed
  //with dtostrf a double (float) is converted to an array of chars (string)
  //dtostrf(input, with, decimal place, output) -> width -> total String length (can be longer, will be filled automatically with spaces)
  dtostrf(data.drive, 6, 2, buf_drive);
  dtostrf(data.acceleration, 4, 2, buf_acc);
  dtostrf(data.voltage, 6, 2, buf_volt);
  dtostrf(data.current, 6, 2, buf_curr);

  snprintf(buffer, sizeof(buffer), "<%u;%u;%s;%u;%u;%u;%s;%s;%s>",
           data.identifier,
           data.status,
           buf_drive,
           data.temperature_engine,
           data.temperature_battery,
           data.temperature_chip,
           buf_acc,
           buf_volt,
           buf_curr);

  dataBuffer += String(buffer);


}

void Communication::writeBufferToSD() {
  if (dataBuffer.length() == 0) return;

  if (!file) {
    m_serial->println("[ERROR] File on SD not Open!");
    return;
  }

  if (file.print(dataBuffer) == 0) {
    m_serial->println("[ERROR] Could not write to SD!");
  }
  
  file.flush();
  dataBuffer = "";
}

bool Communication::checkWritingToSD() {
  if (file.print("checkup")){
    return true;
  } else {
    return false;
  }
}

void Communication::removeSDFile(String file) {
  SD.remove(file);
}

void Communication::closeSDFile() {
  file.close();
  
}

void Communication::sendData(TransmissionData data) {
  uint8_t buffer[sizeof(TransmissionData) + 2];

  convertDataToByteWithMarkers(data, buffer);

  if (!radio->write(&buffer, sizeof(buffer))) {
    m_serial->println("[ERROR] Could not send data over radio!");
  }

  //just for Debugging
  for (size_t i = 0; i < sizeof(buffer); i++) {
    if (i == 1 || i == 7 || i == 8 || i == 9 || i == 2) {
      m_serial->print((uint8_t)buffer[i]);
    }
    if (i == 0 || i == sizeof(buffer) - 1) {
      m_serial->print((char)buffer[i]);
    } else {
      m_serial->print(";");
    }
  }
  m_serial->println();

  TransmissionData dataRecovered;

  convertBytesToStruct(dataRecovered, buffer, sizeof(buffer));

  m_serial->println(dataRecovered.current);
}


void Communication::convertDataToByteWithMarkers(const TransmissionData& data, uint8_t* buffer) {
  buffer[0] = '<';
  memcpy(buffer + 1, &data, sizeof(TransmissionData));
  buffer[sizeof(TransmissionData) + 1] = '>';
}

void Communication::convertBytesToStruct(TransmissionData& data, const uint8_t* buffer, size_t length) {
  //for security to prevent errors
  if (length < sizeof(TransmissionData) + 2) return;

  memcpy(&data, buffer + 1, sizeof(TransmissionData));
}

bool Communication::checkDataIntegrity(uint8_t* buffer, size_t length) {
  if (length == 0) return false;
  if (buffer[0] == '<' && buffer[length - 1] == '>') {
    return true;
  }
  return false;
}
