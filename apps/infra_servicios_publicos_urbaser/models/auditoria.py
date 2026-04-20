from django.db import models


class SLAAlert(models.Model):
    """
    Resultado del cruce espacial PostGIS.
    Generada AUTOMÁTICAMENTE por receivers.py al recibir
    la signal complaint_created.

    NUNCA se crea manualmente.

    Lógica por servicio:
      sweeping-cleaning:
        ST_DWithin(complaint.location, urbaser_sweeping_microroute.geom, D(m=50))
        + hora denuncia fuera de ventana horaria de la macroruta
        → violation=True

      green-zones:
        ST_DWithin(complaint.location, urbaser_green_zone.geom, D(m=30))
        + days_since_last_intervention > zone.cycle_days
        → violation=True
        + schedule.executed=False con fecha pasada → violation directa
    """
    ROUTE_TYPE_CHOICES = [
        ('sweeping_microroute', 'Microruta de barrido'),
        ('green_zone',         'Zona verde'),
    ]

    CONFIDENCE_CHOICES = [
        ('high',   'Alta — coordenada GPS'),
        ('medium', 'Media — pin manual'),
        ('low',    'Baja — centroide barrio'),
    ]

    # Soft FK a urbaser_complaint
    complaint_id              = models.IntegerField(db_index=True)
    service_slug              = models.CharField(max_length=100)

    # Qué ruta o zona fue afectada
    route_type                = models.CharField(
        max_length=25,
        choices=ROUTE_TYPE_CHOICES,
    )
    route_id                  = models.IntegerField()
    macroroute_code           = models.CharField(
        max_length=10, blank=True,
        help_text='Código del PPS para reportes oficiales: B211, 611…',
    )

    # Resultado del análisis
    violation                 = models.BooleanField()
    distance_meters           = models.FloatField(
        null=True, blank=True,
        help_text='Distancia en metros entre la denuncia y la ruta',
    )
    days_since_intervention   = models.IntegerField(
        null=True, blank=True,
        help_text='Solo zonas verdes — días desde el último corte',
    )
    confidence                = models.CharField(
        max_length=6,
        choices=CONFIDENCE_CHOICES,
        default='high',
    )
    generated_at              = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table            = 'urbaser_sla_alert'
        ordering            = ['-generated_at']
        verbose_name        = 'Alerta SLA'
        verbose_name_plural = 'Alertas SLA'
        indexes = [
            models.Index(fields=['complaint_id'],  name='idx_alert_complaint'),
            models.Index(fields=['violation'],     name='idx_alert_violation'),
            models.Index(fields=['service_slug'],  name='idx_alert_service'),
            models.Index(fields=['generated_at'],  name='idx_alert_date'),
            models.Index(fields=['route_type', 'route_id'], name='idx_alert_route'),
        ]

    def __str__(self):
        estado = 'INCUMPLIMIENTO' if self.violation else 'Conforme'
        return f'Alerta #{self.id} — {estado} ({self.route_type})'


class CommuneMetric(models.Model):
    """
    Caché estadístico precalculado por comuna y servicio.
    Alimenta el heatmap del dashboard sin queries costosas.

    Recalculada síncronamente tras cada nueva SLAAlert (Fase 1).
    En Fase 2 se mueve a tarea Celery asíncrona.

    Colores del heatmap:
      violation_rate > 0.70 → rojo   (crítico)
      violation_rate > 0.40 → naranja (atención)
      violation_rate ≤ 0.40 → verde  (conforme)
    """
    # Soft FK a core_commune
    commune_id              = models.IntegerField()
    commune_name            = models.CharField(max_length=50)
    service_slug            = models.CharField(max_length=100)

    # Contadores precalculados
    total_complaints        = models.IntegerField(default=0)
    total_alerts            = models.IntegerField(default=0)
    total_violations        = models.IntegerField(default=0)
    violation_rate          = models.FloatField(
        default=0.0,
        help_text='Fracción 0.0–1.0. violations / alerts',
    )
    period                  = models.DateField(
        help_text='Primer día del mes calculado',
    )
    updated_at              = models.DateTimeField(auto_now=True)

    class Meta:
        db_table            = 'urbaser_commune_metric'
        ordering            = ['-period', 'commune_id']
        verbose_name        = 'Métrica por comuna'
        verbose_name_plural = 'Métricas por comuna'
        unique_together     = [['commune_id', 'service_slug', 'period']]
        indexes = [
            models.Index(
                fields=['period', 'service_slug'],
                name='idx_metric_period',
            ),
        ]

    def __str__(self):
        return f'C{self.commune_id} · {self.service_slug} · {self.period}'
