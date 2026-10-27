from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, Q
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
import random

from .models import (
    PipelineSector, IoTSensor, IoTSensorLog,
    MaintenanceTask, AIAlert, SystemConfiguration
)
from .serializers import (
    UserSerializer, UserRegistrationSerializer, PipelineSectorSerializer,
    IoTSensorSerializer, IoTSensorLogSerializer, MaintenanceTaskSerializer,
    AIAlertSerializer, SystemConfigurationSerializer, DashboardStatsSerializer
)
from .permissions import (
    IsAdmin, IsManager, IsManagerOrAdmin, IsTechnician,
    IsTechnicianOrAdmin, ReadOnlyOrManager
)
from ai_engine.leak_detector import get_detector
from core.simulator import sensor_simulator

User = get_user_model()


# ============================================================
# AUTHENTICATION
# ============================================================

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Add extra claims to JWT token and allow login by username or email."""
    
    def validate(self, attrs):
        login_value = attrs.get(self.username_field)
        
        # Look up the user by username OR email
        try:
            user_obj = User.objects.get(
                Q(username=login_value) | Q(email=login_value)
            )
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {'detail': 'No active account found with the given credentials.'}
            )
        except User.MultipleObjectsReturned:
            # Prefer username match if multiple users share the email
            user_obj = User.objects.filter(username=login_value).first() or \
                       User.objects.filter(email=login_value).first()
        
        # Rewrite the username field so the parent class authenticates correctly
        attrs[self.username_field] = user_obj.username
        
        data = super().validate(attrs)
        data['user'] = UserSerializer(self.user).data
        return data
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = user.role_type
        token['username'] = user.username
        token['full_name'] = user.get_full_name() or user.username
        return token


# Need to import serializers here for the ValidationError
from rest_framework import serializers


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    return Response(UserSerializer(request.user).data)


# ============================================================
# VIEWSETS (With Strict RBAC)
# ============================================================

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    search_fields = ['username', 'email', 'first_name', 'last_name']
    filterset_fields = ['role_type', 'is_active']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsManagerOrAdmin()]
        if self.action in ['create', 'destroy', 'update', 'partial_update', 'toggle_active']:
            return [IsAdmin()]
        if self.action == 'me':
            return [IsAuthenticated()]
        return [IsAdmin()]
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        return Response(UserSerializer(request.user).data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def toggle_active(self, request, pk=None):
        user = self.get_object()
        user.is_active = not user.is_active
        user.save()
        return Response(UserSerializer(user).data)


class PipelineSectorViewSet(viewsets.ModelViewSet):
    queryset = PipelineSector.objects.all()
    serializer_class = PipelineSectorSerializer
    search_fields = ['sector_id', 'location_name', 'region']
    filterset_fields = ['status', 'region']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'summary']:
            return [IsAuthenticated()]
        return [IsManagerOrAdmin()]
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def summary(self, request):
        total = self.queryset.count()
        by_status = self.queryset.values('status').annotate(count=Count('id'))
        return Response({
            'total': total,
            'by_status': list(by_status),
        })


class IoTSensorViewSet(viewsets.ModelViewSet):
    queryset = IoTSensor.objects.all()
    serializer_class = IoTSensorSerializer
    filterset_fields = ['sensor_type', 'is_active', 'pipeline_sector']
    search_fields = ['sensor_id', 'ip_address']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsManagerOrAdmin()]


class IoTSensorLogViewSet(viewsets.ModelViewSet):
    queryset = IoTSensorLog.objects.all()
    serializer_class = IoTSensorLogSerializer
    filterset_fields = ['pipeline_sector', 'ai_anomaly_flag']
    ordering_fields = ['timestamp', 'water_flow_rate', 'water_pressure']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'latest', 'trend']:
            return [IsAuthenticated()]
        return [IsTechnicianOrAdmin()]  # Only techs/admins can post sensor logs
    
    def perform_create(self, serializer):
        """Override to run AI evaluation on new sensor data"""
        data = self.request.data
        flow_rate = float(data.get('water_flow_rate'))
        pressure = float(data.get('water_pressure'))
        
        sector_id = data.get('pipeline_sector')
        try:
            sector = PipelineSector.objects.get(pk=sector_id)
        except PipelineSector.DoesNotExist:
            sector = None
        
        detector = get_detector()
        baseline_flow = sector.baseline_flow_rate if sector else 42.0
        baseline_pressure = sector.baseline_pressure if sector else 350.0
        
        result = detector.predict(flow_rate, pressure, baseline_flow, baseline_pressure)
        
        log = serializer.save(
            ai_anomaly_flag=result['is_anomaly'],
            ai_confidence_score=result['confidence'],
            ai_anomaly_type=result['anomaly_type']
        )
        
        if result['is_anomaly'] and sector:
            severity = 'CRITICAL' if result['confidence'] > 0.85 else 'WARNING'
            AIAlert.objects.create(
                pipeline_sector=sector,
                sensor_log=log,
                alert_type=result['anomaly_type'] or 'LEAK',
                severity=severity,
                confidence_score=result['confidence'],
                message=result['message'],
                estimated_water_loss=15.0 if result['anomaly_type'] == 'LEAK' else None,
            )
            sector.status = 'AI_ALERT'
            sector.save()
        
        return log
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Get latest sensor reading per sector"""
        sectors = PipelineSector.objects.all()
        data = []
        for sector in sectors:
            log = sector.sensor_logs.order_by('-timestamp').first()
            if log:
                data.append(IoTSensorLogSerializer(log).data)
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def trend(self, request):
        """Get time-series trend for a sector"""
        sector_id = request.query_params.get('sector_id')
        hours = int(request.query_params.get('hours', 24))
        since = timezone.now() - timedelta(hours=hours)
        
        qs = self.queryset.filter(timestamp__gte=since)
        if sector_id:
            qs = qs.filter(pipeline_sector_id=sector_id)
        
        qs = qs.order_by('timestamp')
        return Response(IoTSensorLogSerializer(qs, many=True).data)


class MaintenanceTaskViewSet(viewsets.ModelViewSet):
    queryset = MaintenanceTask.objects.all()
    serializer_class = MaintenanceTaskSerializer
    filterset_fields = ['status', 'priority', 'assigned_to', 'pipeline_sector']
    search_fields = ['issue_description', 'pipeline_sector__sector_id']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        if self.action == 'create':
            return [IsAuthenticated()]
        if self.action in ['update', 'partial_update', 'destroy', 'resolve']:
            return [IsManagerOrAdmin()]
        return [IsAuthenticated()]
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[IsManagerOrAdmin])
    def resolve(self, request, pk=None):
        task = self.get_object()
        task.status = 'RESOLVED'
        task.resolution_notes = request.data.get('resolution_notes', task.resolution_notes)
        task.resolved_date = timezone.now()
        task.save()
        return Response(MaintenanceTaskSerializer(task).data)


class AIAlertViewSet(viewsets.ModelViewSet):
    queryset = AIAlert.objects.all()
    serializer_class = AIAlertSerializer
    filterset_fields = ['alert_type', 'severity', 'is_resolved', 'pipeline_sector']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'active']:
            return [IsAuthenticated()]
        return [IsManagerOrAdmin()]
    
    @action(detail=True, methods=['post'], permission_classes=[IsManagerOrAdmin])
    def acknowledge(self, request, pk=None):
        alert = self.get_object()
        alert.is_acknowledged = True
        alert.acknowledged_by = request.user
        alert.acknowledged_at = timezone.now()
        alert.save()
        return Response(AIAlertSerializer(alert).data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsManagerOrAdmin])
    def resolve(self, request, pk=None):
        alert = self.get_object()
        alert.is_resolved = True
        alert.resolved_at = timezone.now()
        alert.save()
        
        sector = alert.pipeline_sector
        if not sector.ai_alerts.filter(is_resolved=False).exists():
            sector.status = 'ACTIVE'
            sector.save()
        return Response(AIAlertSerializer(alert).data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def active(self, request):
        active = self.queryset.filter(is_resolved=False)
        return Response(AIAlertSerializer(active, many=True).data)


# ============================================================
# DASHBOARD STATISTICS
# ============================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """Aggregated stats for manager dashboard"""
    total_sectors = PipelineSector.objects.count()
    
    # Latest flow rate average
    recent_logs = IoTSensorLog.objects.filter(
        timestamp__gte=timezone.now() - timedelta(hours=1)
    )
    avg_flow = recent_logs.aggregate(avg=Avg('water_flow_rate'))['avg'] or 0.0
    
    active_alerts = AIAlert.objects.filter(is_resolved=False).count()
    techs_deployed = MaintenanceTask.objects.filter(
        status__in=['PENDING', 'IN_PROGRESS']
    ).values('assigned_to').distinct().count()
    
    critical = PipelineSector.objects.filter(status='AI_ALERT').count()
    warning = PipelineSector.objects.filter(status='MAINTENANCE').count()
    offline = PipelineSector.objects.filter(status='OFFLINE').count()
    healthy = total_sectors - critical - warning - offline
    
    data = {
        'active_pipelines': total_sectors,
        'avg_flow_rate': round(avg_flow, 2),
        'active_alerts': active_alerts,
        'techs_deployed': techs_deployed,
        'total_sectors': total_sectors,
        'healthy_sectors': max(0, healthy),
        'warning_sectors': warning,
        'critical_sectors': critical,
    }
    return Response(data)


# ============================================================
# MANUAL SIMULATION TRIGGER (ONE-OFF)
# ============================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsManagerOrAdmin])
def simulate_sensor_data(request):
    """Simulate a single IoT data ingestion event manually."""
    sector_id = request.data.get('sector_id')
    scenario = request.data.get('scenario', 'normal')
    
    try:
        sector = PipelineSector.objects.get(pk=sector_id)
    except PipelineSector.DoesNotExist:
        return Response({'error': 'Sector not found'}, status=404)
    
    if scenario == 'normal':
        flow = sector.baseline_flow_rate + random.uniform(-1, 1)
        pressure = sector.baseline_pressure + random.uniform(-5, 5)
    elif scenario == 'leak':
        flow = sector.baseline_flow_rate + random.uniform(15, 25)
        pressure = sector.baseline_pressure - random.uniform(70, 100)
    elif scenario == 'pressure_drop':
        flow = sector.baseline_flow_rate + random.uniform(-2, 2)
        pressure = sector.baseline_pressure - random.uniform(35, 60)
    else:
        return Response({'error': 'Invalid scenario'}, status=400)
    
    log = IoTSensorLog.objects.create(
        pipeline_sector=sector,
        water_flow_rate=round(flow, 2),
        water_pressure=round(pressure, 2),
    )
    
    detector = get_detector()
    result = detector.predict(
        flow, pressure, 
        sector.baseline_flow_rate, sector.baseline_pressure
    )
    
    log.ai_anomaly_flag = result['is_anomaly']
    log.ai_confidence_score = result['confidence']
    log.ai_anomaly_type = result['anomaly_type']
    log.save()
    
    if result['is_anomaly']:
        severity = 'CRITICAL' if result['confidence'] > 0.85 else 'WARNING'
        AIAlert.objects.create(
            pipeline_sector=sector,
            sensor_log=log,
            alert_type=result['anomaly_type'] or 'LEAK',
            severity=severity,
            confidence_score=result['confidence'],
            message=result['message'],
            estimated_water_loss=15.0 if result['anomaly_type'] == 'LEAK' else None,
        )
        sector.status = 'AI_ALERT'
        sector.save()
    
    return Response({
        'log': IoTSensorLogSerializer(log).data,
        'ai_result': result,
    })


# ============================================================
# BACKGROUND SIMULATOR CONTROL
# ============================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def simulator_status(request):
    """Return simulator running state + counters."""
    return Response({
        'running': sensor_simulator.is_running(),
        'stats': sensor_simulator.stats,
        'interval_seconds': getattr(settings, 'SIMULATE_INTERVAL', 5),
        'anomaly_rate': getattr(settings, 'SIMULATE_ANOMALY_RATE', 0.03),
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsManagerOrAdmin])
def simulator_start(request):
    """Manually start the simulator."""
    started = sensor_simulator.start()
    return Response({
        'started': started,
        'running': sensor_simulator.is_running(),
        'message': 'Simulator started.' if started else 'Simulator already running.',
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsManagerOrAdmin])
def simulator_stop(request):
    """Manually stop the simulator."""
    stopped = sensor_simulator.stop()
    return Response({
        'stopped': stopped,
        'running': sensor_simulator.is_running(),
        'message': 'Stopping simulator...' if stopped else 'Simulator not running.',
    })