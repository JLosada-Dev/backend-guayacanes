from django.db import models


class Service(models.Model):
    """
    Catálogo de servicios públicos auditables.
    Cargado con fixtures/core_services.json
    Fase 1 activos: sweeping-cleaning, green-zones
    Fase 2 inactivos: waste-collection, street-washing, tree-pruning
    """
    name        = models.CharField(max_length=100, unique=True)
    slug        = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    active      = models.BooleanField(default=True)
    order       = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table            = 'core_service'
        ordering            = ['order', 'name']
        verbose_name        = 'Servicio'
        verbose_name_plural = 'Servicios'

    def __str__(self):
        return self.name


class Aspect(models.Model):
    """
    Subcategorías de queja por servicio.
    Cargado con fixtures/core_aspects.json
    Sweeping (7): scope, frequency, cleanliness, sand-residue,
                  weed-removal, bins, quality
    Green zones (4): cutting-not-done, frequency-missed,
                     pruning-waste-left, area-deteriorated
    """
    service     = models.ForeignKey(
        Service,
        on_delete=models.PROTECT,
        related_name='aspects',
    )
    slug        = models.SlugField()
    description = models.CharField(max_length=200)
    active      = models.BooleanField(default=True)

    class Meta:
        db_table        = 'core_aspect'
        ordering        = ['service', 'description']
        verbose_name    = 'Aspecto'
        verbose_name_plural = 'Aspectos'
        unique_together = [['service', 'slug']]

    def __str__(self):
        return f'{self.service.name} — {self.description}'


class ServiceContent(models.Model):
    """
    Contenido informativo de un servicio público.
    Editado por líderes de operaciones desde el admin.
    El ícono es un nombre de Lucide Icons (ej: 'trash-2', 'leaf').
    """
    service        = models.OneToOneField(
        Service,
        on_delete=models.CASCADE,
        related_name='content',
    )
    icon           = models.CharField(
        max_length=50,
        help_text='Nombre del ícono Lucide. Ej: trash-2, leaf, droplets',
    )
    summary        = models.CharField(
        max_length=300,
        help_text='Descripción corta visible en el formulario (máx 300 chars)',
    )
    full_description = models.TextField(
        help_text='Descripción completa del servicio y sus obligaciones contractuales',
    )
    frequency      = models.CharField(
        max_length=200, blank=True,
        help_text='Ej: Lunes a sábado según macroruta de tu zona',
    )
    citizen_rights = models.TextField(
        blank=True,
        help_text='Derechos del ciudadano según el PPS 2024',
    )
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        db_table            = 'core_service_content'
        verbose_name        = 'Contenido informativo del servicio'
        verbose_name_plural = 'Contenidos informativos de servicios'

    def __str__(self):
        return f'Contenido — {self.service.name}'


class AspectContent(models.Model):
    """
    Contenido informativo de un aspecto de queja.
    Ayuda al ciudadano a entender qué está reportando
    y cómo recopilar evidencia útil.
    """
    aspect          = models.OneToOneField(
        Aspect,
        on_delete=models.CASCADE,
        related_name='content',
    )
    icon            = models.CharField(
        max_length=50,
        help_text='Nombre del ícono Lucide. Ej: alert-circle, camera',
    )
    what_is         = models.TextField(
        help_text='Explicación de qué es este problema y cuándo ocurre',
    )
    how_to_evidence = models.TextField(
        help_text='Cómo el ciudadano puede documentar este problema con fotos',
    )
    response_time   = models.CharField(
        max_length=100, blank=True,
        help_text='Tiempo de respuesta según contrato. Ej: 24 horas',
    )
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table            = 'core_aspect_content'
        verbose_name        = 'Contenido informativo del aspecto'
        verbose_name_plural = 'Contenidos informativos de aspectos'

    def __str__(self):
        return f'Contenido — {self.aspect.description}'
