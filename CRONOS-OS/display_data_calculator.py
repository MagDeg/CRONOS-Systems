from datetime import datetime
from math import sqrt

from data_structs.displayed_data import DisplayData
from data_structs.received_data import TransmittedData


class DisplayDataCalculator:
    start_time: datetime

    def __init__(self, data_out: DisplayData, data_in: TransmittedData):
        self.data_display = data_out
        self.data_transmitted = data_in

    def calculate_all_display_data(self):
        self.calculate_packet_loss()
        self.calculate_connection_state()
        self.calculate_elapsed_time()
        self.calculate_remaining_time()
        self.calculate_acceleration()
        self.calculate_g_force()
        self.calculate_velocity()
        self.calculate_power()
        self.calculate_delay()
        self.set_temperatures()
        self.set_voltage()
        self.set_current()
        self.set_list_with_errors()


    def set_voltage(self):
        self.data_display.voltage = self.data_transmitted.voltage

    def set_current(self):
        self.data_display.current = self.data_transmitted.current

    def set_temperatures(self):
        self.data_display.temperature_chip = self.data_transmitted.temperature_chip
        self.data_display.temperature_battery = self.data_transmitted.temperature_battery
        self.data_display.temperature_engine = self.data_transmitted.temperature_engine


    def calculate_power(self):
        self.data_display.power = self.data_transmitted.voltage * self.data_transmitted.current

    def calculate_delay(self):
        self.data_display.delay = self.data_transmitted.timestamp - self.data_transmitted.previous_packet_timestamp

    def calculate_packet_loss(self):
        expecter_packet_number = self.data_transmitted.packet_number - self.data_transmitted.previous_packet_number + 1
        received_packages = 1
        self.data_display.packet_loss = ((expecter_packet_number - received_packages) / expecter_packet_number) * 100

    def calculate_connection_state(self):
        if self.data_display.delay > 3000: # bigger than 3 seconds
            self.data_display.connection_state = False
        else:
            self.data_display.connection_state = True

    def calculate_acceleration(self):
        ax = self.data_transmitted.lin_accel_x
        ay = self.data_transmitted.lin_accel_y
        self.data_display.acceleration = sqrt(ax**2 + ay**2)

    def calculate_g_force(self):
        self.data_display.g_force = self.data_display.acceleration / 9.80665

    def calculate_velocity(self):
        pass

    def calculate_elapsed_time(self):
        pass

    def calculate_remaining_time(self):
        pass

    def get_current_time(self):
        pass

    def set_start_time(self, start_time):
        self.start_time = start_time

    def set_list_with_errors(self):
        match self.data_transmitted.status:
            #TODO: IMPLEMENT ERROR MESSAGE HANDLING
            case 1:
                pass
            case 2:
                pass
            case 3:
                pass
            case _:
                pass
