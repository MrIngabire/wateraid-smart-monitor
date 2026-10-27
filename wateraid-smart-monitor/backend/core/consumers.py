"""
WebSocket consumer for live IoT telemetry and AI alerts.
Broadcasts to all connected clients whenever new data arrives.
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class TelemetryConsumer(AsyncWebsocketConsumer):
    """Broadcasts sensor telemetry to all subscribers."""

    async def connect(self):
        self.group_name = 'telemetry'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        print(f'[WS] Client connected: {self.channel_name}')

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        print(f'[WS] Client disconnected: {self.channel_name}')

    async def receive(self, text_data):
        # Clients can send a "ping" to keep alive
        try:
            data = json.loads(text_data)
            if data.get('type') == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
        except json.JSONDecodeError:
            pass

    async def telemetry_update(self, event):
        """Handler for group_send messages."""
        await self.send(text_data=json.dumps(event['data']))


class AlertsConsumer(AsyncWebsocketConsumer):
    """Broadcasts AI alerts to all subscribers."""

    async def connect(self):
        self.group_name = 'alerts'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def alert_update(self, event):
        await self.send(text_data=json.dumps(event['data']))