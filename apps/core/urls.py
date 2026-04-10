from rest_framework.routers import DefaultRouter
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import serializers
from .models import Service, Aspect, Commune

router = DefaultRouter()


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Service
        fields = ['id', 'name', 'slug', 'description', 'order']


class AspectSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Aspect
        fields = ['id', 'service_id', 'slug', 'description']


class CommuneSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Commune
        fields = ['id', 'number', 'name', 'area_hectares']


@api_view(['GET'])
def services_list(request):
    """GET /api/core/services/ — servicios activos para el formulario"""
    services = Service.objects.filter(active=True).order_by('order')
    return Response(ServiceSerializer(services, many=True).data)


@api_view(['GET'])
def aspects_list(request):
    """GET /api/core/aspects/?service=sweeping-cleaning"""
    service_slug = request.query_params.get('service')
    aspects = Aspect.objects.filter(active=True)
    if service_slug:
        aspects = aspects.filter(service__slug=service_slug)
    return Response(AspectSerializer(aspects, many=True).data)


@api_view(['GET'])
def communes_list(request):
    """GET /api/core/communes/"""
    communes = Commune.objects.all().order_by('number')
    return Response(CommuneSerializer(communes, many=True).data)


urlpatterns = router.urls + [
    __import__('django.urls', fromlist=['path']).path(
        'services/', services_list, name='services-list'
    ),
    __import__('django.urls', fromlist=['path']).path(
        'aspects/', aspects_list, name='aspects-list'
    ),
    __import__('django.urls', fromlist=['path']).path(
        'communes/', communes_list, name='communes-list'
    ),
]
