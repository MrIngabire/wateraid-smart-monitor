"""
Database Models for AI-based Smart Water Infrastructure Monitoring System
Case Study: WaterAid Rwanda
"""
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator


class User(AbstractUser):
    """Custom User model with role-based access control"""
    ROLE_CHOICES = (
        ('ADMIN', 'System Administrator'),
        ('MANAGER', 'WaterAid Manager'),
        ('TECHNICIAN', 'Field Technician'),
    )
    
    role_type = models.CharField(max_length=15, choices=ROLE_CHOICES, default='TECHNICIAN')
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    region_assigned = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"
    
    def get_role_display(self):
        return dict(self.ROLE_CHOICES).get(self.role_type, self.role_type)


class PipelineSector(models.Model):
    """Represents a geographic pipeline sector/zone"""
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('MAINTENANCE', 'Under Maintenance'),
        ('OFFLINE', 'Offline'),
        ('AI_ALERT', 'AI Alert Triggered'),
    )
    
    sector_id = models.CharField(max_length=50, primary_key=True, unique=True)
    location_name = models.CharField(max_length=150)
    region = models.CharField(max_length=100)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    installation_date = models.DateField()
    pipeline_length_km = models.FloatField(default=0.0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    baseline_pressure = models.FloatField(default=350.0, help_text="Normal operating pressure in kPa")
    baseline_flow_rate = models.FloatField(default=42.0, help_text="Normal flow rate in L/s")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'pipeline_sectors'
        ordering = ['sector_id']
    
    def __str__(self):
        return f"{self.sector_id} - {self.location_name}"
    
    @property
    def sensor_count(self):
        return self.sensors.filter(is_active=True).count()


class IoTSensor(models.Model):
    """Physical IoT sensor device installed in a pipeline sector"""
    SENSOR_TYPES = (
        ('FLOW', 'Flow Rate Sensor'),
        ('PRESSURE', 'Pressure Sensor'),
        ('COMBINED', 'Combined Flow & Pressure'),
    )
    
    sensor_id = models.CharField(max_length=50, unique=True)
    sensor_type = models.CharField(max_length=20, choices=SENSOR_TYPES, default='COMBINED')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    mac_address = models.CharField(max_length=50, blank=True, null=True)
    firmware_version = models.CharField(max_length=20, default='1.0.0')
    pipeline_sector = models.ForeignKey(
        PipelineSector, 
        on_delete=models.CASCADE, 
        related_name='sensors',
        null=True, blank=True
    )
    is_active = models.BooleanField(default=True)
    last_ping = models.DateTimeField(null=True, blank=True)
    installed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'iot_sensors'
        ordering = ['sensor_id']
    
    def __str__(self):
        return f"{self.sensor_id} ({self.get_sensor_type_display()})"


class IoTSensorLog(models.Model):
    """Real-time telemetry data from IoT sensors"""
    sensor = models.ForeignKey(
        IoTSensor, 
        on_delete=models.CASCADE, 
        related_name='logs',
        null=True, blank=True
    )
    pipeline_sector = models.ForeignKey(
        PipelineSector, 
        on_delete=models.CASCADE, 
        related_name='sensor_logs'
    )
    water_flow_rate = models.FloatField(help_text="Flow rate in L/s")
    water_pressure = models.FloatField(help_text="Pressure in kPa")
    temperature = models.FloatField(null=True, blank=True, help_text="Water temperature in Celsius")
    ai_anomaly_flag = models.BooleanField(default=False)
    ai_confidence_score = models.FloatField(null=True, blank=True, help_text="AI confidence 0-1")
    ai_anomaly_type = models.CharField(max_length=50, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'iot_sensor_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['pipeline_sector', '-timestamp']),
            models.Index(fields=['ai_anomaly_flag']),
        ]
    
    def __str__(self):
        return f"{self.pipeline_sector.sector_id} @ {self.timestamp:%Y-%m-%d %H:%M}"


class MaintenanceTask(models.Model):
    """Field maintenance records"""
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('RESOLVED', 'Resolved'),
        ('CANCELLED', 'Cancelled'),
    )
    PRIORITY_CHOICES = (
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    )
    
    task_id = models.AutoField(primary_key=True)
    pipeline_sector = models.ForeignKey(
        PipelineSector, 
        on_delete=models.CASCADE, 
        related_name='maintenance_tasks'
    )
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='assigned_tasks'
    )
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='created_tasks'
    )
    issue_description = models.TextField()
    resolution_notes = models.TextField(blank=True, null=True)
    parts_replaced = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    is_ai_generated = models.BooleanField(default=False)
    scheduled_date = models.DateTimeField(null=True, blank=True)
    resolved_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'maintenance_tasks'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Task #{self.task_id} - {self.pipeline_sector.sector_id} [{self.status}]"


class AIAlert(models.Model):
    """AI-generated alerts for anomalies"""
    ALERT_TYPES = (
        ('LEAK', 'Pipeline Leak Detected'),
        ('PRESSURE_DROP', 'Abnormal Pressure Drop'),
        ('FLOW_ANOMALY', 'Flow Rate Anomaly'),
        ('MAINTENANCE', 'Predictive Maintenance Needed'),
    )
    SEVERITY_CHOICES = (
        ('INFO', 'Informational'),
        ('WARNING', 'Warning'),
        ('CRITICAL', 'Critical'),
    )
    
    alert_id = models.AutoField(primary_key=True)
    pipeline_sector = models.ForeignKey(
        PipelineSector, 
        on_delete=models.CASCADE, 
        related_name='ai_alerts'
    )
    sensor_log = models.ForeignKey(
        IoTSensorLog, 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='triggered_alerts'
    )
    alert_type = models.CharField(max_length=30, choices=ALERT_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='WARNING')
    confidence_score = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    message = models.TextField()
    estimated_water_loss = models.FloatField(null=True, blank=True, help_text="L/min")
    is_acknowledged = models.BooleanField(default=False)
    acknowledged_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='acknowledged_alerts'
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ai_alerts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_resolved', '-created_at']),
            models.Index(fields=['severity']),
        ]
    
    def __str__(self):
        return f"Alert #{self.alert_id} - {self.get_alert_type_display()} [{self.severity}]"


class SystemConfiguration(models.Model):
    """Global system configuration for AI thresholds"""
    config_key = models.CharField(max_length=100, unique=True)
    config_value = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'system_configurations'
    
    def __str__(self):
        return f"{self.config_key} = {self.config_value}"
    
    @classmethod
    def get_value(cls, key, default=None):
        try:
            return cls.objects.get(config_key=key).config_value
        except cls.DoesNotExist:
            return default