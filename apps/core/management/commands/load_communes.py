"""
Management command: load_communes
Carga las 9 comunas de Popayán desde el shapefile oficial del POT.

Fuente: ~/guayacanes_docs/SHAPESPOT/SHAPES POT/U2_COMUNAS/U2_COMUNAS.shp
CRS original: PCS_CAUCA_POPAYAN (sin EPSG numérico)
CRS destino:  EPSG:4326 (WGS84)

Uso:
    python manage.py load_communes
    python manage.py load_communes --shapefile /ruta/custom/U2_COMUNAS.shp
    python manage.py load_communes --clear
"""
from pathlib import Path

from django.contrib.gis.geos import GEOSGeometry
from django.core.management.base import BaseCommand

from apps.core.models import Commune

DEFAULT_SHAPEFILE = (
    Path.home()
    / 'guayacanes_docs'
    / 'SHAPESPOT'
    / 'SHAPES POT'
    / 'U2_COMUNAS'
    / 'U2_COMUNAS.shp'
)


class Command(BaseCommand):
    help = 'Carga las 9 comunas de Popayán desde U2_COMUNAS.shp'

    def add_arguments(self, parser):
        parser.add_argument(
            '--shapefile',
            default=str(DEFAULT_SHAPEFILE),
            help='Ruta al shapefile U2_COMUNAS.shp',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Elimina todas las comunas antes de cargar',
        )

    def handle(self, *args, **options):
        try:
            import geopandas as gpd
        except ImportError:
            self.stderr.write(self.style.ERROR(
                'geopandas no está instalado. Ejecuta: uv add geopandas'
            ))
            return

        shapefile = Path(options['shapefile'])
        if not shapefile.exists():
            self.stderr.write(self.style.ERROR(
                f'Shapefile no encontrado: {shapefile}'
            ))
            return

        if options['clear']:
            count = Commune.objects.count()
            Commune.objects.all().delete()
            self.stdout.write(self.style.WARNING(
                f'Eliminadas {count} comunas existentes.'
            ))

        self.stdout.write(f'Leyendo shapefile: {shapefile}')
        gdf = gpd.read_file(shapefile)
        self.stdout.write(f'CRS original: {gdf.crs}')
        self.stdout.write(f'Features encontrados: {len(gdf)}')

        # Reproyectar a WGS84
        gdf = gdf.to_crs(epsg=4326)
        self.stdout.write('Reproyectado a EPSG:4326')

        created = 0
        updated = 0

        for _, row in gdf.iterrows():
            number       = int(row['COMUNA'])
            area_has     = float(row.get('Area_Has', 0) or 0)
            geom         = GEOSGeometry(row['geometry'].wkt, srid=4326)

            commune, is_new = Commune.objects.update_or_create(
                number=number,
                defaults={
                    'name':          f'Comuna {number}',
                    'area_hectares': area_has,
                    'geom':          geom,
                },
            )

            if is_new:
                created += 1
                self.stdout.write(f'  + Creada: {commune}')
            else:
                updated += 1
                self.stdout.write(f'  ~ Actualizada: {commune}')

        self.stdout.write(self.style.SUCCESS(
            f'\nListo. {created} creadas, {updated} actualizadas.'
        ))
