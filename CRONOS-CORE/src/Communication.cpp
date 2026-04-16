#include "Communication.h"

bool Communication::initRadio(int _ce_pin, int _csn_pin, int module, Diagnostics* _diagnostics, bool auto_ack) {
  diagnostics = _diagnostics;

  ce_pin = _ce_pin;
  csn_pin = _csn_pin;

  radio = new RF24(ce_pin, csn_pin);

  if (!radio->begin()) {
    m_serial.println(F("[ERROR] Could not initialize Radiotransmitter!"));
    diagnostics->addSystemStateToQueue(RADIO_INIT_FAILED);
    return false;
  }


  radio->setPALevel(RF24_PA_HIGH);  // starke, aber sichere Sendeleistung
  radio->setDataRate(RF24_1MBPS);   // stabiler als 2 Mbps
  radio->setChannel(90);            // außerhalb üblicher WLAN-Kanäle
  radio->setAutoAck(auto_ack); //if true, it means, if data is send to that device, there is a confimation of receiving form this device to sender        
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
      m_serial.println("[ERROR] Failed to initialize SD-Card!");
      diagnostics->addSystemStateToQueue(SD_INIT_FAILED);
    }

  return status;

}

bool Communication::checkRadioConnection() {
   const char data[] = "Ping"; 
   radio->stopListening(); 
   delay(5); 
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
  file = SD.open(file_name.c_str(), FILE_WRITE);
  if (!file) {
    m_serial.println("[ERROR] There was an error while reading file!");
    diagnostics->addSystemStateToQueue(SD_FILE_OPEN_FAILED);
    return false;
  }
  return file;
}

void Communication::saveDataForSDBuffered(DataToMaster data) {
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
    m_serial.println("[ERROR] File on SD not Open!");
    diagnostics->addSystemStateToQueue(SD_FILE_NOT_OPEN);
    return;
  }

  if (file.print(dataBuffer) == 0) {
    m_serial.println("[ERROR] Could not write to SD!");
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
  SD.remove(file.c_str());
}

void Communication::closeSDFile() {
  file.close();
  
}

size_t Communication::extractDatapacketAsBytestring(uint8_t identifier, uint8_t* buffer, DataToMaster* data) {
    int pos = 0; 
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

uint16_t Communication::generateCrc16(const uint8_t *data, size_t len) {
  uint16_t crc = 0xFFFF;

  for (size_t i = 0; i < len; i++) {
    crc ^= (uint16_t)data[i];

    for (uint8_t j = 0; j < 8; j++) {
      if (crc & 1) crc = (crc >> 1) ^ 0xA001;
      else crc >>= 1;
    }
  }

  return crc;
}

void Communication::appendHash(uint8_t* buffer, size_t packet_size) {
  // hash nur über Daten (ohne buffer[0])
  uint16_t crc = generateCrc16(buffer, packet_size);

  buffer[packet_size]     = (uint8_t)(crc & 0xFF);
  buffer[packet_size + 1] = (uint8_t)(crc >> 8);
}

void Communication::sendDataToSlave(DataFromMaster &data) {
  radio->stopListening();

  uint8_t buffer[64];
  size_t packet_size;
  uint8_t pos = 0; 
  buffer[pos++] = data.identifier;
  buffer[pos++] = data.deactivateListeningToMaster;
  buffer[pos++] = data.startDiagnostic;
  buffer[pos++] = data.activateDriftCorrection;
  memcpy(&buffer[pos], &data.intervalForStoringDataOnSD, sizeof(data.intervalForStoringDataOnSD));
  pos += sizeof(data.intervalForStoringDataOnSD); 

  packet_size = pos;
  appendHash(buffer, packet_size); 
  if (!radio->write(buffer, packet_size+2)) {
    m_serial.println("[ERROR] Could not send data over radio!");
  }



}

void Communication::sendDataToMaster(DataToMaster data) {
  
  radio->stopListening();

  uint8_t buffer[64]; 
  size_t packet_size;

  //Datapacket 1
  packet_size = extractDatapacketAsBytestring(0, buffer, &data);

  appendHash(buffer, packet_size);
  radio->write(buffer, packet_size+2);
  delay(5);


  //Datapacket 2
  packet_size = extractDatapacketAsBytestring(2, buffer, &data);
  appendHash(buffer, packet_size);

  radio->write(buffer, packet_size+2);
  delay(5);
}

bool Communication::receiveDataFromMasterNoDynPayload(DataFromMaster &data) {
  radio->startListening();

  if (!radio->available()) return false;

  uint8_t buffer[64];

  radio->read(buffer, sizeof(DataFromMaster)+2);

  if(!checkDataIntegrity(buffer, sizeof(DataFromMaster)+2)) {
    return false;
  }

  memcpy(&data, buffer, sizeof(DataFromMaster));
  return true; 
}

//NOTE: IF THERE A ANY ERROR WITH SENDING, REMOVE THE DYNAMIC PAYLOAD!!
//TODO: IMPLEMENT HASH VALUE AS ADDITIONAL INTEGRITY CHECK (OPTIONAL)
bool Communication::receiveDataFromMasterDynPayload(DataFromMaster &data) {

  radio->startListening();

  if (!radio->available()) return false;

  uint8_t buffer[64];

  uint8_t len = radio->getDynamicPayloadSize();
  radio->read(buffer, len);

  if (len != sizeof(DataFromMaster) + 2) return false;

  // Integritätscheck (Marker + ggf. weitere Regeln)
  if (!checkDataIntegrity(buffer, len)) {
    return false;
  }

  // Payload extrahieren
  memcpy(&data, buffer, sizeof(DataFromMaster));

  return true;
}

bool Communication::receiveDataFromSlaveNoDynPayload(DataToMaster &data) {
  radio->startListening();
  if(!radio->available()) {
    return false;
  }
  uint8_t buffer[64];
  radio->read(buffer, sizeof(buffer));

  uint8_t identifier = buffer[0];
  size_t expected_packet_size = 0;
  switch(identifier){
    case 0:
        expected_packet_size = 1 /*identifier*/ + 1 /*packet_number*/
                        + 2 /*timestamp*/ + 6 /*uint8_t Felder*/
                        + sizeof(float)*3 /*current, voltage, drive*/
                        + 2 /*temperature_4 & 5*/ 
                        + 2 /*crc16*/; 
        break;
    case 2:
        expected_packet_size = 1 /*identifier*/ + 1 /*packet_number*/
                        + 2 /*timestamp*/ + sizeof(float)*4 /*lin_acc_x, lin_acc_y, gyro_z, euler*/
                        + 2 /*crc16*/;
        break;
    default:
        m_serial.println("[ERROR] Unknown identifier!");
        return false;
  }
  if (!checkDataIntegrity(buffer, expected_packet_size)) {
    //Invalid Datapacket
    return false;
  }
  convertBytesToStruct(data, buffer, expected_packet_size-2);

  return true;
}

bool Communication::receiveDataFromSlaveDynPayload(DataToMaster &data) {
    radio->startListening();

    if (!radio->available()) return false;
    uint8_t buffer[64];   // Maximalgröße

    // 🔴 FIX: echte Payload-Länge verwenden
    uint8_t len = radio->getDynamicPayloadSize();
    // Sicherheitscheck
    if (len < 6 || len > sizeof(buffer)) return false;

    radio->read(buffer, len);

    // Identifier auslesen
    uint8_t identifier = buffer[0];

    // Paketgröße anhand Identifier bestimmen (inklusive Start- und Endmarker)
    size_t expected_size = 0;
    switch(identifier) {
        case 0:
            expected_size = 1 /*identifier*/ + 1 /*packet_number*/
                            + 2 /*timestamp*/ + 6 /*uint8_t Felder*/
                            + sizeof(float)*3 /*current, voltage, drive*/
                            + 2 /*temperature_4 & 5*/ 
                            + 2 /*crc16*/; 
            break;
        case 2:
            expected_size =  1 /*identifier*/ + 1 /*packet_number*/
                            + 2 /*timestamp*/ + sizeof(float)*4 /*lin_acc_x, lin_acc_y, gyro_z, euler*/
                            + 2 /*crc16*/;
            break;
        default:
            m_serial.println("[ERROR] Unknown identifier!");
            return false;
    }

    // Prüfen, ob Länge passt
    if(len < expected_size) return false; 

    // Start- und Endmarker prüfen
    if(!checkDataIntegrity(buffer, len)) {
        m_serial.println("[ERROR] Invalid start or end marker!");
        return false;
    }

    // Bytes ins Struct konvertieren
    convertBytesToStruct(data, buffer, len-2);

    return true;

}



void Communication::convertBytesToStruct(DataToMaster& data, const uint8_t* buffer, size_t length) {
  int pos = 0;

  uint8_t identifier = buffer[pos++];

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

  if (length < 6) return false;

  uint16_t received =
    buffer[length - 2] | (buffer[length - 1] << 8);

  uint16_t calc = generateCrc16(buffer, length - 2);

  return received == calc;
}

