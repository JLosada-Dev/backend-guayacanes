# Barrios de Popayán — Opciones de carga

Estado actual: `core_neighborhood.geom = null`. El sistema funciona sin barrios gracias al fallback a centroide de comuna. Este documento lista las opciones investigadas para cargar barrios reales cuando se decida implementarlo.

---

## Contexto del problema

Los shapefiles del POT de Popayán que ya están en `guayacanes_docs/SHAPESPOT/SHAPES POT/` **no contienen datos de barrios**:

| Shapefile | Contenido | Sirve para barrios |
|-----------|-----------|-------------------|
| `U2_COMUNAS.shp` | 9 comunas | No |
| `U3_POBLACION.shp` | 9 polígonos (uno por comuna) con datos de densidad | No |
| `U1_POPAYAN BASE/MANZANAS.shp` | 4,712 manzanas CAD sin atributos semánticos | No |
| `U1_POPAYAN BASE/LOTE.shp` | Lotes individuales sin barrio | No |

**Conclusión:** Los shapefiles del POT son de uso urbanístico, no estadístico. No traen nombre de barrio ni código DANE.

---

## Opción 1 — DANE MGN 2022 (RECOMENDADA)

Fuente oficial del gobierno colombiano. Cobertura completa con código DANE por sector urbano.

### Pro
- Oficial y exhaustivo
- Código DANE único por barrio/sector
- Geometría en EPSG:4326 directamente
- Consistencia con el resto del Estado colombiano

### Contra
- Requiere descarga manual (el portal no expone URL directa estable)
- Archivo grande (ZIP con todos los municipios del departamento)

### Cómo descargar

1. Ir a [geoportal.dane.gov.co/servicios/descarga-y-metadatos](https://geoportal.dane.gov.co/servicios/descarga-y-metadatos/)
2. Buscar "Marco Geoestadístico Nacional (MGN)"
3. Seleccionar versión **MGN Urbano 2022**
4. Filtrar: Departamento = **Cauca (19)**, Municipio = **Popayán (19001)**
5. Descargar el ZIP
6. Extraer — buscar el shapefile a nivel de sector urbano

### Atributos esperados

| Campo | Descripción |
|-------|-------------|
| `COD_DANE_A` | Código DANE oficial del sector (ej: `19001000101`) |
| `NOMBRE_SEC` | Nombre del sector/barrio |
| `COD_MPIO` | Código municipal (Popayán = `19001`) |
| `NOM_MPIO` | `POPAYAN` |
| `geometry` | MultiPolygon en EPSG:4326 |

### Implementación

Crear `apps/core/management/commands/load_neighborhoods.py` similar a `load_communes.py`:

```python
# Pseudo-código
for row in gdf.itertuples():
    commune_number = int(row.COD_DANE_A[7:9])  # extraer comuna del código DANE
    commune = Commune.objects.get(number=commune_number)
    Neighborhood.objects.update_or_create(
        dane_code=row.COD_DANE_A,
        defaults={
            'name': row.NOMBRE_SEC,
            'commune': commune,
            'geom': GEOSGeometry(row.geometry.wkt, srid=4326),
        }
    )
```

Luego agregar al `Makefile` dentro del target `data`.

### Enlaces

- [Geoportal DANE - Descargas](https://geoportal.dane.gov.co/servicios/descarga-y-metadatos/)
- [Manual MGN (PDF)](https://geoportal.dane.gov.co/descargas/descarga_mgn/Manual_MGN.pdf)
- [Guía de descarga MGN](https://geoportal.dane.gov.co/descargas/descarga_mgn/GuiaDescargaVisualiz_CO.pdf)
- [Geovisor MGN](https://geoportal.dane.gov.co/geovisores/territorio/mgn-marco-geoestadistico-nacional/)

---

## Opción 2 — OpenStreetMap (Overpass API)

Datos comunitarios. Automatizable pero con cobertura incompleta en Popayán.

### Pro
- Automatizable via API
- No requiere descarga manual
- Datos abiertos bajo licencia ODbL

### Contra
- Cobertura incompleta en Popayán (ciudades pequeñas tienen menos contribuidores)
- Sin código DANE
- Nombres inconsistentes entre contribuidores
- Servidor público con rate limiting y saturación frecuente

### Consulta Overpass

```
[out:json][timeout:90];
area["name"="Popayán"][admin_level="8"]->.p;
(
  node["place"~"^(suburb|neighbourhood|quarter)$"](area.p);
  way["place"~"^(suburb|neighbourhood|quarter)$"](area.p);
  relation["boundary"="administrative"]["admin_level"~"^(10|11)$"](area.p);
);
out geom;
```

### Endpoints

- Principal: `https://overpass-api.de/api/interpreter`
- Mirror: `https://overpass.kumi.systems/api/interpreter`
- Visual: [overpass-turbo.eu](https://overpass-turbo.eu)

### Implementación

```python
import requests, geopandas as gpd
from shapely.geometry import shape

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
QUERY = """...ver arriba..."""

resp = requests.post(OVERPASS_URL, data={'data': QUERY}, timeout=120)
data = resp.json()
# parsear elements y convertir a geometrías
```

### Enlaces

- [Overpass API Wiki](https://wiki.openstreetmap.org/wiki/Overpass_API)
- [Overpass Turbo (editor visual)](https://overpass-turbo.eu)
- [OSM Colombia - Geofabrik](https://download.geofabrik.de/south-america/colombia.html)

---

## Opción 3 — Geofabrik OSM Colombia completo

Descargar Colombia entera de OSM y filtrar Popayán localmente.

### Pro
- No depende de disponibilidad de Overpass API
- Permite procesamiento offline
- Incluye toda la data de OSM (no solo barrios)

### Contra
- Archivo grande (~800 MB comprimido)
- Mismo problema de cobertura que OSM directo
- Requiere herramientas extras (`osmium-tool`, `ogr2ogr`)

### Comandos

```bash
# Descargar Colombia
wget https://download.geofabrik.de/south-america/colombia-latest.osm.pbf

# Filtrar Popayán con osmium
osmium extract -b -76.70,2.40,-76.54,2.55 colombia-latest.osm.pbf -o popayan.osm.pbf

# Extraer barrios a shapefile
osmium tags-filter popayan.osm.pbf place=suburb,neighbourhood -o barrios.osm.pbf
ogr2ogr -f "ESRI Shapefile" barrios.shp barrios.osm.pbf multipolygons
```

---

## Opción 4 — Alcaldía de Popayán

Solicitar directamente a la Secretaría de Planeación Municipal el shapefile de barrios oficial de la ciudad.

### Pro
- Datos locales actualizados
- Potencialmente más detallados que DANE
- Incluye delimitaciones de barrios informales y asentamientos

### Contra
- Depende de relación institucional
- Sin garantía de disponibilidad ni formato
- Puede venir en CRS local (PCS_CAUCA_POPAYAN) que requiere reproyección

### Contacto

Secretaría de Planeación Municipal — Alcaldía de Popayán
[popayan.gov.co](https://www.popayan.gov.co)

---

## Opción 5 — Dejar pendiente (estado actual)

No cargar barrios. El sistema funciona con la cascada:

```
Denuncia → GPS (high confidence)
        → Pin manual (medium confidence)
        → Centroide de comuna (low confidence)
```

### Pro
- Sin trabajo adicional
- Sistema operativo hoy mismo
- Sin dependencia de fuentes externas

### Contra
- `neighborhood_id` y `neighborhood_name` en denuncias siempre null/vacíos
- Heatmap y auditoría se hacen solo a nivel de comuna, no de barrio
- Precisión del location_source = `centroid` es baja (centroide de comuna es muy amplio)

---

## Recomendación

**Fase 1 (ahora):** Dejar pendiente (Opción 5). El sistema funciona. Los barrios no son bloqueantes para la detección de SLA — ese pipeline usa las rutas de barrido, no los barrios.

**Fase 2 (cuando se decida):** Implementar Opción 1 (DANE MGN). Requiere que alguien del equipo o de la Alcaldía descargue el ZIP manualmente una sola vez. Después es reproducible con `load_neighborhoods` en el Makefile.

**Si hay que decidir rápido sin descarga manual:** Opción 2 (Overpass) aceptando la cobertura incompleta. Usarla como fallback mientras se consigue el MGN oficial.

---

## Decisión pendiente

- [ ] Definir quién descarga el MGN 2022 del DANE
- [ ] Implementar `apps/core/management/commands/load_neighborhoods.py`
- [ ] Agregar `load_neighborhoods` al target `data` del Makefile
- [ ] Actualizar `docs/CONTEXT_GUYACANES.md` removiendo el `PENDIENTE` de barrios
- [ ] Remover la migration `0002_neighborhood_geom_nullable` o dejar el campo como `null=True` opcional
