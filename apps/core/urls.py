from django.urls import path
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Service, Aspect, Commune, ServiceContent, AspectContent


class AspectContentSerializer(serializers.ModelSerializer):
    class Meta:
        model  = AspectContent
        fields = ['icon', 'what_is', 'how_to_evidence', 'response_time']


class ServiceContentSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ServiceContent
        fields = ['icon', 'summary', 'full_description', 'frequency', 'citizen_rights']


class AspectSerializer(serializers.ModelSerializer):
    content = AspectContentSerializer(read_only=True)

    class Meta:
        model  = Aspect
        fields = ['id', 'service_id', 'slug', 'description', 'content']


class ServiceSerializer(serializers.ModelSerializer):
    content = ServiceContentSerializer(read_only=True)

    class Meta:
        model  = Service
        fields = ['id', 'name', 'slug', 'description', 'order', 'content']


class CommuneSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Commune
        fields = ['id', 'number', 'name', 'area_hectares']


@api_view(['GET'])
def services_list(request):
    """
    GET /api/v1/core/services/
    Servicios activos con su contenido informativo.
    Usado por el formulario ciudadano.
    """
    services = Service.objects.filter(
        active=True
    ).select_related('content').order_by('order')
    return Response(ServiceSerializer(services, many=True).data)


@api_view(['GET'])
def aspects_list(request):
    """
    GET /api/v1/core/aspects/?service=sweeping-cleaning
    Aspectos activos con su contenido informativo.
    Cuando el ciudadano selecciona un aspecto ve la explicación.
    """
    service_slug = request.query_params.get('service')
    aspects = Aspect.objects.filter(
        active=True
    ).select_related('content', 'service')
    if service_slug:
        aspects = aspects.filter(service__slug=service_slug)
    return Response(AspectSerializer(aspects, many=True).data)


@api_view(['GET'])
def communes_list(request):
    """
    GET /api/v1/core/communes/
    9 comunas de Popayán.
    """
    communes = Commune.objects.all().order_by('number')
    return Response(CommuneSerializer(communes, many=True).data)


urlpatterns = [
    path('services/', services_list,  name='services-list'),
    path('aspects/',  aspects_list,   name='aspects-list'),
    path('communes/', communes_list,  name='communes-list'),
]
