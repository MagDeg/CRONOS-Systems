
from callbacks.page_routing import register_routing_callbacks
from callbacks.register_gauge import register_gauge_callbacks


def register_callbacks(app):

    register_routing_callbacks(app)
    register_gauge_callbacks(app)
