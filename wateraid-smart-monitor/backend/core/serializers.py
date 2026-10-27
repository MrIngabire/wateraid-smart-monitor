from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    PipelineSector, IoTSensor, IoTSensorLog, 
    MaintenanceTask, AIAlert, SystemConfiguration
)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                  'full_name', 'role_type', 'role_display', 'phone_number',
                  'region_assigned', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm',
                  'first_name', 'last_name', 'role_type', 'phone_number', 'region_assigned']
    
    def validate(self, data):
        if data['password'] != data.pop('password_confirm'):
            raise serializers.ValidationError("Passwords do not match.")
        return data
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class PipelineSectorSerializer(serializers.ModelSerializer):
    sensor_count = serializers.IntegerField(read_only=True)
    active_alerts_count = serializers.SerializerMethodField()
    
    class Meta:
        model = PipelineSector
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
    
    def get_active_alerts_count(self, obj):
        return obj.ai_alerts.filter(is_resolved=False).count()


class IoTSensorSerializer(serializers.ModelSerializer):
    sector_name = serializers.CharField(source='pipeline_sector.location_name', read_only=True)
    
    class Meta:
        model = IoTSensor
        fields = '__all__'
        read_only_fields = ['installed_at']


class IoTSensorLogSerializer(serializers.ModelSerializer):
    sector_id = serializers.CharField(source='pipeline_sector.sector_id', read_only=True)
    sector_name = serializers.CharField(source='pipeline_sector.location_name', read_only=True)
    
    class Meta:
        model = IoTSensorLog
        fields = '__all__'
        read_only_fields = ['timestamp', 'ai_anomaly_flag', 'ai_confidence_score', 'ai_anomaly_type']


class MaintenanceTaskSerializer(serializers.ModelSerializer):
    sector_id = serializers.CharField(source='pipeline_sector.sector_id', read_only=True)
    sector_name = serializers.CharField(source='pipeline_sector.location_name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = MaintenanceTask
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class AIAlertSerializer(serializers.ModelSerializer):
    sector_id = serializers.CharField(source='pipeline_sector.sector_id', read_only=True)
    sector_name = serializers.CharField(source='pipeline_sector.location_name', read_only=True)
    alert_type_display = serializers.CharField(source='get_alert_type_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    
    class Meta:
        model = AIAlert
        fields = '__all__'
        read_only_fields = ['created_at']


class SystemConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemConfiguration
        fields = '__all__'


class DashboardStatsSerializer(serializers.Serializer):
    """Aggregated dashboard statistics"""
    active_pipelines = serializers.IntegerField()
    avg_flow_rate = serializers.FloatField()
    active_alerts = serializers.IntegerField()
    techs_deployed = serializers.IntegerField()
    total_sectors = serializers.IntegerField()
    healthy_sectors = serializers.IntegerField()
    warning_sectors = serializers.IntegerField()
    critical_sectors = serializers.IntegerField()