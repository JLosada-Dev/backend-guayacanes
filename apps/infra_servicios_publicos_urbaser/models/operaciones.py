from django.contrib.gis.db import models


class SweepingMacroRoute(models.Model):
    """
    Macroruta de barrido del PPS 2024 — Tabla 9.
    8 macrorutas del contrato Urbaser.

    Fuente: Macrorutas-Publicar-Barrido-2024.pdf
    Códigos: B211, B212, B213, 611, 621, 631b, 117b, 127b

    geom (MultiPolygon): área de cobertura — null hasta tener
    polígonos oficiales validados.
    """
    ZONE_TYPE_CHOICES = [
        ('residential',   'Residencial — comunas'),
        ('main_roads',    'Vías principales'),
        ('historic_center', 'Centro histórico'),
        ('market',        'Plazas de mercado'),
        ('sunday',        'Servicio dominical'),
    ]

    code           = models.CharField(max_length=10, unique=True)
    name           = models.CharField(max_length=300)
    zone_type      = models.CharField(
        max_length=20,
        choices=ZONE_TYPE_CHOICES,
        default='residential',
    )
    communes_text  = models.CharField(
        max_length=50, blank=True,
        help_text='Ej: "1,2,3,8,9"',
    )
    days_text      = models.CharField(
        max_length=50, blank=True,
        help_text='Ej: "Lu-Ju", "Lu-Sá", "Domingo"',
    )
    schedule_text  = models.CharField(
        max_length=100, blank=True,
        help_text='Texto original del horario: "6:00"',
    )
    start_time     = models.TimeField(
        null=True, blank=True,
        help_text='Parseado para comparación numérica en SLA',
    )
    end_time       = models.TimeField(
        null=True, blank=True,
        help_text='Null si no hay fin explícito en el PPS',
    )
    active         = models.BooleanField(default=True)
    geom           = models.MultiPolygonField(
        srid=4326, null=True, blank=True,
        help_text='Área de cobertura — null hasta tener polígonos oficiales',
    )

    class Meta:
        db_table            = 'urbaser_sweeping_macroroute'
        ordering            = ['code']
        verbose_name        = 'Macroruta de barrido'
        verbose_name_plural = 'Macrorutas de barrido'

    def __str__(self):
        return f'Barrido {self.code} — {self.name}'


class SweepingMicroRoute(models.Model):
    """
    Trayecto individual de barrido — LineString.
    Fuente: U18_VIAL.shp (POT Popayán) — 3,800 LineStrings
    Reproyección: PCS_CAUCA_POPAYAN → EPSG:4326
    Cargado con: python manage.py load_sweeping

    PostGIS usa este campo para el cruce SLA:
      ST_DWithin(complaint.location, geom, D(m=50))
    """
    macroroute        = models.ForeignKey(
        SweepingMacroRoute,
        on_delete=models.CASCADE,
        related_name='microroutes',
    )
    layer             = models.CharField(
        max_length=50, blank=True,
        help_text='Del shapefile: VC1, VARIANT, VAP-2',
    )
    # Soft FK a core_neighborhood
    neighborhood_id   = models.IntegerField(null=True, blank=True)
    neighborhood_name = models.CharField(max_length=150, blank=True)
    active            = models.BooleanField(default=True)
    geom              = models.LineStringField(srid=4326)

    class Meta:
        db_table            = 'urbaser_sweeping_microroute'
        ordering            = ['macroroute__code']
        verbose_name        = 'Microruta de barrido'
        verbose_name_plural = 'Microrutas de barrido'

    def __str__(self):
        return f'{self.macroroute.code} — {self.layer}'


class GreenZone(models.Model):
    """
    Área verde bajo responsabilidad de Urbaser.
    Fuente geometría: combinar 4 shapefiles del POT:
      U19_ESPACIO_PUBLICO2.shp  (11 parques)
      U19_ESPACIO_PUBLICO3.shp  (96 nodos)
      U19_ESPACIO_PUBLICO5.shp  (72 corredores)
      SEPARADOR.shp             (132 separadores)

    external_id: ID del polígono en el cronograma PDF de Urbaser.
    ciclo_dias: 11 días según datos reales de febrero 2026.

    geom null=True hasta cruzar shapefiles con cronograma PDF.
    """
    ZONE_TYPE_CHOICES = [
        ('park',        'Parque público'),
        ('road_divider','Separador vial'),
        ('bike_path',   'Ciclovía'),
        ('roundabout',  'Glorieta / rotonda'),
        ('sports',      'Polideportivo'),
        ('other',       'Otro'),
    ]

    external_id       = models.IntegerField(
        unique=True,
        help_text='ID del polígono en el cronograma PDF de Urbaser',
    )
    name              = models.CharField(max_length=300)
    zone_type         = models.CharField(
        max_length=20,
        choices=ZONE_TYPE_CHOICES,
        default='park',
    )
    area_sqm          = models.DecimalField(
        max_digits=12, decimal_places=2,
        null=True, blank=True,
        help_text='Área en m² del cronograma PDF',
    )
    cycle_days        = models.IntegerField(
        default=11,
        help_text='Días entre cortes según contrato',
    )
    # Soft FK a core_neighborhood
    neighborhood_id   = models.IntegerField(null=True, blank=True)
    neighborhood_name = models.CharField(max_length=150, blank=True)
    active            = models.BooleanField(default=True)
    geom              = models.MultiPolygonField(
        srid=4326, null=True, blank=True,
        help_text='Polígono del área — null hasta cruzar con shapefiles POT',
    )

    class Meta:
        db_table            = 'urbaser_green_zone'
        ordering            = ['name']
        verbose_name        = 'Zona verde'
        verbose_name_plural = 'Zonas verdes'

    def __str__(self):
        return f'{self.name} (ID {self.external_id})'

    def days_since_last_intervention(self):
        """
        Días desde el último corte registrado.
        Usado por aud/receivers.py para determinar incumplimiento.
        """
        from django.utils import timezone
        last = self.interventions.order_by('-execution_date').first()
        if not last:
            return None
        return (timezone.now().date() - last.execution_date).days


class CuttingSchedule(models.Model):
    """
    Fecha programada de corte según el cronograma mensual de Urbaser.
    Fuente: cronograma-de-cesped-febrero-2026.pdf y meses siguientes.

    Si scheduled_date ya pasó y executed=False → incumplimiento directo.
    """
    zone             = models.ForeignKey(
        GreenZone,
        on_delete=models.CASCADE,
        related_name='schedules',
    )
    scheduled_date   = models.DateField()
    month            = models.IntegerField()
    year             = models.IntegerField()
    executed         = models.BooleanField(default=False)

    class Meta:
        db_table        = 'urbaser_cutting_schedule'
        ordering        = ['scheduled_date']
        verbose_name    = 'Programación de corte'
        verbose_name_plural = 'Programaciones de corte'
        unique_together = [['zone', 'scheduled_date']]

    def __str__(self):
        return f'{self.zone.name} — {self.scheduled_date}'


class Intervention(models.Model):
    """
    Registro de cuándo SÍ se ejecutó el corte.
    Al guardar marca automáticamente schedule.executed = True.
    """
    INTERVENTION_TYPE_CHOICES = [
        ('grass_cut',    'Corte de césped'),
        ('tree_pruning', 'Poda de árbol'),
    ]

    zone             = models.ForeignKey(
        GreenZone,
        on_delete=models.CASCADE,
        related_name='interventions',
    )
    schedule         = models.ForeignKey(
        CuttingSchedule,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='interventions',
    )
    execution_date   = models.DateField()
    intervention_type = models.CharField(
        max_length=15,
        choices=INTERVENTION_TYPE_CHOICES,
        default='grass_cut',
    )
    recorded_by      = models.CharField(max_length=150, blank=True)
    notes            = models.TextField(blank=True)

    class Meta:
        db_table            = 'urbaser_intervention'
        ordering            = ['-execution_date']
        verbose_name        = 'Intervención registrada'
        verbose_name_plural = 'Intervenciones registradas'

    def __str__(self):
        return f'{self.zone.name} — {self.get_intervention_type_display()} {self.execution_date}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.schedule and not self.schedule.executed:
            self.schedule.executed = True
            self.schedule.save(update_fields=['executed'])
