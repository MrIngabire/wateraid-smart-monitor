from django.apps import AppConfig
import os
import sys


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        """
        Called once when Django starts.
        Boots the background sensor simulator unless:
          - we're running migrations / collectstatic / shell
          - the AUTO_SIMULATE setting is False
          - we're running the autoreloader's parent process
        """
        # Skip during management commands that don't serve requests
        skip_commands = {
            'makemigrations', 'migrate', 'collectstatic',
            'shell', 'test', 'seed_data', 'createsuperuser',
            'dbshell', 'flush', 'loaddata', 'dumpdata',
            'run_simulation',   # the standalone command handles its own lifecycle
        }
        if any(cmd in sys.argv for cmd in skip_commands):
            return

        # The Django autoreloader runs the app twice; only boot in the child
        if os.environ.get('RUN_MAIN') != 'true' and 'runserver' in sys.argv:
            return

        from django.conf import settings
        if not getattr(settings, 'AUTO_SIMULATE', False):
            print('[Simulator] AUTO_SIMULATE=False → simulator not started.')
            return

        # Import here to avoid AppRegistryNotReady
        from core.simulator import sensor_simulator
        sensor_simulator.start()