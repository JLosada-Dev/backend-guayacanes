"""
Management command: load_sweeping
Carga las macrorutas y microrutas de barrido desde U18_VIAL.shp

Fuente: ~/guayacanes_docs/SHAPESPOT/SHAPES POT/U18_VIAL/U18_VIAL.shp
CRS original: PCS_CAUCA_POPAYAN (sin EPSG numérico)
CRS destino:  EPSG:4326 (WGS84)
Features: 3,800 LineStrings con campo Layer (VC1, VARIANT, VAP-2)

Las macrorutas se crean desde MACROROUTES_DEF — datos del PPS 2024.
Las microrutas se asignan a la macroruta según el campo Layer del shapefile.

Uso:
    python manage.py load_sweeping
    python manage.py load_sweeping --shapefile /ruta/custom/U18_VIAL.shp
    python manage.py load_sweeping --clear
"""
from datetime import time
from pathlib import Path

from django.contrib.gis.geos import GEOSGeometry
from django.core.management.base import BaseCommand

from apps.infra_servicios_publicos_urbaser.models import (
    SweepingMacroRoute,
    SweepingMicroRoute,
)

DEFAULT_SHAPEFILE = (
    Path.home()
    / 'guayacanes_docs'
    / 'SHAPESPOT'
    / 'SHAPES POT'
    / 'U18_VIAL'
    / 'U18_VIAL.shp'
)

# Definición de las 8 macrorutas del PPS 2024
# Fuente: Macrorutas-Publicar-Barrido-2024.pdf
MACROROUTES_DEF = {
    'B211': {
        'name':          'Comunas 1,2,3,8,9 — Lu-Ju 06:00',
        'zone_type':     'residential',
        'communes_text': '1,2,3,8,9',
        'days_text':     'Lu-Ju',
        'schedule_text': '6:00',
        'start_time':    time(6, 0),
    },
    'B212': {
        'name':          'Comunas 2,4,5,7,8,9 — Ma-Vi 06:00',
        'zone_type':     'residential',
        'communes_text': '2,4,5,7,8,9',
        'days_text':     'Ma-Vi',
        'schedule_text': '6:00',
        'start_time':    time(6, 0),
    },
    'B213': {
        'name':          'Comunas 3,4,5,6,7 — Mi-Sá 06:00',
        'zone_type':     'residential',
        'communes_text': '3,4,5,6,7',
        'days_text':     'Mi-Sá',
        'schedule_text': '6:00',
        'start_time':    time(6, 0),
    },
    '611': {
        'name':          'Vías principales + Centro + Mercados — Lu-Sá 05:00',
        'zone_type':     'main_roads',
        'communes_text': '1,2,3,4,5,6,7,8,9',
        'days_text':     'Lu-Sá',
        'schedule_text': '5:00',
        'start_time':    time(5, 0),
    },
    '621': {
        'name':          'Centro histórico tarde — Lu-Sá 13:00',
        'zone_type':     'historic_center',
        'communes_text': '4',
        'days_text':     'Lu-Sá',
        'schedule_text': '13:00',
        'start_time':    time(13, 0),
    },
    '631b': {
        'name':          'Centro histórico nocturno — Lu-Sá 19:00',
        'zone_type':     'historic_center',
        'communes_text': '4',
        'days_text':     'Lu-Sá',
        'schedule_text': '19:00',
        'start_time':    time(19, 0),
    },
    '117b': {
        'name':          'Centro histórico — Domingo 09:00',
        'zone_type':     'sunday',
        'communes_text': '4',
        'days_text':     'Domingo',
        'schedule_text': '9:00',
        'start_time':    time(9, 0),
    },
    '127b': {
        'name':          'Plazas de mercado — Domingo 10:00',
        'zone_type':     'market',
        'communes_text': '4',
        'days_text':     'Domingo',
        'schedule_text': '10:00',
        'start_time':    time(10, 0),
    },
}

# Mapeo de Layer del shapefile → macroruta
# VC1 y VARIANT son las capas principales del shapefile U18_VIAL
LAYER_TO_MACROROUTE = {
    'VC1':     '611',
    'VARIANT': 'B211',
    'VAP-2':   'B212',
}


class Command(BaseCommand):
    help = 'Carga macrorutas y microrutas de barrido desde U18_VIAL.shp'

    def add_arguments(self, parser):
        parser.add_argument(
            '--shapefile',
            default=str(DEFAULT_SHAPEFILE),
            help='Ruta al shapefile U18_VIAL.shp',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Elimina todas las rutas antes de cargar',
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
            n_micro = SweepingMicroRoute.objects.count()
            n_macro = SweepingMacroRoute.objects.count()
            SweepingMicroRoute.objects.all().delete()
            SweepingMacroRoute.objects.all().delete()
            self.stdout.write(self.style.WARNING(
                f'Eliminados: {n_macro} macrorutas, {n_micro} microrutas.'
            ))

        # Paso 1 — Crear las 8 macrorutas
        self.stdout.write('Creando macrorutas del PPS 2024...')
        macroroutes = {}
        for code, data in MACROROUTES_DEF.items():
            obj, created = SweepingMacroRoute.objects.update_or_create(
                code=code,
                defaults={**data, 'active': True},
            )
            macroroutes[code] = obj
            marca = '+ Creada' if created else '~ Actualizada'
            self.stdout.write(f'  {marca}: {obj}')

        # Paso 2 — Leer shapefile y reproyectar
        self.stdout.write(f'\nLeyendo shapefile: {shapefile}')
        gdf = gpd.read_file(shapefile)
        self.stdout.write(f'CRS original: {gdf.crs}')
        self.stdout.write(f'Features: {len(gdf)}')
        gdf = gdf.to_crs(epsg=4326)
        self.stdout.write('Reproyectado a EPSG:4326')

        # Paso 3 — Bulk create microrutas por macroruta
        self.stdout.write('\nImportando microrutas...')
        total_created = 0
        omitted       = 0

        for layer_value, macro_code in LAYER_TO_MACROROUTE.items():
            subset = gdf[gdf['Layer'] == layer_value]
            if subset.empty:
                self.stdout.write(
                    self.style.WARNING(f'  Layer "{layer_value}" no encontrado en shapefile')
                )
                continue

            macro   = macroroutes[macro_code]
            batch   = []

            for _, row in subset.iterrows():
                if row['geometry'] is None:
                    omitted += 1
                    continue
                geom = GEOSGeometry(row['geometry'].wkt, srid=4326)
                batch.append(SweepingMicroRoute(
                    macroroute=macro,
                    layer=layer_value,
                    active=True,
                    geom=geom,
                ))

            # bulk_create en lotes de 500
            for i in range(0, len(batch), 500):
                SweepingMicroRoute.objects.bulk_create(batch[i:i + 500])

            total_created += len(batch)
            self.stdout.write(
                f'  Layer {layer_value} → {macro_code}: {len(batch)} microrutas'
            )

        if omitted:
            self.stdout.write(
                self.style.WARNING(f'Features omitidos (geom nula): {omitted}')
            )

        self.stdout.write(self.style.SUCCESS(
            f'\nListo. {len(macroroutes)} macrorutas, {total_created} microrutas.'
        ))
