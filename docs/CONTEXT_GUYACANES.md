# GUYACANES — Contexto del Proyecto
# Sistema de Servicios Públicos — Alcaldía de Popayán
# Versión definitiva — Marzo 2026

---

## ROL DE ESTE CHAT

Este chat actúa como **tercero de confianza y líder técnico** del proyecto.
El desarrollador usa Claude Code y Gemini como agentes de ejecución.
Este chat NO ejecuta código — revisa decisiones de arquitectura, detecta
errores de diseño antes de que los agentes implementen, mantiene la
coherencia del sistema y guía a los agentes con instrucciones precisas.

Regla: el desarrollador NO re-explica decisiones ya tomadas.
Todo lo necesario está en este documento.

---

## QUÉ ES ESTE PROYECTO

Sistema de supervisión y veeduría ciudadana para el servicio público
de aseo urbano de Urbaser Popayán S.A. E.S.P. contratado con la
Alcaldía de Popayán, Cauca.

Cruza el "deber ser" (rutas contractuales del PPS 2024) contra la
"realidad" (denuncias ciudadanas georeferenciadas) usando PostGIS
para detectar incumplimientos SLA automáticamente.

Este sistema es el primer módulo de una plataforma más grande de la
Alcaldía. Otros servicios públicos (acueducto, vivienda, etc.) tendrán
sus propias apps independientes en el futuro.

---

## STACK TECNOLÓGICO

- Backend:     Django 6 + DRF + GeoDjango + djangorestframework-gis
- Base datos:  PostgreSQL 16 + PostGIS — SRID 4326 en todo el sistema
- Frontend:    React + Vite + TypeScript (esperando template — NO iniciado)
- Python env:  uv como herramienta principal (José) — pip + venv para el resto del equipo
- Python version: 3.13 (uv python pin 3.13)
- Compatibilidad: requirements.txt y requirements-dev.txt generados con
  `uv export --format requirements-txt --no-hashes`
  Se mantienen actualizados cada vez que cambian las dependencias
- Regla: nadie instala dependencias globalmente — uv sync o pip install -r requirements.txt
- Infra local: Docker solo para PostgreSQL+PostGIS y Redis
- Storage:     media_local/ (sin S3 por ahora) — MEDIA_ROOT = BASE_DIR / 'media_local'
- Async:       Celery + Redis — solo para facturación (Fase 2)

Convención de código: TODO en inglés — nombres de clases, campos,
métodos, comentarios técnicos. Solo texto visible al usuario final
(verbose_name, descripciones en fixtures) en español.

---

## VERSIONES INSTALADAS (confirmadas)

- Python:                  3.13.12
- Django:                  6.0.3
- djangorestframework:     3.17.1
- djangorestframework-gis: 1.0
- django-cors-headers:     4.9.0
- django-filter:           25.2
- psycopg2-binary:         2.9.11
- python-decouple:         3.8
- Pillow:                  12.1.1
- pytest:                  9.0.2
- pytest-django:           4.12.0

---

## NOMBRE DEL PROYECTO

```
guyacanes
```

---

## ARQUITECTURA — UNA APP POR SERVICIO PÚBLICO

Cada servicio público de la Alcaldía es una app Django independiente.
Equipos distintos, migraciones independientes, deploys sin coordinación.

```
guyacanes/
  core/                                          ← toda la Alcaldía lee de aquí
  infra_servicios_publicos_urbaser/              ← servicio de aseo — ESTE SISTEMA
  infra_servicios_publicos_urbaser_facturacion/  ← facturación aseo — en espera
  infra_servicios_publicos_acueducto/            ← futuro
  infra_servicios_publicos_vivienda/             ← futuro
```

---

## APP: core — catálogo transversal de la Alcaldía

Usada por TODOS los servicios públicos. Nunca importa de ninguna
otra app. Solo se escribe al cargar datos iniciales.

```
core/
  models/
    geography.py    ← Commune + Neighborhood
    catalog.py      ← Service + Aspect
```

### Prefijos de tabla: core_*

### Model: Commune (db_table: core_commune)
```
number          IntegerField UNIQUE         # 1–9
name            CharField(50)               # "Comuna 1"
area_hectares   DecimalField(10,2)          # del shapefile POT
geom            PolygonField(4326)          # límite de la comuna
```
Fuente: U2_COMUNAS.shp — requiere reproyección PCS_CAUCA_POPAYAN → 4326

### Model: Neighborhood (db_table: core_neighborhood)
```
name            CharField(150)
commune         ForeignKey → Commune (hard FK, PROTECT)
geom            MultiPolygonField(4326)     # centroide = fallback GPS
```
Fuente: shapefile DANE MGN 2022 — pendiente URL exacta
El centroide del barrio es el fallback de coordenada cuando el
ciudadano no tiene GPS ni usa pin en el mapa.

### Model: Service (db_table: core_service)
```
name            CharField(100) UNIQUE
slug            SlugField UNIQUE            # referencia estable entre módulos
description     TextField
active          BooleanField default=True
order           PositiveSmallIntegerField
```

Fixtures Phase 1 (active=True):
  slug=sweeping-cleaning  → Barrido y Limpieza
  slug=green-zones        → Corte de Césped y Zonas Verdes

Fixtures Phase 2 (active=False):
  slug=waste-collection   → Recolección y Transporte
  slug=street-washing     → Lavado de Vías
  slug=tree-pruning       → Poda de Árboles

### Model: Aspect (db_table: core_aspect)
```
service         ForeignKey → Service (hard FK, PROTECT)
slug            SlugField
description     CharField(200)
active          BooleanField
unique_together: [service, slug]
```

Fixtures Barrido (7):
  scope, frequency, cleanliness, sand-residue,
  weed-removal, bins, quality

Fixtures Zonas Verdes (4):
  cutting-not-done, frequency-missed,
  pruning-waste-left, area-deteriorated

---

## APP: infra_servicios_publicos_urbaser

Tres módulos internos dentro de una sola app Django.
Migraciones independientes de core y de facturación.

```
infra_servicios_publicos_urbaser/
  models/
    operaciones.py    ← rutas de barrido + zonas verdes
    veeduria.py       ← denuncias ciudadanas
    auditoria.py      ← alertas SLA + métricas dashboard
  signals.py          ← emite complaint_created
  receivers.py        ← escucha signal, ejecuta PostGIS
  admin.py            ← GISModelAdmin con Leaflet
  serializers.py
  views.py
  urls.py
  migrations/
  management/
    commands/
      load_sweeping.py
      load_green_zones.py
```

### Prefijos de tabla: urbaser_*

---

## MODELOS — operaciones.py

### Model: SweepingMacroRoute (db_table: urbaser_sweeping_macroroute)
```
code            CharField(10) UNIQUE
name            CharField(300)
zone_type       CharField(20)   # residential/main_roads/historic_center/market/sunday
communes_text   CharField(50)   # "1,2,3,8,9"
days_text       CharField(50)   # "Mon-Thu"
schedule_text   CharField(100)  # "6:00" texto original
start_time      TimeField null
end_time        TimeField null
active          BooleanField
geom            MultiPolygonField(4326) null  # área cobertura — pendiente
```

8 macrorutas del PPS 2024:
  B211: comunas 1,2,3,8,9 · Lu-Ju · 06:00
  B212: comunas 2,4,5,7,8,9 · Ma-Vi · 06:00
  B213: comunas 3,4,5,6,7 · Mi-Sá · 06:00
  611:  todas · Lu-Sá · 05:00 (vías principales + centro + mercados)
  621:  comuna 4 · Lu-Sá · 13:00 (centro tarde)
  631b: comuna 4 · Lu-Sá · 19:00 (centro noche)
  117b: comuna 4 · Domingo · 09:00
  127b: comuna 4 · Domingo · 10:00 (mercados)

### Model: SweepingMicroRoute (db_table: urbaser_sweeping_microroute)
```
macroroute      ForeignKey → SweepingMacroRoute (CASCADE)
layer           CharField(50)   # VC1, VARIANT, VAP-2
neighborhood_id IntegerField null  # soft FK
neighborhood_name CharField(150)
active          BooleanField
geom            LineStringField(4326)  # ST_DWithin 50m para SLA
```
Fuente: U18_VIAL.shp — 3,800 LineStrings oficiales del POT
Requiere reproyección PCS_CAUCA_POPAYAN → 4326

### Model: GreenZone (db_table: urbaser_green_zone)
```
external_id     IntegerField UNIQUE   # ID del cronograma PDF Urbaser
name            CharField(300)
zone_type       CharField(20)   # park/road_divider/bike_path/roundabout/sports/other
area_sqm        DecimalField null
cycle_days      IntegerField default=11
neighborhood_id IntegerField null  # soft FK
neighborhood_name CharField(150)
active          BooleanField
geom            MultiPolygonField(4326) null  # pendiente cruce con shapefiles
```

Fuentes para geom (combinar y reproyectar):
  U19_ESPACIO_PUBLICO2.shp → 11 parques urbanos recreativos
  U19_ESPACIO_PUBLICO3.shp → 96 nodos espacio público
  U19_ESPACIO_PUBLICO5.shp → 72 rondas de ríos, corredores verdes
  SEPARADOR.shp            → 132 separadores viales
  Total: ~311 polígonos oficiales del POT

290 polígonos del PPS 2024 con área total 1,648,366.47 m²

### Model: CuttingSchedule (db_table: urbaser_cutting_schedule)
```
zone            ForeignKey → GreenZone (CASCADE)
scheduled_date  DateField
month           IntegerField
year            IntegerField
executed        BooleanField default=False
unique_together: [zone, scheduled_date]
```

### Model: Intervention (db_table: urbaser_intervention)
```
zone            ForeignKey → GreenZone (CASCADE)
schedule        ForeignKey → CuttingSchedule null (SET_NULL)
execution_date  DateField
intervention_type CharField(10)  # grass_cut / tree_pruning
recorded_by     CharField(150)
notes           TextField
```
Al guardar: marca schedule.executed = True automáticamente

---

## MODELOS — veeduria.py

### Model: Complaint (db_table: urbaser_complaint)
```
# Qué — soft FKs a core (validadas en serializer, sin FK en BD)
service_id          IntegerField
service_slug        CharField(100)    # snapshot
service_name        CharField(100)    # snapshot
aspect_id           IntegerField
aspect_slug         CharField(100)    # snapshot
aspect_description  CharField(200)    # snapshot

# Dónde — soft FK a core_neighborhood
neighborhood_id     IntegerField null
neighborhood_name   CharField(150)    # snapshot
is_rural            BooleanField default=False
hamlet_name         CharField(150)    # veredas rurales si is_rural=True

# Coordenada — NUNCA NULL
location            PointField(4326)
location_source     CharField(10)     # gps / manual / centroid

# Contexto
description         TextField blank
status              CharField(15)     # received / under_review / closed
created_at          DateTimeField auto_now_add
```

REGLA CRÍTICA: location NUNCA NULL.
Cascada en serializer: GPS → pin manual → centroide barrio → error 400

### Model: Evidence (db_table: urbaser_evidence)
```
complaint       ForeignKey → Complaint (CASCADE)
image           ImageField upload_to='complaints/%Y/%m/'
uploaded_at     DateTimeField auto_now_add
```

---

## MODELOS — auditoria.py

### Model: SLAAlert (db_table: urbaser_sla_alert)
```
complaint_id        IntegerField db_index  # soft FK
service_slug        CharField(100)
route_type          CharField(20)   # sweeping_microroute / green_zone
route_id            IntegerField
macroroute_code     CharField(10)   # B211, 611… para reportes oficiales
violation           BooleanField
distance_meters     FloatField null
days_since_intervention IntegerField null  # solo zonas verdes
confidence          CharField(5)    # high / medium / low
generated_at        DateTimeField auto_now_add
```

NUNCA se crea manualmente — solo por signal post_save.

Lógica SLA:
  Barrido:      ST_DWithin(location, urbaser_sweeping_microroute.geom, D(m=50))
                + hora denuncia fuera de ventana macroruta → violation=True
  Zonas verdes: ST_DWithin(location, urbaser_green_zone.geom, D(m=30))
                + days_since_intervention > zone.cycle_days → violation=True
                + schedule.executed=False con fecha pasada → violation directa

### Model: CommuneMetric (db_table: urbaser_commune_metric)
```
commune_id              IntegerField      # soft FK
commune_name            CharField(50)     # snapshot
service_slug            CharField(100)
total_complaints        IntegerField default=0
total_alerts            IntegerField default=0
total_violations        IntegerField default=0
violation_rate          FloatField default=0.0   # 0.0–1.0
period                  DateField
updated_at              DateTimeField auto_now
unique_together: [commune_id, service_slug, period]
```

Heatmap dashboard:
  violation_rate > 0.70 → rojo   (crítico)
  violation_rate > 0.40 → naranja (atención)
  violation_rate ≤ 0.40 → verde  (conforme)

---

## REGLAS DE ARQUITECTURA — NUNCA VIOLAR

```
core                    → no importa de ninguna app
infra_servicios_*       → puede importar de core únicamente
veeduria (modelos)      → no conoce auditoria
auditoria               → lee de operaciones + core, escribe solo en sus tablas
facturacion             → app completamente separada, independiente

FKs duras:    solo dentro del mismo archivo de modelos
Soft FKs:     entre módulos — siempre con snapshot de texto
Signals:      veeduria emite → auditoria escucha (nunca import directo)
```

### Flujo de signal
```
urbaser_complaint.save()
  → post_save → signals.py emite complaint_created
    → receivers.py escucha
      → ejecuta PostGIS query
        → crea SLAAlert
          → recalcula CommuneMetric (síncrono Fase 1)
```

---

## GEODATOS DISPONIBLES

### Shapefiles POT Popayán (56 archivos analizados)
CRS: 55/56 usan PCS_CAUCA_POPAYAN (sin EPSG numérico)
     1/56 usa EPSG:3115
Todos requieren reproyección a EPSG:4326

### USO DIRECTO en el sistema:

| Shapefile | Features | Destino en BD |
|-----------|----------|---------------|
| U2_COMUNAS.shp | 9 | core_commune |
| U18_VIAL.shp | 3,800 | urbaser_sweeping_microroute.geom |
| U19_ESPACIO_PUBLICO2.shp | 11 | urbaser_green_zone.geom |
| U19_ESPACIO_PUBLICO3.shp | 96 | urbaser_green_zone.geom |
| U19_ESPACIO_PUBLICO5.shp | 72 | urbaser_green_zone.geom |
| SEPARADOR.shp | 132 | urbaser_green_zone.geom |

### PENDIENTE:
- Shapefile barrios DANE MGN 2022 → core_neighborhood
  URL base: https://geoportal.dane.gov.co/
  Buscar: Marco Geoestadístico Nacional → Popayán → Barrios urbanos

### DESCARTAR (no útiles para el sistema):
- Archivos con 32 cols CAD sin atributos semánticos
- COTAS, geología, geomorfología
- Inundaciones, deslizamientos
- Telefonía, salud, educación
- Archivos con Id=0 o DocVer=None

### Reproyección requerida (todos los shapefiles POT):
```python
# Con geopandas — usando uv, nada global
import geopandas as gpd
gdf = gpd.read_file('U2_COMUNAS.shp')
gdf_wgs84 = gdf.to_crs(epsg=4326)
```

---

## RUTAS DEL CONTRATO PPS 2024

### Barrido y Limpieza — 222 rutas totales
Macrorutas urbanas activas en Fase 1:
  B211, B212, B213 — residencial (semanal por días)
  611 — vías principales + centro + mercados (Lu-Sá 05:00)
  621 — centro histórico tarde (Lu-Sá 13:00)
  631b — centro histórico noche (Lu-Sá 19:00)
  117b — centro histórico domingo (09:00)
  127b — mercados domingo (10:00)

### Recolección — 32 rutas urbanas + 3 rurales (Fase 2)
  Diurnas LMV (7): 311, 313, 315, 316, 317, 318, 319
  Diurnas MJS (7): 312, 314, 320, 321, 322, 323, 324
  Nocturnas LMV (8): 331, 333, 334, 335, 336, 337, 338, 339
  Nocturnas MJS (7): 332, 340, 341, 342, 343, 344, 345
  Rurales (3): 211 Occidente, 212 Nororiente, 213 Suroriente
  Fuente: MACRO-RECOLECCION-2024.pdf

### Zonas Verdes
  290 polígonos · área total 1,648,366.47 m²
  Ciclo contractual: ~11 días entre cortes
  Cronograma mensual: cronograma-cesped-febrero-2026.pdf
  Inventario arbóreo: 18,123 árboles — Fase 2
    (direcciones textuales, requiere geocodificación)

---

## MANAGEMENT COMMANDS

```
load_communes       ← U2_COMUNAS.shp → core_commune
load_neighborhoods  ← shapefile DANE → core_neighborhood (pendiente)
load_sweeping       ← U18_VIAL.shp → urbaser_sweeping_macroroute + microroute
                      bulk_create batch_size=500
load_green_zones    ← combinar 4 shapefiles espacio público → urbaser_green_zone
                      reproyectar + cruzar con cronograma PDF por nombre
```

---

## HOJA DE RUTA

### Fase 0 — Contexto y arquitectura ← COMPLETADA
```
✓ Modelos diseñados
✓ 56 shapefiles POT analizados
✓ Rutas documentadas (barrido + recolección + zonas verdes)
✓ Nombre proyecto: guyacanes
✓ App principal: infra_servicios_publicos_urbaser
✓ Arquitectura: una app por servicio público
✓ Contexto actualizado
□ Shapefile barrios DANE — pendiente URL
```

### Fase 1 — Backend base ← SIGUIENTE
```
□ uv init guyacanes
□ docker-compose.yml (PostgreSQL+PostGIS + Redis)
□ Django project init + settings (base/local/production)
□ Crear apps: core + infra_servicios_publicos_urbaser
              + infra_servicios_publicos_urbaser_facturacion (vacía)
□ Escribir modelos (inglés, db_table explícito)
□ makemigrations + migrate
□ Fixtures: servicios + aspectos
□ Management commands: load_communes, load_sweeping, load_green_zones
□ Admin con Leaflet (GISModelAdmin)
```

### Fase 2 — API REST
```
□ Serializers + ViewSets
□ Endpoints core (communes, neighborhoods, services, aspects)
□ Endpoints veeduría (POST complaint, GET complaints)
□ Signals + receivers PostGIS
□ Endpoints auditoría (alerts, heatmap, summary)
```

### Fase 3 — Frontend
```
□ React + Vite + TypeScript (esperando template)
□ Portal ciudadano — formulario denuncia
□ Dashboard Alcaldía — heatmap + tabla alertas
```

### Fase 4 — Expansión
```
□ Recolección activa (32 rutas documentadas)
□ Inventario arbóreo (geocodificación PDFs)
□ Facturación (Celery + Redis)
```

---

## CONVENCIONES PARA AGENTES

- José usa uv — los agentes usan uv en sus comandos
- El resto del equipo usa pip + venv con requirements.txt
- Cada vez que se añade una dependencia con uv, regenerar:
  `uv export --format requirements-txt --no-hashes -o requirements.txt`
  `uv export --format requirements-txt --no-hashes --dev -o requirements-dev.txt`
- Docker solo para BD y Redis — app server corre directamente
- db_table explícito en cada Meta
- Prefijos de tabla: core_* · urbaser_* · urbaser_fac_*
- Geometrías sin datos aún: null=True, blank=True
- Soft FKs siempre acompañadas de campo _name snapshot
- No choices hardcodeados en frontend — siempre fetch de /api/core/
- Geometrías pendientes no bloquean el sistema:
  receivers.py filtra geom__isnull=False antes de ST_DWithin
