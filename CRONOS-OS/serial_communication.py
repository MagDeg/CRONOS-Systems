import serial
import serial.tools.list_ports
from data_struct import *
import struct

class SerialCommunication:
    _port = None
    _baudrate = 9600
    _timeout = 1
    _serial = None

    def __init__(self, port, baudrate, timeout):
        self._port = port
        self._baudrate = baudrate
        self._timeout = timeout
        self._serial = serial.Serial(port, baudrate, timeout=timeout)

    def _refresh_serial(self):
        self._serial = serial.Serial(self._port, self._baudrate, timeout=self._timeout)

    def change_baudrate(self, baudrate):
        self._baudrate = baudrate
        self._refresh_serial()

    def change_timeout(self, timeout):
        self._timeout = timeout
        self._refresh_serial()

    def change_port(self, port):
        self._port = port
        self._refresh_serial()

    def get_availabe_ports(self):
        return serial.tools.list_ports.comports()

    def _read_serial(self):
        # only reading exact size of one package -> marker + data + marker
        packet_size = 1 + struct.calcsize('<BBfBBBfff') + 1
        buffer = bytearray()
        while True:

            byte = self._serial.read(1)
            if not byte:
                continue

            buffer += byte

            while buffer and buffer[0] != ord('<'):
                buffer.pop(0)

            if len(buffer) == packet_size and buffer[-1] == ord('>'):
                return bytes(buffer)

            if len(buffer) > packet_size:
                buffer.clear()

    def get_serial_data(self):
        data_packet = self._read_serial()
        return self._decode_data(data_packet)

    def _code_data(self, data: TransmittedData) -> bytes:
        payload = struct.pack(
            '<BBfBBBfff',
            data.identifier,
            data.status,
            data.drive,
            data.temperature_engine,
            data.temperature_battery,
            data.temperature_chip,
            data.acceleration,
            data.voltage,
            data.current
        )
        packet = b'<' + payload + b'>'
        return packet

    def _decode_data(self, data_packet: bytes):
        # simply removing marker
        payload = data_packet[1:-1]
        # covert bytes to values (<...little endian (fist coded element, will be the first to decode), B...unsigned char, f...float)
        unpacked = struct.unpack('<BBfBBBfff', payload)
        # with the * all values will be inserted into the function, without specifically naming them
        return TransmittedData(*unpacked)

    def _send_data(self,data):
        packet = self._code_data(data)
        self._serial.write(packet)
        self._serial.flush()


