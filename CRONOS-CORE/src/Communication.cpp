#include "Communication.h"

bool Communication::initRadio(HardwareSerial* serial, int _ce_pin, int _csn_pin, int module, Diagnostics* _diagnostics) {
  m_serial = serial;
  diagnostics = _diagnostics;

  ce_pin = _ce_pin;
  csn_pin = _csn_pin;

  radio = new RF24(ce_pin, csn_pin);

  if (!radio->begin()) {
    Serial.println(F("[ERROR] Could not initialize Radiotransmitter!"));
    diagnostics->addSystemStateToQueue(RADIO_INIT_FAILED);
    return false;
  }

  radio->setPALevel(RF24_PA_HIGH);  // starke, aber sichere Sendeleistung
  radio->setDataRate(RF24_1MBPS);   // stabiler als 2 Mbps
  radio->setChannel(90);            // außerhalb üblicher WLAN-Kanäle
  radio->setAutoAck(false);         
  radio->enableDynamicPayloads();   // nur nötige Bytes senden
  radio->setRetries(3, 15);         // 3 Versuche, max. Wartezeit

  if (module == 1) {
    radio->openWritingPipe(link_address);
    radio->openReadingPipe(1, unit_address);
    radio->startListening();
  } else {
    radio->openWritingPipe(unit_address);
    radio->openReadingPipe(1, link_address);
    radio->startListening();
  }

  return true;
}


bool Communication::initSD(int sd_pin) {
    bool status = SD.begin(sd_pin);

    if (!status) {
      m_serial->println("[ERROR] Failed to initialize SD-Card!");
      diagnostics->addSystemStateToQueue(SD_INIT_FAILED);
    }

  return status;

}

bool Communication::checkRadioConnection() {
  const char data[] = "Ping";

  if (radio->write(data, sizeof(data))) {
    return true;
  } else {
    diagnostics->addSystemStateToQueue(NO_RADIO_CONNECTION);
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
    diagnostics->addSystemStateToQueue(SD_FILE_OPEN_FAILED);
  }
  return file;
}

void Communication::saveDataForSDBuffered(TransmissionData data) {
  char buffer[256];
  char buf_drive[10], buf_acc_x[10], buf_acc_y[10], buf_euler[10], buf_gyro_z[10], buf_volt[10], buf_curr[10];


  //Arduino libaries do not support floats with the snprintf, so a work-around is needed
  //with dtostrf a double (float) is converted to an array of chars (string)
  //dtostrf(input, with, decimal place, output) -> width -> total String length (can be longer, will be filled automatically with spaces)
    dtostrf(data.drive, 6, 2, buf_drive);
    dtostrf(data.lin_accel_x, 4, 2, buf_acc_x);
    dtostrf(data.lin_accel_y, 4, 2, buf_acc_y);
    dtostrf(data.euler, 5, 2, buf_euler);
    dtostrf(data.gyro_z, 5, 2, buf_gyro_z);
    dtostrf(data.voltage, 6, 2, buf_volt);
    dtostrf(data.current, 6, 2, buf_curr);

  uint16_t timestamp = (uint16_t)(millis() & 0xFFFF);

    snprintf(buffer, sizeof(buffer),
             "<%u;%u;%u;%u;%u;%s;%s;%s;%s;%s;%s;%s;%u;%u>",
             timestamp,                  // Zeitstempel
             data.status,
             data.temperature_engine,
             data.temperature_battery,
             data.temperature_chip,
             buf_drive,
             buf_acc_x,
             buf_acc_y,
             buf_euler,
             buf_gyro_z,
             buf_volt,
             buf_curr,
             data.temperature_4,
             data.temperature_5
    );

  dataBuffer += String(buffer);


}

void Communication::writeBufferToSD() {
  if (dataBuffer.length() == 0) return;

  if (!file) {
    m_serial->println("[ERROR] File on SD not Open!");
    diagnostics->addSystemStateToQueue(SD_FILE_NOT_OPEN);
    return;
  }

  if (file.print(dataBuffer) == 0) {
    m_serial->println("[ERROR] Could not write to SD!");
    diagnostics->addSystemStateToQueue(SD_WRITE_FAILED);

  }
  
  file.flush();
  dataBuffer = "";
}

bool Communication::checkWritingToSD() {
  if (file.print("checkup")){
    return true;
  } else {
    diagnostics->addSystemStateToQueue(SD_WRITE_FAILED);
    return false;
  }
}

void Communication::removeSDFile(String file) {
  SD.remove(file);
}

void Communication::closeSDFile() {
  file.close();
  
}

size_t Communication::extractDatapacketAsBytestring(uint8_t identifier, uint8_t* buffer, TransmissionData* data) {
    int pos = 1; //0 is later used für markers
    buffer[pos++] = identifier;
    buffer[pos++] = packet_number_counter; 
    packet_number_counter++;
    // Timestamp (2 Bytes)
    uint16_t ts = (uint16_t)(millis() & 0xFFFF);
    buffer[pos++] = ts & 0xFF;
    buffer[pos++] = (ts >> 8) & 0xFF;

    switch(identifier) {
      case 0:
        buffer[pos++] = data->status;
        buffer[pos++] = data->temperature_battery;
        buffer[pos++] = data->temperature_chip;
        buffer[pos++] = data->temperature_engine;
        buffer[pos++] = data->temperature_4;
        buffer[pos++] = data->temperature_5;
        memcpy(&buffer[pos], &data->current, sizeof(data->current));
        pos += sizeof(data->current);
        memcpy(&buffer[pos], &data->voltage, sizeof(data->voltage));
        pos += sizeof(data->voltage);
        memcpy(&buffer[pos], &data->drive, sizeof(data->drive));
        pos += sizeof(data->drive);
        break; 
      case 2: 
        memcpy(&buffer[pos], &data->lin_accel_x, sizeof(data->lin_accel_x));
        pos += sizeof(data->lin_accel_x);
        memcpy(&buffer[pos], &data->lin_accel_y, sizeof(data->lin_accel_y));
        pos += sizeof(data->lin_accel_y);
        memcpy(&buffer[pos], &data->gyro_z, sizeof(data->gyro_z));
        pos += sizeof(data->gyro_z);
        memcpy(&buffer[pos], &data->euler, sizeof(data->euler));
        pos += sizeof(data->euler);
        break;
    }
    return pos;

}; 



void Communication::sendData(TransmissionData data) {
  
  radio->stopListening();

  uint8_t buffer[64]; 
  size_t packet_size;

  //Datapacket 1
  packet_size = extractDatapacketAsBytestring(0, buffer, &data);
  addMakersToData(data, buffer, packet_size);
  if (!radio->write(buffer, packet_size +1)) {
    m_serial->println("[ERROR] Could not send data over radio!");
    diagnostics->addSystemStateToQueue(DATA_TRANSMISSION_FAILED);
  }
  delay(5);
  //Datapacket 2
  packet_size = extractDatapacketAsBytestring(2, buffer, &data);
  addMakersToData(data, buffer, packet_size);

  if (!radio->write(buffer, packet_size +1)) {
    m_serial->println("[ERROR] Could not send data over radio!");
    diagnostics->addSystemStateToQueue(DATA_TRANSMISSION_FAILED);
  }
  delay(5);
}

bool Communication::receiveData(TransmissionData &data) {
    radio->startListening();

    if (radio->available()) {
        uint8_t buffer[64];   // Maximalgröße

        // Erstes Byte für Startmarker, zweites für Identifier
        radio->read(buffer, sizeof(buffer)); 

        // Identifier auslesen
        uint8_t identifier = buffer[1];

        // Paketgröße anhand Identifier bestimmen (inklusive Start- und Endmarker)
        size_t expected_size = 0;
        switch(identifier) {
            case 0:
                expected_size = 1  /*<*/ + 1 /*identifier*/ + 1 /*packet_number*/
                                + 2 /*timestamp*/ + 6 /*uint8_t Felder*/
                                + sizeof(float)*3 /*current, voltage, drive*/
                                + 2 /*temperature_4 & 5*/ 
                                + 1 /*>*/; // Endmarker
                break;
            case 2:
                expected_size = 1  /*<*/ + 1 /*identifier*/ + 1 /*packet_number*/
                                + 2 /*timestamp*/ + sizeof(float)*4 /*lin_acc_x, lin_acc_y, gyro_z, euler*/
                                + 1 /*>*/;
                break;
            default:
                m_serial->println("[ERROR] Unknown identifier!");
                return false;
        }

        // Prüfen, ob Länge passt
        if (expected_size > sizeof(buffer)) {
            m_serial->println("[ERROR] Packet too large!");
            return false;
        }

        // Start- und Endmarker prüfen
        if(!checkDataIntegrity(buffer, expected_size)) {
            m_serial->println("[ERROR] Invalid start or end marker!");
            return false;
        }

        // Bytes ins Struct konvertieren
        convertBytesToStruct(data, buffer, expected_size);

        return true;
    }

    return false; // keine Daten verfügbar
}


void Communication::addMakersToData(const TransmissionData& data, uint8_t* buffer, size_t packet_size) {
  buffer[0] = '<';
  buffer[packet_size] = '>';
}

void Communication::convertBytesToStruct(TransmissionData& data, const uint8_t* buffer, size_t length) {
  int pos = 2; // buffer[0]='<' , buffer[1]=identifier

  uint8_t identifier = buffer[1];

  data.packet_number = buffer[pos++];

  data.timestamp = buffer[pos++];
  data.timestamp |= (uint16_t)buffer[pos++] << 8;

  switch(identifier) {

      case 0:
          data.status = buffer[pos++];
          data.temperature_battery = buffer[pos++];
          data.temperature_chip = buffer[pos++];
          data.temperature_engine = buffer[pos++];
          data.temperature_4 = buffer[pos++];
          data.temperature_5 = buffer[pos++];

          memcpy(&data.current, &buffer[pos], sizeof(data.current));
          pos += sizeof(data.current);

          memcpy(&data.voltage, &buffer[pos], sizeof(data.voltage));
          pos += sizeof(data.voltage);

          memcpy(&data.drive, &buffer[pos], sizeof(data.drive));
          pos += sizeof(data.drive);
          break;

      case 2:
          memcpy(&data.lin_accel_x, &buffer[pos], sizeof(data.lin_accel_x));
          pos += sizeof(data.lin_accel_x);

          memcpy(&data.lin_accel_y, &buffer[pos], sizeof(data.lin_accel_y));
          pos += sizeof(data.lin_accel_y);

          memcpy(&data.gyro_z, &buffer[pos], sizeof(data.gyro_z));
          pos += sizeof(data.gyro_z);

          memcpy(&data.euler, &buffer[pos], sizeof(data.euler));
          pos += sizeof(data.euler);
          break;
  }
}

bool Communication::checkDataIntegrity(uint8_t* buffer, size_t length) {
  if (length == 0) return false;
  if (buffer[0] == '<' && buffer[length - 1] == '>') {
    return true;
  }
  return false;
}
