import threading
import time
import serial

from data_structs.received_data import TransmittedData


class SerialReader:
    def __init__(self, port, baudrate=115200, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout

        self.serial = None
        self.thread = None
        self.running = False

    def start(self):
        self.serial = serial.Serial(
            port = self.port,
            baudrate = self.baudrate,
            timeout = self.timeout
        )
        self.running = True
        # target is the function, that will be called continually in the background/second process
        # daemon = True -> thread is killed automatically if mein program is terminated
        self.thread = threading.Thread(target=self._read_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        if self.serial and self.serial.is_open:
            self.serial.close()

    def _read_loop(self):
        while self.running:
            if self.serial.in_waiting:
                # errors='ignore' -> data that could not be decoded will be ignored
                line = self.serial.readline().decode(errors='ignore').strip()

                if line:
                    self.on_data(line)
            time.sleep(0.01)

    def on_data(self, data: str, transmitted_data: TransmittedData):
        #data is accessible as a string
        split_data = data.split(';')

        if len(split_data) != 15:
            return

        try:
            transmitted_data.previous_packet_number = transmitted_data.packet_number
            transmitted_data.packet_number = int(split_data[0])
            transmitted_data.previous_packet_timestamp = transmitted_data.timestamp
            transmitted_data.timestamp = int(split_data[1])
            transmitted_data.status = int(split_data[2])

            transmitted_data.drive = float(split_data[3])

            transmitted_data.temperature_engine = int(split_data[4])
            transmitted_data.temperature_battery = int(split_data[5])
            transmitted_data.temperature_chip = int(split_data[6])

            transmitted_data.lin_accel_x = float(split_data[7])
            transmitted_data.lin_accel_y = float(split_data[8])
            transmitted_data.euler = float(split_data[9])
            transmitted_data.gyro_z = float(split_data[10])

            transmitted_data.voltage = float(split_data[11])
            transmitted_data.current = float(split_data[12])

            transmitted_data.temperature_5 = int(split_data[13])
            transmitted_data.temperature_4 = int(split_data[14])
        except:
            return

        pass