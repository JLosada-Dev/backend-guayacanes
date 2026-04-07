from django.contrib.gis.db import models


class Commune(models.Model):
    """
    9 comunas urbanas de Popayán.
    Fuente: U2_COMUNAS.shp (POT Popayán)
    Reproyección requerida: PCS_CAUCA_POPAYAN → EPSG:4326
    Cargado con: python manage.py load_communes
    """
    number        = models.IntegerField(unique=True)
    name          = models.CharField(max_length=50, blank=True)
    area_hectares = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    geom          = models.PolygonField(srid=4326)

    class Meta:
        db_table            = 'core_commune'
        ordering            = ['number']
        verbose_name        = 'Comuna'
        verbose_name_plural = 'Comunas'

    def __str__(self):
        return self.name or f'Comuna {self.number}'

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = f'Comuna {self.number}'
        super().save(*args, **kwargs)


class Neighborhood(models.Model):
    """
    Barrios de Popayán.
    Fuente: OSM (nombre) + DANE secciones urbanas (geometría fallback)
    El centroide de geom es el fallback de coordenada en vee_complaint
    cuando el ciudadano no activa GPS ni usa pin manual.
    """
    name      = models.CharField(max_length=150)
    commune   = models.ForeignKey(
        Commune,
        on_delete=models.PROTECT,
        related_name='neighborhoods',
    )
    osm_id    = models.CharField(max_length=50, blank=True)
    dane_code = models.CharField(max_length=25, blank=True)
    geom      = models.MultiPolygonField(srid=4326)

    class Meta:
        db_table            = 'core_neighborhood'
        ordering            = ['commune__number', 'name']
        verbose_name        = 'Barrio'
        verbose_name_plural = 'Barrios'

    def __str__(self):
        return f'{self.name} (C{self.commune.number})'

    @property
    def centroid(self):
        """Punto central del barrio. Usado como coordenada fallback en denuncias."""
        return self.geom.centroid
