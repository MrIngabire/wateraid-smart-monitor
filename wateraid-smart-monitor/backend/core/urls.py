from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'sectors', views.PipelineSectorViewSet, basename='sector')
router.register(r'sensors', views.IoTSensorViewSet, basename='sensor')
router.register(r'sensor-logs', views.IoTSensorLogViewSet, basename='sensor-log')
router.register(r'tasks', views.MaintenanceTaskViewSet, basename='task')
router.register(r'alerts', views.AIAlertViewSet, basename='alert')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/register/', views.register_user, name='register'),
    path('auth/me/', views.current_user, name='current-user'),
    path('dashboard/stats/', views.dashboard_stats, name='dashboard-stats'),

    # One-off simulation trigger (single request)
    path('simulate/', views.simulate_sensor_data, name='simulate'),

    # Continuous simulator control
    path('simulator/status/', views.simulator_status, name='simulator-status'),
    path('simulator/start/', views.simulator_start, name='simulator-start'),
    path('simulator/stop/', views.simulator_stop, name='simulator-stop'),
]