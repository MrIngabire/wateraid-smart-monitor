import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from faker import Faker
from core.models import (
    User, PipelineSector, IoTSensor, IoTSensorLog,
    MaintenanceTask, AIAlert, SystemConfiguration
)

fake = Faker()


class Command(BaseCommand):
    help = 'Seed the database with sample data for WaterAid Rwanda'
    
    def add_arguments(self, parser):
        parser.add_argument('--logs', type=int, default=500, help='Number of sensor logs')
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Seeding data...'))
        
        # 1. Create users
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser(
                username='admin', email='admin@wateraid.rw',
                password='admin123', first_name='System', last_name='Admin',
                role_type='ADMIN'
            )
            self.stdout.write(self.style.SUCCESS(f'✓ Admin: admin/admin123'))
        
        if not User.objects.filter(username='manager').exists():
            manager = User.objects.create_user(
                username='manager', email='manager@wateraid.rw',
                password='manager123', first_name='Jean', last_name='Doe',
                role_type='MANAGER', region_assigned='Southern Province'
            )
            self.stdout.write(self.style.SUCCESS(f'✓ Manager: manager/manager123'))
        
        technicians = []
        for i in range(1, 6):
            username = f'tech{i}'
            if not User.objects.filter(username=username).exists():
                tech = User.objects.create_user(
                    username=username, email=f'{username}@wateraid.rw',
                    password='tech123', first_name=fake.first_name(),
                    last_name=fake.last_name(), role_type='TECHNICIAN',
                    region_assigned=random.choice(['Nyanza', 'Huye', 'Kigali', 'Muhanga', 'Rwamagana'])
                )
                technicians.append(tech)
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(technicians)} technicians: tech1-tech5/tech123'))
        
        # 2. Create pipeline sectors
        sectors_data = [
            {'sector_id': 'SEC-NYA-01', 'location_name': 'Nyanza Central', 'region': 'Nyanza', 'lat': -2.3500, 'lon': 29.7500},
            {'sector_id': 'SEC-HUY-44', 'location_name': 'Huye Campus Branch', 'region': 'Huye', 'lat': -2.6000, 'lon': 29.7400},
            {'sector_id': 'SEC-KIG-12', 'location_name': 'Kigali Kicukiro', 'region': 'Kigali', 'lat': -1.9800, 'lon': 30.1000},
            {'sector_id': 'SEC-MUH-07', 'location_name': 'Muhanga Center', 'region': 'Muhanga', 'lat': -2.0800, 'lon': 29.7500},
            {'sector_id': 'SEC-RWA-22', 'location_name': 'Rwamagana East', 'region': 'Rwamagana', 'lat': -1.9500, 'lon': 30.4300},
            {'sector_id': 'SEC-NYA-05', 'location_name': 'Nyanza Busasamana', 'region': 'Nyanza', 'lat': -2.3200, 'lon': 29.7200},
            {'sector_id': 'SEC-HUY-50', 'location_name': 'Huye Mukura', 'region': 'Huye', 'lat': -2.5800, 'lon': 29.7000},
            {'sector_id': 'SEC-KIG-33', 'location_name': 'Kigali Gasabo', 'region': 'Kigali', 'lat': -1.9300, 'lon': 30.0800},
        ]
        
        sectors = []
        for data in sectors_data:
            sector, created = PipelineSector.objects.get_or_create(
                sector_id=data['sector_id'],
                defaults={
                    'location_name': data['location_name'],
                    'region': data['region'],
                    'latitude': data['lat'],
                    'longitude': data['lon'],
                    'installation_date': fake.date_between(start_date='-3y', end_date='today'),
                    'pipeline_length_km': round(random.uniform(2.0, 15.0), 2),
                    'status': 'ACTIVE',
                    'baseline_pressure': round(random.uniform(330, 370), 1),
                    'baseline_flow_rate': round(random.uniform(38, 46), 1),
                }
            )
            sectors.append(sector)
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(sectors)} pipeline sectors'))
        
        # 3. Create IoT sensors
        for i, sector in enumerate(sectors):
            for j in range(2):  # 2 sensors per sector
                IoTSensor.objects.get_or_create(
                    sensor_id=f'IOT-{sector.sector_id}-{j+1}',
                    defaults={
                        'sensor_type': 'COMBINED',
                        'ip_address': f'192.168.1.{100 + i*2 + j}',
                        'pipeline_sector': sector,
                        'is_active': True,
                        'last_ping': timezone.now(),
                    }
                )
        self.stdout.write(self.style.SUCCESS(f'✓ Created IoT sensors'))
        
        # 4. Generate sensor logs
        logs_count = options['logs']
        now = timezone.now()
        for _ in range(logs_count):
            sector = random.choice(sectors)
            # 95% normal, 5% anomalous
            if random.random() < 0.95:
                flow = sector.baseline_flow_rate + random.uniform(-2, 2)
                pressure = sector.baseline_pressure + random.uniform(-8, 8)
                anomaly = False
            else:
                flow = sector.baseline_flow_rate + random.uniform(10, 25)
                pressure = sector.baseline_pressure - random.uniform(50, 100)
                anomaly = True
            
            log = IoTSensorLog.objects.create(
                pipeline_sector=sector,
                water_flow_rate=round(flow, 2),
                water_pressure=round(pressure, 2),
                temperature=round(random.uniform(18, 25), 1),
                ai_anomaly_flag=anomaly,
                ai_confidence_score=round(random.uniform(0.7, 0.98), 3) if anomaly else None,
                ai_anomaly_type='LEAK' if anomaly else None,
            )
            log.timestamp = now - timedelta(minutes=random.randint(1, 7*24*60))
            log.save(update_fields=['timestamp'])
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {logs_count} sensor logs'))
        
        # 5. Create some AI alerts
        for _ in range(5):
            sector = random.choice(sectors)
            AIAlert.objects.create(
                pipeline_sector=sector,
                alert_type=random.choice(['LEAK', 'PRESSURE_DROP', 'FLOW_ANOMALY']),
                severity=random.choice(['WARNING', 'CRITICAL']),
                confidence_score=round(random.uniform(0.65, 0.98), 3),
                message=f"Anomaly detected in {sector.location_name}",
                estimated_water_loss=random.uniform(5, 25) if random.random() > 0.5 else None,
            )
        self.stdout.write(self.style.SUCCESS(f'✓ Created AI alerts'))
        
        # 6. Create maintenance tasks
        for _ in range(10):
            sector = random.choice(sectors)
            tech = random.choice(technicians)
            status = random.choice(['PENDING', 'IN_PROGRESS', 'RESOLVED'])
            task = MaintenanceTask.objects.create(
                pipeline_sector=sector,
                assigned_to=tech,
                created_by=manager,
                issue_description=fake.sentence(nb_words=12),
                status=status,
                priority=random.choice(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']),
                is_ai_generated=random.random() > 0.5,
                scheduled_date=now + timedelta(days=random.randint(-5, 10)),
            )
            if status == 'RESOLVED':
                task.resolved_date = now - timedelta(days=random.randint(1, 10))
                task.resolution_notes = fake.sentence()
                task.save()
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created maintenance tasks'))
        
        # 7. System configurations
        configs = [
            ('AI_LEAK_THRESHOLD', '0.85', 'Confidence threshold for leak alerts'),
            ('AI_PRESSURE_DROP_PCT', '15', 'Pressure drop percentage to flag'),
            ('AI_FLOW_ANOMALY_PCT', '25', 'Flow rate deviation percentage'),
            ('SYSTEM_NAME', 'WaterAid Smart Monitor', 'System display name'),
        ]
        for key, value, desc in configs:
            SystemConfiguration.objects.get_or_create(
                config_key=key,
                defaults={'config_value': value, 'description': desc}
            )
        
        self.stdout.write(self.style.SUCCESS('\n✅ Database seeded successfully!'))
        self.stdout.write(self.style.WARNING('\nLogin credentials:'))
        self.stdout.write('  Admin:    admin / admin123')
        self.stdout.write('  Manager:  manager / manager123')
        self.stdout.write('  Tech:     tech1 / tech123')