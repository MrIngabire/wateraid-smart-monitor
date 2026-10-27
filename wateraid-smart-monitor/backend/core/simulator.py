"""
Continuous IoT Sensor Simulator for WaterAid Smart Monitor
============================================================

Runs in a background thread while the Django server is alive.
Generates realistic sensor telemetry for every active pipeline sector:

- Normal operation ~97% of the time (flow ~ baseline, pressure ~ baseline)
- Anomalies ~3% of the time (leak, pressure drop, flow anomaly)
- Respects a daily usage curve (higher flow during daytime)
- Feeds the AI leak detector exactly as a real sensor would
- Auto-creates AIAlert rows when anomalies are detected
"""
import random
import threading
import time
import math
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import close_old_connections, transaction
from django.conf import settings

from core.models import PipelineSector, IoTSensorLog, AIAlert
from ai_engine.leak_detector import get_detector


class SensorSimulator:
    """Background thread that continuously generates IoT telemetry."""

    def __init__(self):
        self._thread = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self.running = False
        self.stats = {
            'ticks': 0,
            'logs_created': 0,
            'alerts_created': 0,
            'started_at': None,
            'last_tick_at': None,
        }

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def start(self, interval=None):
        """Start the simulator thread. Safe to call multiple times."""
        with self._lock:
            if self.running:
                print('[Simulator] Already running.')
                return False

            self._stop_event.clear()
            self._thread = threading.Thread(
                target=self._run,
                args=(interval,),
                daemon=True,
                name='SensorSimulator',
            )
            self._thread.start()
            self.running = True
            self.stats['started_at'] = timezone.now().isoformat()
            print('[Simulator] ▶ Started — generating telemetry every '
                  f'{interval or getattr(settings, "SIMULATE_INTERVAL", 5)}s')
            return True

    def stop(self):
        """Stop the simulator thread gracefully."""
        with self._lock:
            if not self.running:
                return False
            self._stop_event.set()
            self.running = False
            print('[Simulator] ⏹ Stop requested — waiting for thread to exit...')
            return True

    def is_running(self):
        return self.running

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def _run(self, interval=None):
        tick_seconds = interval or getattr(settings, 'SIMULATE_INTERVAL', 5)

        # Small startup delay so the DB is definitely ready
        time.sleep(2)

        while not self._stop_event.is_set():
            try:
                close_old_connections()
                self._tick()
            except Exception as e:
                print(f'[Simulator] ⚠ Tick failed: {e}')
            finally:
                close_old_connections()

            # Sleep in small increments so stop() is responsive
            slept = 0
            while slept < tick_seconds and not self._stop_event.is_set():
                time.sleep(0.5)
                slept += 0.5

        print('[Simulator] ■ Stopped.')

    # ------------------------------------------------------------------
    # One simulation tick
    # ------------------------------------------------------------------
    def _tick(self):
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()

        sectors = list(PipelineSector.objects.exclude(status='OFFLINE'))
        if not sectors:
            return

        anomaly_rate = getattr(settings, 'SIMULATE_ANOMALY_RATE', 0.03)
        max_logs = getattr(settings, 'SIMULATE_LOGS_PER_TICK', 8)
        sectors_to_sample = random.sample(sectors, min(max_logs, len(sectors)))

        detector = get_detector()
        logs_created = 0
        alerts_created = 0

        for sector in sectors_to_sample:
            flow, pressure = self._generate_reading(sector, anomaly_rate)
            result = detector.predict(
                flow, pressure,
                sector.baseline_flow_rate,
                sector.baseline_pressure,
            )

            log = IoTSensorLog.objects.create(
                pipeline_sector=sector,
                water_flow_rate=round(flow, 2),
                water_pressure=round(pressure, 2),
                temperature=round(random.uniform(18, 24), 1),
                ai_anomaly_flag=result['is_anomaly'],
                ai_confidence_score=result['confidence'],
                ai_anomaly_type=result['anomaly_type'],
            )
            logs_created += 1

            # --- Broadcast telemetry to WebSocket clients ---
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    'telemetry',
                    {
                        'type': 'telemetry_update',
                        'data': {
                            'id': log.id,
                            'sector_id': sector.sector_id,
                            'sector_name': sector.location_name,
                            'water_flow_rate': log.water_flow_rate,
                            'water_pressure': log.water_pressure,
                            'ai_anomaly_flag': log.ai_anomaly_flag,
                            'ai_confidence_score': log.ai_confidence_score,
                            'ai_anomaly_type': log.ai_anomaly_type,
                            'timestamp': log.timestamp.isoformat(),
                        },
                    }
                )

            if result['is_anomaly']:
                severity = 'CRITICAL' if result['confidence'] > 0.85 else 'WARNING'

                recent = AIAlert.objects.filter(
                    pipeline_sector=sector,
                    alert_type=result['anomaly_type'] or 'LEAK',
                    is_resolved=False,
                    created_at__gte=timezone.now() - timedelta(minutes=2),
                ).exists()

                if not recent:
                    alert_obj = AIAlert.objects.create(
                        pipeline_sector=sector,
                        sensor_log=log,
                        alert_type=result['anomaly_type'] or 'LEAK',
                        severity=severity,
                        confidence_score=result['confidence'],
                        message=result['message'],
                        estimated_water_loss=(
                            round(random.uniform(5, 25), 1)
                            if result['anomaly_type'] == 'LEAK' else None
                        ),
                    )
                    sector.status = 'AI_ALERT'
                    sector.save(update_fields=['status'])
                    alerts_created += 1

                    # --- Broadcast alert to WebSocket clients ---
                    if channel_layer:
                        async_to_sync(channel_layer.group_send)(
                            'alerts',
                            {
                                'type': 'alert_update',
                                'data': {
                                    'alert_id': alert_obj.alert_id,
                                    'sector_id': sector.sector_id,
                                    'sector_name': sector.location_name,
                                    'alert_type': alert_obj.alert_type,
                                    'severity': alert_obj.severity,
                                    'confidence_score': alert_obj.confidence_score,
                                    'message': alert_obj.message,
                                    'estimated_water_loss': alert_obj.estimated_water_loss,
                                    'created_at': alert_obj.created_at.isoformat(),
                                },
                            }
                        )

        self.stats['ticks'] += 1
        self.stats['logs_created'] += logs_created
        self.stats['alerts_created'] += alerts_created
        self.stats['last_tick_at'] = timezone.now().isoformat()

        print(f'[Simulator] tick #{self.stats["ticks"]} → '
              f'{logs_created} logs, {alerts_created} alerts')

    # ------------------------------------------------------------------
    # Realistic reading generator
    # ------------------------------------------------------------------
    def _generate_reading(self, sector, anomaly_rate):
        """
        Produce flow + pressure for a given sector.
        Uses a daily usage curve + noise + occasional anomaly.
        """
        baseline_flow = sector.baseline_flow_rate or 42.0
        baseline_pressure = sector.baseline_pressure or 350.0

        # Daily usage curve (peak ~14:00, trough ~03:00)
        hour = timezone.now().hour
        daily_factor = 1.0 + 0.15 * math.sin((hour - 6) * math.pi / 12)

        # Baseline flow with diurnal pattern + random noise
        flow = baseline_flow * daily_factor + random.uniform(-1.5, 1.5)
        pressure = baseline_pressure + random.uniform(-5, 5)

        # Occasionally inject an anomaly
        if random.random() < anomaly_rate:
            scenario = random.choices(
                ['leak', 'pressure_drop', 'flow_spike'],
                weights=[0.4, 0.4, 0.2],
            )[0]

            if scenario == 'leak':
                flow += random.uniform(15, 28)
                pressure -= random.uniform(70, 110)
            elif scenario == 'pressure_drop':
                pressure -= random.uniform(40, 65)
                flow += random.uniform(-2, 4)
            elif scenario == 'flow_spike':
                flow += random.uniform(20, 35)

        # Physical bounds
        flow = max(0.0, flow)
        pressure = max(0.0, pressure)

        return flow, pressure


# ------------------------------------------------------------------
# Singleton
# ------------------------------------------------------------------
sensor_simulator = SensorSimulator()