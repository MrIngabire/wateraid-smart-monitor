"""
Run the sensor simulator as a standalone process.
Useful for demos where you want the simulator running in its own terminal.

Usage:
    python manage.py run_simulation
    python manage.py run_simulation --interval 3 --anomaly-rate 0.05
"""
import time
from django.core.management.base import BaseCommand
from core.simulator import SensorSimulator


class Command(BaseCommand):
    help = 'Run the IoT sensor simulator as a standalone process.'

    def add_arguments(self, parser):
        parser.add_argument('--interval', type=int, default=5,
                            help='Seconds between ticks (default: 5)')
        parser.add_argument('--anomaly-rate', type=float, default=0.03,
                            help='Probability of anomaly per sector per tick (default: 0.03)')

    def handle(self, *args, **options):
        from django.conf import settings
        settings.SIMULATE_INTERVAL = options['interval']
        settings.SIMULATE_ANOMALY_RATE = options['anomaly_rate']

        sim = SensorSimulator()
        self.stdout.write(self.style.SUCCESS(
            f'▶ Starting simulator (interval={options["interval"]}s, '
            f'anomaly_rate={options["anomaly_rate"]})...'
        ))
        self.stdout.write('Press Ctrl+C to stop.\n')

        sim.start(interval=options['interval'])

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stdout.write('\n⏹ Stopping...')
            sim.stop()
            time.sleep(1)
            self.stdout.write(self.style.SUCCESS('✓ Stopped.'))