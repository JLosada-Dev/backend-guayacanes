from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Complaint, Evidence, SLAAlert, CommuneMetric
from .serializers import (
    ComplaintSerializer,
    ComplaintGeoSerializer,
    EvidenceSerializer,
    SLAAlertSerializer,
    CommuneMetricSerializer,
)


class ComplaintViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    Denuncias ciudadanas.

    POST /api/urbaser/complaints/         — crear denuncia
    GET  /api/urbaser/complaints/         — listar (solo admin)
    GET  /api/urbaser/complaints/{id}/    — detalle
    GET  /api/urbaser/complaints/geojson/ — mapa dashboard
    """
    queryset         = Complaint.objects.all().order_by('-created_at')
    serializer_class = ComplaintSerializer
    filter_backends  = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'service_slug', 'commune_id', 'is_rural']
    search_fields    = ['aspect_description', 'commune_name', 'neighborhood_name']
    ordering_fields  = ['created_at', 'status', 'service_slug']

    def get_serializer_class(self):
        if self.action == 'geojson':
            return ComplaintGeoSerializer
        return ComplaintSerializer

    @action(detail=False, methods=['get'], url_path='geojson')
    def geojson(self, request):
        """
        Retorna denuncias como GeoJSON FeatureCollection.
        Usado por el mapa del dashboard de la Alcaldía.
        """
        queryset   = self.filter_queryset(self.get_queryset())
        serializer = ComplaintGeoSerializer(queryset, many=True)
        return Response(serializer.data)


class EvidenceViewSet(
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """
    POST /api/urbaser/evidence/ — subir foto adjunta a una denuncia
    """
    queryset         = Evidence.objects.all()
    serializer_class = EvidenceSerializer
    parser_classes   = [MultiPartParser, FormParser, JSONParser]


class SLAAlertViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    GET /api/v1/urbaser/alerts/           — listado de alertas SLA
    GET /api/v1/urbaser/alerts/{id}/      — detalle
    GET /api/v1/urbaser/alerts/?violation=true  — solo incumplimientos
    """
    queryset         = SLAAlert.objects.all()
    serializer_class = SLAAlertSerializer
    filter_backends  = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['violation', 'service_slug', 'route_type', 'confidence', 'complaint_id']
    ordering_fields  = ['generated_at', 'violation', 'service_slug']


class CommuneMetricViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    GET /api/v1/urbaser/metrics/          — métricas por comuna (heatmap)
    GET /api/v1/urbaser/metrics/?service_slug=sweeping-cleaning
    GET /api/v1/urbaser/metrics/?period=2026-04-01
    """
    queryset         = CommuneMetric.objects.all()
    serializer_class = CommuneMetricSerializer
    filter_backends  = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['service_slug', 'period', 'commune_id']
    ordering_fields  = ['period', 'violation_rate', 'commune_id']
