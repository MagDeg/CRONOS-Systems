
from callbacks.page_routing import register_routing_callbacks
from callbacks.register_accel_dist_g import register_accel_gforce_distance_callbacks
from callbacks.register_connection import register_network_callbacks
from callbacks.register_gauge import register_gauge_callbacks
from callbacks.register_power import register_power_callbacks
from callbacks.register_speed_drive import register_speed_drive_callbacks
from callbacks.register_temperature import register_temperature_callbacks
from callbacks.register_time import register_time_panel_compact_callbacks


def register_callbacks(app):

    register_routing_callbacks(app)
    register_gauge_callbacks(app)
    register_power_callbacks(app)
    register_temperature_callbacks(app)
    register_speed_drive_callbacks(app)
    register_accel_gforce_distance_callbacks(app)
    register_network_callbacks(app)
    register_time_panel_compact_callbacks(app)
