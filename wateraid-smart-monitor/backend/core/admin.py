from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, PipelineSector, IoTSensor, IoTSensorLog,
    MaintenanceTask, AIAlert, SystemConfiguration
)



@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role_type', 'is_active']
    list_filter = ['role_type', 'is_active', 'is_staff']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('role_type', 'phone_number', 'region_assigned')}),
    )


@admin.register(PipelineSector)
class PipelineSectorAdmin(admin.ModelAdmin):
    list_display = ['sector_id', 'location_name', 'region', 'status', 'installation_date']
    list_filter = ['status', 'region']
    search_fields = ['sector_id', 'location_name']


@admin.register(IoTSensor)
class IoTSensorAdmin(admin.ModelAdmin):
    list_display = ['sensor_id', 'sensor_type', 'pipeline_sector', 'is_active', 'last_ping']
    list_filter = ['sensor_type', 'is_active']


@admin.register(IoTSensorLog)
class IoTSensorLogAdmin(admin.ModelAdmin):
    list_display = ['pipeline_sector', 'water_flow_rate', 'water_pressure', 'ai_anomaly_flag', 'timestamp']
    list_filter = ['ai_anomaly_flag', 'pipeline_sector']
    date_hierarchy = 'timestamp'


@admin.register(MaintenanceTask)
class MaintenanceTaskAdmin(admin.ModelAdmin):
    list_display = ['task_id', 'pipeline_sector', 'assigned_to', 'status', 'priority', 'created_at']
    list_filter = ['status', 'priority', 'is_ai_generated']


@admin.register(AIAlert)
class AIAlertAdmin(admin.ModelAdmin):
    list_display = ['alert_id', 'pipeline_sector', 'alert_type', 'severity', 'confidence_score', 'is_resolved', 'created_at']
    list_filter = ['alert_type', 'severity', 'is_resolved']


@admin.register(SystemConfiguration)
class SystemConfigurationAdmin(admin.ModelAdmin):
    list_display = ['config_key', 'config_value', 'updated_at']


from django.urls import path
from django.shortcuts import redirect
from django.contrib import admin as dj_admin
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator


class SimulatorAdminView(dj_admin.AdminSite):
    """Not used — we'll attach custom URLs to the default admin site instead."""
    pass


# Custom admin URLs
_original_get_urls = dj_admin.site.get_urls


def _simulator_get_urls():
    from django.urls import path
    from django.http import JsonResponse

    def simulator_view(request):
        if request.method == 'POST':
            action = request.POST.get('action')
            if action == 'start':
                sensor_simulator.start()
            elif action == 'stop':
                sensor_simulator.stop()
            return redirect('/admin/simulator/')
        return JsonResponse({
            'running': sensor_simulator.is_running(),
            'stats': sensor_simulator.stats,
        }, json_dumps_params={'indent': 2})

    custom = [
        path('simulator/', staff_member_required(simulator_view), name='simulator-control'),
    ]
    return custom + _original_get_urls()


dj_admin.site.get_urls = _simulator_get_urls