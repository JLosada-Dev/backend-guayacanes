# Geodatos — Inventario y guía de carga

Todos los shapefiles del POT de Popayán están en:
```
guayacanes_docs/SHAPESPOT/SHAPES POT/
```

**CRS original de todos los shapefiles:** `PCS_CAUCA_POPAYAN` (Transverse Mercator local, sin código EPSG numérico).
**CRS destino en la BD:** `EPSG:4326` (WGS84). Los management commands hacen la reproyección automáticamente con geopandas.

---

## Capas en uso directo por el sistema

| Capa | Features | Tabla destino | Estado | Comando |
|------|----------|--------------|--------|---------|
| `U2_COMUNAS/U2_COMUNAS.shp` | 9 polígonos | `core_commune` | ✓ Cargado | `load_communes` |
| `U18_VIAL/U18_VIAL.shp` | 3,800 LineStrings | `urbaser_sweeping_microroute` | ✓ Cargado (1,731) | `load_sweeping` |
| `U-19 ESPACIO PUBLICO/U19_ESPACIO_PUBLICO1.shp` | 2 polígonos | `urbaser_green_zone` | ✓ Cargado | `load_green_zones` |
| `U-19 ESPACIO PUBLICO/U19_ESPACIO_PUBLICO2.shp` | 11 polígonos | `urbaser_green_zone` | ✓ Cargado | `load_green_zones` |
| `U-19 ESPACIO PUBLICO/U19_ESPACIO_PUBLICO3.shp` | 96 polígonos | `urbaser_green_zone` | ✓ Cargado | `load_green_zones` |
| `U-19 ESPACIO PUBLICO/U19_ESPACIO_PUBLICO5.shp` | 72 polígonos | `urbaser_green_zone` | ✓ Cargado | `load_green_zones` |
| `U1_POPAYAN BASE/SEPARADOR.shp` | 132 polígonos | `urbaser_green_zone` | ✓ Cargado | `load_green_zones` |

> Las 5 capas de espacio público se cargan juntas en `urbaser_green_zone` (**313 polígonos en BD**).
> `external_id` se genera por rango según la fuente (10001+ EP1, 20001+ EP2, 30001+ EP3, 50001+ EP5, 90001+ SEPARADOR).
> `cycle_days=11` por defecto (PPS 2024). Los nombres vienen del campo `NOMBRE` cuando existe (solo EP3), o se generan como `<tipo> NNN`.

---

## Cargar comunas

```bash
uv run python manage.py load_communes
uv run python manage.py load_communes --clear   # recargar desde cero
uv run python manage.py load_communes --shapefile "ruta/custom.shp"
```

## Cargar rutas de barrido

```bash
uv run python manage.py load_sweeping
uv run python manage.py load_sweeping --clear
```

Carga las 8 macrorutas del PPS 2024 con horarios fijos (start_time/end_time) y
asigna las 1,731 microrutas al macroruta correspondiente según el campo `Layer`
del shapefile.

## Cargar zonas verdes

```bash
uv run python manage.py load_green_zones
uv run python manage.py load_green_zones --clear
```

Lee los 5 shapefiles del espacio público + separadores, los reproyecta a EPSG:4326,
calcula el área en EPSG:3116 (metros reales), y crea 313 registros en
`urbaser_green_zone`.

## Shortcut con Make

```bash
make data    # todos los fixtures + geodatos de una vez
make seed    # + 14 denuncias de prueba (dispara pipeline SLA)
make demo    # migrate + data + seed (setup completo)
```

---

## Inventario completo de capas POT

Referencial — no todas se usan en el sistema.

| Carpeta | Descripción | Features aprox. | Uso |
|---------|-------------|----------------|-----|
| `U1_POPAYAN BASE/` | Mapa base (vías, ríos, manzanas, cotas, lotes…) | ~20 capas | Referencial |
| `U2_COMUNAS/` | 9 comunas urbanas | 9 | ✓ Cargado |
| `U3_POBLACION/` | Distribución poblacional | — | No usado |
| `U4_TELEFONIA/` | Cobertura telecom | — | No usado |
| `U5_EDUCACION/` | Instituciones educativas | — | No usado |
| `U6_SALUD/` | Centros de salud | — | No usado |
| `U7_EQUIPAMENTO/` | Equipamientos urbanos | — | No usado |
| `U-8= USO ACTUAL/` | Uso actual del suelo | — | No usado |
| `U9_SINCONSOLIDAR/` | Zonas sin consolidar | — | No usado |
| `U10_ZONASHOMOGENEAS2/` | Zonas homogéneas | — | No usado |
| `U11_GEOMORFOLOGICO/` | Geomorfología | — | No usado |
| `U11_GEOMORFOLOGICO/U22_TRATAMIENTOS/` | Tratamientos urbanísticos | — | No usado |
| `U12_MICROZONIFICACION/` | Microzonificación sísmica | — | No usado |
| `U13_USO PROYECTADO/` | Uso proyectado del suelo | — | No usado |
| `U14_ COMERCIALES/` | Zonas comerciales | — | No usado |
| `U15_EXPANSION/` | Áreas de expansión urbana | — | No usado |
| `U16_DESLIZAMIENTOS (1)/` | Riesgo de deslizamientos | — | No usado |
| `U17_INUNDACIONES/` | Riesgo de inundaciones | — | No usado |
| `U18_VIAL/` | Red vial — rutas de barrido | ~3,800 | ✓ Cargado (operaciones) |
| `U-19 ESPACIO PUBLICO/` | Zonas verdes (5 subcapas) | 181 total | ✓ Cargado (operaciones) |
| `U20_AREASESPECIALES/` | Áreas especiales | — | No usado |
| `U21_CENTRALIDADES/` | Centralidades urbanas | — | No usado |
| `U_23 INTERES AMBIENTAL/` | Interés ambiental | — | No usado |
| `U_23A VIS/` | Vivienda de interés social | — | No usado |
| `U30 UNIDADES DE PAIJASE RURAL/` | Paisaje rural | — | Fase 2 (rural) |

---

## Datos de barrios (Neighborhood)

No existe un shapefile oficial de barrios con nombres para Popayán.

**Lo que existe:**
- **DANE WFS (descargado):** 189 secciones urbanas censales — solo tienen códigos, sin nombres de barrio. Archivo: `guayacanes_docs/reporte_barrios_popayan.md` + shapefiles generados (popayan_seccion_urbana.\*).
- **Alcaldía de Popayán:** tiene una capa de 79 barrios con nombres pero sin geometría (PDF de estratificación).

**Estrategia actual:** `Neighborhood.geom` permite `null` temporalmente (migración `0002`). Los barrios se cargarán cuando se consiga geometría con nombres desde la Alcaldía o cruzando DANE + nombres conocidos.

---

## Notas de reproyección

El CRS `PCS_CAUCA_POPAYAN` es una proyección Transverse Mercator local:
- `central_meridian: -76.6060916`
- `latitude_of_origin: 2.4561599`
- `false_easting: 1,052,430.525`
- `false_northing: 763,366.548`

geopandas resuelve la reproyección con `gdf.to_crs(epsg=4326)` sin necesidad de definir el CRS manualmente — el `.prj` del shapefile tiene la definición completa.

Al convertir geometrías Shapely → GEOSGeometry usar `.wkt` directamente:
```python
geom = GEOSGeometry(row['geometry'].wkt, srid=4326)
```
No usar `str(row['geometry'].__geo_interface__)` — genera Python dict con comillas simples (JSON inválido).
