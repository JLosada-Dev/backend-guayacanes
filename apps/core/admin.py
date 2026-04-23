from django.contrib.gis import admin
from .models import (
    Commune, Neighborhood,
    Service, Aspect,
    ServiceContent, AspectContent,
)


@admin.register(Commune)
class CommuneAdmin(admin.GISModelAdmin):
    list_display  = ['number', 'name', 'area_hectares']
    ordering      = ['number']
    search_fields = ['name', 'number']


@admin.register(Neighborhood)
class NeighborhoodAdmin(admin.GISModelAdmin):
    list_display  = ['name', 'commune', 'dane_code', 'osm_id']
    ordering      = ['commune__number', 'name']
    search_fields = ['name']
    list_filter   = ['commune']
    autocomplete_fields = ['commune']
    exclude       = ['geom']


class ServiceContentInline(admin.StackedInline):
    model       = ServiceContent
    extra       = 1
    fields      = ['icon', 'summary', 'full_description', 'frequency', 'citizen_rights']


class AspectContentInline(admin.StackedInline):
    model       = AspectContent
    extra       = 1
    fields      = ['icon', 'what_is', 'how_to_evidence', 'response_time']


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display  = ['name', 'slug', 'active', 'order']
    ordering      = ['order']
    search_fields = ['name', 'slug']
    list_filter   = ['active']
    inlines       = [ServiceContentInline]


@admin.register(Aspect)
class AspectAdmin(admin.ModelAdmin):
    list_display  = ['description', 'service', 'slug', 'active']
    ordering      = ['service__order', 'description']
    search_fields = ['description', 'slug']
    list_filter   = ['service', 'active']
    inlines       = [AspectContentInline]


@admin.register(ServiceContent)
class ServiceContentAdmin(admin.ModelAdmin):
    list_display  = ['service', 'icon', 'updated_at']
    search_fields = ['service__name', 'summary']


@admin.register(AspectContent)
class AspectContentAdmin(admin.ModelAdmin):
    list_display  = ['aspect', 'icon', 'response_time', 'updated_at']
    search_fields = ['aspect__description']
    list_filter   = ['aspect__service']
