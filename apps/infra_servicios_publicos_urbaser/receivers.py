"""
Receivers de auditoría SLA.
Escucha complaint_created y ejecuta el cruce PostGIS.

Flujo:
  complaint_created signal
    → determinar confianza por location_source
    → según service_slug ejecutar cruce correspondiente
    → crear SLAAlert(es)
    → recalcular CommuneMetric
"""
from django.utils import timezone
from django.contrib.gis.measure import D

from .signals import complaint_created
from .models import (
    SweepingMicroRoute,
    GreenZone,
    CuttingSchedule,
    SLAAlert,
    CommuneMetric,
)

CONFIDENCE_MAP = {
    'gps':      'high',
    'manual':   'medium',
    'centroid': 'low',
}


def _recalculate_commune_metric(commune_id, service_slug):
    """
    Recalcula CommuneMetric para el mes actual.
    Llamada síncronamente tras crear cada SLAAlert (Fase 1).
    """
    if not commune_id:
        return

    today  = timezone.now().date()
    period = today.replace(day=1)

    alerts = SLAAlert.objects.filter(
        service_slug=service_slug,
    )

    from .models import Complaint
    complaints_ids = list(
        Complaint.objects.filter(
            commune_id=commune_id,
            service_slug=service_slug,
            created_at__year=today.year,
            created_at__month=today.month,
        ).values_list('id', flat=True)
    )

    total_complaints  = len(complaints_ids)
    relevant_alerts   = alerts.filter(complaint_id__in=complaints_ids)
    total_alerts      = relevant_alerts.count()
    total_violations  = relevant_alerts.filter(violation=True).count()
    violation_rate    = (
        total_violations / total_alerts if total_alerts > 0 else 0.0
    )

    from apps.core.models import Commune
    try:
        commune_name = Commune.objects.get(id=commune_id).name
    except Commune.DoesNotExist:
        commune_name = f'Comuna {commune_id}'

    CommuneMetric.objects.update_or_create(
        commune_id=commune_id,
        service_slug=service_slug,
        period=period,
        defaults={
            'commune_name':       commune_name,
            'total_complaints':   total_complaints,
            'total_alerts':       total_alerts,
            'total_violations':   total_violations,
            'violation_rate':     violation_rate,
        },
    )


def _process_sweeping(complaint_id, location, created_at, confidence, commune_id):
    """
    Cruce SLA para barrido.
    Busca microrutas a ≤50m de la denuncia y verifica ventana horaria.
    """
    nearby = SweepingMicroRoute.objects.filter(
        active=True,
        geom__isnull=False,
        geom__dwithin=(location, D(m=50)),
    ).select_related('macroroute')

    if not nearby.exists():
        return

    complaint_hour = created_at.hour

    for microroute in nearby:
        macro      = microroute.macroroute
        violation  = False

        if macro.start_time:
            start_hour = macro.start_time.hour
            end_hour   = macro.end_time.hour if macro.end_time else 23
            violation  = not (start_hour <= complaint_hour <= end_hour)

        distance = location.distance(microroute.geom) * 111320

        SLAAlert.objects.create(
            complaint_id    = complaint_id,
            service_slug    = 'sweeping-cleaning',
            route_type      = 'sweeping_microroute',
            route_id        = microroute.id,
            macroroute_code = macro.code,
            violation       = violation,
            distance_meters = round(distance, 2),
            confidence      = confidence,
        )

    _recalculate_commune_metric(commune_id, 'sweeping-cleaning')


def _process_green_zones(complaint_id, location, confidence, commune_id):
    """
    Cruce SLA para zonas verdes.
    Busca zonas a ≤30m y verifica si el ciclo de corte está vencido.
    """
    nearby = GreenZone.objects.filter(
        active=True,
        geom__isnull=False,
        geom__dwithin=(location, D(m=30)),
    )

    if not nearby.exists():
        return

    today = timezone.now().date()

    for zone in nearby:
        days_since = zone.days_since_last_intervention()
        violation  = False

        if days_since is None:
            # Sin intervención registrada — verificar programación vencida
            overdue = CuttingSchedule.objects.filter(
                zone=zone,
                scheduled_date__lt=today,
                executed=False,
            ).exists()
            violation = overdue
        else:
            violation = days_since > zone.cycle_days

        SLAAlert.objects.create(
            complaint_id          = complaint_id,
            service_slug          = 'green-zones',
            route_type            = 'green_zone',
            route_id              = zone.id,
            macroroute_code       = '',
            violation             = violation,
            days_since_intervention = days_since,
            confidence            = confidence,
        )

    _recalculate_commune_metric(commune_id, 'green-zones')


def handle_complaint_created(
    sender, complaint_id, service_slug,
    location, created_at, location_source,
    commune_id, **kwargs
):
    """
    Entry point principal del módulo de auditoría.
    Recibe la signal y delega al procesador correspondiente.
    """
    confidence = CONFIDENCE_MAP.get(location_source, 'low')

    if service_slug == 'sweeping-cleaning':
        _process_sweeping(
            complaint_id, location, created_at, confidence, commune_id
        )
    elif service_slug == 'green-zones':
        _process_green_zones(
            complaint_id, location, confidence, commune_id
        )


# Conectar el receiver a la signal
complaint_created.connect(handle_complaint_created)
