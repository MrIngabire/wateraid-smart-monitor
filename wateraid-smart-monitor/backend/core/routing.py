from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/telemetry/$', consumers.TelemetryConsumer.as_asgi()),
    re_path(r'ws/alerts/$', consumers.AlertsConsumer.as_asgi()),
]