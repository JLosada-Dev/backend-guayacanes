from rest_framework import viewsets, mixins, status
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .models import Complaint, Evidence, SLAAlert, CommuneMetric
from .serializers import (
    ComplaintSerializer,
    ComplaintGeoSerializer,
    EvidenceSerializer,
    SLAAlertSerializer,
    CommuneMetricSerializer,
)


@extend_schema_view(
    list=extend_schema(
        summary='Listar denuncias ciudadanas',
        description=(
            'Lista todas las denuncias recibidas. Soporta filtros por estado, servicio, '
            'comuna y zona rural. También permite búsqueda de texto y ordenamiento.'
        ),
        parameters=[
            OpenApiParameter('status', OpenApiTypes.STR, OpenApiParameter.QUERY,
                             description='Filtrar por estado (`received`, `under_review`, `closed`).'),
            OpenApiParameter('service_slug', OpenApiTypes.STR, OpenApiParameter.QUERY,
                             description='Filtrar por servicio (ej: `sweeping-cleaning`, `green-zones`).'),
            OpenApiParameter('commune_id', OpenApiTypes.INT, OpenApiParameter.QUERY,
                             description='Filtrar por ID de comuna.'),
            OpenApiParameter('is_rural', OpenApiTypes.BOOL, OpenApiParameter.QUERY,
                             description='Filtrar denuncias rurales (`true`) o urbanas (`false`).'),
            OpenApiParameter('search', OpenApiTypes.STR, OpenApiParameter.QUERY,
                             description='Búsqueda de texto en descripción del aspecto, nombre de comuna o barrio.'),
            OpenApiParameter('ordering', OpenApiTypes.STR, OpenApiParameter.QUERY,
                             description='Ordenar por campo. Prefijo `-` para descendente. Ej: `-created_at`.'),
        ],
        responses=ComplaintSerializer(many=True),
        tags=['Urbaser / Denuncias'],
    ),
    retrieve=extend_schema(
        summary='Detalle de una denuncia',
        description='Retorna el detalle completo de una denuncia incluyendo las evidencias fotográficas adjuntas.',
        responses=ComplaintSerializer,
        tags=['Urbaser / Denuncias'],
    ),
    create=extend_schema(
        summary='Crear denuncia ciudadana',
        description=(
            'Crea una nueva denuncia ciudadana. La ubicación sigue una cascada automática:\n\n'
            '1. **GPS**: si se envían `latitude` y `longitude`.\n'
            '2. **Manual**: si se envía solo un punto desde el mapa.\n'
            '3. **Centroide**: si no hay coordenadas, usa el centroide de la comuna seleccionada.\n\n'
            'Al crear la denuncia se generan automáticamente las alertas SLA mediante análisis espacial PostGIS.'
        ),
        request=ComplaintSerializer,
        responses={201: ComplaintSerializer},
        tags=['Urbaser / Denuncias'],
    ),
)
class ComplaintViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Denuncias ciudadanas de infraestructura de servicios públicos Urbaser."""
    permission_classes  = [AllowAny]
    authentication_classes = []
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

    @extend_schema(
        summary='Denuncias en formato GeoJSON',
        description=(
            'Retorna las denuncias como GeoJSON FeatureCollection para renderizar en el mapa '
            'del dashboard de la Alcaldía. Acepta los mismos filtros que el listado estándar.'
        ),
        parameters=[
            OpenApiParameter('status', OpenApiTypes.STR, OpenApiParameter.QUERY,
                             description='Filtrar por estado (`received`, `under_review`, `closed`).'),
            OpenApiParameter('service_slug', OpenApiTypes.STR, OpenApiParameter.QUERY,
                             description='Filtrar por servicio.'),
            OpenApiParameter('commune_id', OpenApiTypes.INT, OpenApiParameter.QUERY,
                             description='Filtrar por ID de comuna.'),
        ],
        responses=ComplaintGeoSerializer(many=True),
        tags=['Urbaser / Denuncias'],
    )
    @action(detail=False, methods=['get'], url_path='geojson')
    def geojson(self, request):
        queryset   = self.filter_queryset(self.get_queryset())
        serializer = ComplaintGeoSerializer(queryset, many=True)
        return Response(serializer.data)


@extend_schema_view(
    create=extend_schema(
        summary='Subir foto de evidencia',
        description=(
            'Sube una fotografía como evidencia adjunta a una denuncia existente. '
            'Acepta `multipart/form-data`. El campo `complaint` debe ser el ID de la denuncia.'
        ),
        request=EvidenceSerializer,
        responses={201: EvidenceSerializer},
        tags=['Urbaser / Denuncias'],
    ),
)
class EvidenceViewSet(
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """Evidencias fotográficas adjuntas a denuncias ciudadanas."""
    queryset         = Evidence.objects.all()
    serializer_class = EvidenceSerializer
    parser_classes   = [MultiPartParser, FormParser, JSONParser]


@extend_schema_view(
    list=extend_schema(
        summary='Listar alertas SLA',
        description=(
            'Lista las alertas SLA generadas automáticamente mediante análisis espacial PostGIS '
            'al crear cada denuncia. Cada alerta indica si la ruta/zona más cercana incumple '
            'el SLA del servicio correspondiente.'
        ),
        parameters=[
            OpenApiParameter('violation', OpenApiTypes.BOOL, OpenApiParameter.QUERY,
                             description='`true` para ver solo incumplimientos.'),
            OpenApiParameter('service_slug', OpenApiTypes.STR, OpenApiParameter.QUERY,
                             description='Filtrar por servicio (ej: `sweeping-cleaning`).'),
            OpenApiParameter('route_type', OpenApiTypes.STR, OpenApiParameter.QUERY,
                             description='Tipo de ruta: `sweeping_microroute` o `green_zone`.'),
            OpenApiParameter('confidence', OpenApiTypes.STR, OpenApiParameter.QUERY,
                             description='Confianza del análisis: `high` (GPS), `medium` (manual), `low` (centroide).'),
            OpenApiParameter('complaint_id', OpenApiTypes.INT, OpenApiParameter.QUERY,
                             description='Filtrar por ID de denuncia asociada.'),
        ],
        responses=SLAAlertSerializer(many=True),
        tags=['Urbaser / SLA'],
    ),
    retrieve=extend_schema(
        summary='Detalle de alerta SLA',
        description='Retorna el detalle de una alerta SLA incluyendo distancia a la ruta, días transcurridos y nivel de confianza.',
        responses=SLAAlertSerializer,
        tags=['Urbaser / SLA'],
    ),
)
class SLAAlertViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Alertas SLA generadas automáticamente por análisis espacial PostGIS."""
    queryset         = SLAAlert.objects.all()
    serializer_class = SLAAlertSerializer
    filter_backends  = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['violation', 'service_slug', 'route_type', 'confidence', 'complaint_id']
    ordering_fields  = ['generated_at', 'violation', 'service_slug']


@extend_schema_view(
    list=extend_schema(
        summary='Listar métricas por comuna',
        description=(
            'Retorna estadísticas pre-calculadas por comuna y servicio para el heatmap del dashboard. '
            'Colores del heatmap según `violation_rate`:\n\n'
            '- `> 0.70` → rojo (crítico)\n'
            '- `> 0.40` → naranja (atención)\n'
            '- `≤ 0.40` → verde (cumplimiento)\n\n'
            'Filtrar por `period` (fecha en formato `YYYY-MM-DD`) para ver un corte temporal específico.'
        ),
        parameters=[
            OpenApiParameter('service_slug', OpenApiTypes.STR, OpenApiParameter.QUERY,
                             description='Filtrar por servicio (ej: `sweeping-cleaning`).'),
            OpenApiParameter('period', OpenApiTypes.DATE, OpenApiParameter.QUERY,
                             description='Filtrar por período (formato `YYYY-MM-DD`).'),
            OpenApiParameter('commune_id', OpenApiTypes.INT, OpenApiParameter.QUERY,
                             description='Filtrar por ID de comuna.'),
        ],
        responses=CommuneMetricSerializer(many=True),
        tags=['Urbaser / Métricas'],
    ),
    retrieve=extend_schema(
        summary='Detalle de métrica por comuna',
        description='Retorna el detalle de las métricas de una comuna para un período y servicio específico.',
        responses=CommuneMetricSerializer,
        tags=['Urbaser / Métricas'],
    ),
)
class CommuneMetricViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Métricas pre-calculadas por comuna para el heatmap del dashboard."""
    queryset         = CommuneMetric.objects.all()
    serializer_class = CommuneMetricSerializer
    pagination_class = None
    filter_backends  = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['service_slug', 'period', 'commune_id']
    ordering_fields  = ['period', 'violation_rate', 'commune_id']
