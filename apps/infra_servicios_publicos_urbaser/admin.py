from django.contrib.gis import admin
from .models import Complaint, Evidence


class EvidenceInline(admin.TabularInline):
    model  = Evidence
    extra  = 0
    fields = ['image', 'uploaded_at']
    readonly_fields = ['uploaded_at']


@admin.register(Complaint)
class ComplaintAdmin(admin.GISModelAdmin):
    list_display   = [
        'id', 'service_slug', 'aspect_description',
        'commune_name', 'status', 'location_source', 'created_at',
    ]
    list_filter    = ['status', 'service_slug', 'location_source', 'is_rural']
    search_fields  = ['aspect_description', 'commune_name', 'neighborhood_name']
    ordering       = ['-created_at']
    readonly_fields = ['created_at']
    inlines        = [EvidenceInline]
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
    list_display  = ['id', 'complaint', 'uploaded_at']
    ordering      = ['-uploaded_at']
    readonly_fields = ['uploaded_at']
