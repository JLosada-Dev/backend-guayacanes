from django.contrib.gis import admin
from .models import (
    Complaint, Evidence,
    SweepingMacroRoute, SweepingMicroRoute,
    GreenZone, CuttingSchedule, Intervention,
)


class EvidenceInline(admin.TabularInline):
    model           = Evidence
    extra           = 0
    fields          = ['image', 'uploaded_at']
    readonly_fields = ['uploaded_at']


@admin.register(Complaint)
class ComplaintAdmin(admin.GISModelAdmin):
    list_display    = [
        'id', 'service_slug', 'aspect_description',
        'commune_name', 'status', 'location_source', 'created_at',
    ]
    list_filter     = ['status', 'service_slug', 'location_source', 'is_rural']
    search_fields   = ['aspect_description', 'commune_name', 'neighborhood_name']
    ordering        = ['-created_at']
    readonly_fields = ['created_at']
    inlines         = [EvidenceInline]
    fieldsets = [
        ('Qué', {
            'fields': [
                'service_id', 'service_slug', 'service_name',
                'aspect_id', 'aspect_slug', 'aspect_description',
            ]
        }),
        ('Dónde', {
            'fields': [
                'commune_id', 'commune_name',
                'neighborhood_id', 'neighborhood_name',
                'is_rural', 'hamlet_name',
                'location', 'location_source',
            ]
        }),
        ('Contexto', {
            'fields': ['description', 'status', 'created_at']
        }),
    ]


@admin.register(Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    list_display    = ['id', 'complaint', 'uploaded_at']
    ordering        = ['-uploaded_at']
    readonly_fields = ['uploaded_at']


class SweepingMicroRouteInline(admin.TabularInline):
    model           = SweepingMicroRoute
    extra           = 0
    fields          = ['layer', 'active']
    readonly_fields = ['layer']
    can_delete      = False
    max_num         = 0
    verbose_name_plural = 'Microrutas (solo lectura — cargadas desde shapefile)'


@admin.register(SweepingMacroRoute)
class SweepingMacroRouteAdmin(admin.GISModelAdmin):
    list_display  = ['code', 'name', 'zone_type', 'days_text', 'start_time', 'active']
    list_filter   = ['zone_type', 'active']
    search_fields = ['code', 'name']
    ordering      = ['code']
    readonly_fields = ['code']
    inlines       = [SweepingMicroRouteInline]


@admin.register(SweepingMicroRoute)
class SweepingMicroRouteAdmin(admin.GISModelAdmin):
    list_display  = ['id', 'macroroute', 'layer', 'active']
    list_filter   = ['macroroute', 'layer', 'active']
    ordering      = ['macroroute__code']
    readonly_fields = ['macroroute', 'layer', 'geom']


class CuttingScheduleInline(admin.TabularInline):
    model           = CuttingSchedule
    extra           = 0
    fields          = ['scheduled_date', 'month', 'year', 'executed']
    readonly_fields = ['scheduled_date', 'month', 'year']


class InterventionInline(admin.TabularInline):
    model  = Intervention
    extra  = 1
    fields = ['execution_date', 'intervention_type', 'recorded_by', 'notes']


@admin.register(GreenZone)
class GreenZoneAdmin(admin.GISModelAdmin):
    list_display  = ['external_id', 'name', 'zone_type', 'area_sqm', 'cycle_days', 'active']
    list_filter   = ['zone_type', 'active']
    search_fields = ['name', 'external_id']
    ordering      = ['name']
    inlines       = [CuttingScheduleInline, InterventionInline]


@admin.register(CuttingSchedule)
class CuttingScheduleAdmin(admin.ModelAdmin):
    list_display  = ['zone', 'scheduled_date', 'month', 'year', 'executed']
    list_filter   = ['executed', 'year', 'month']
    ordering      = ['scheduled_date']
    search_fields = ['zone__name']


@admin.register(Intervention)
class InterventionAdmin(admin.ModelAdmin):
    list_display  = ['zone', 'execution_date', 'intervention_type', 'recorded_by']
    list_filter   = ['intervention_type']
    ordering      = ['-execution_date']
    search_fields = ['zone__name', 'recorded_by']
