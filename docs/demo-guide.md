# Guía de Demo — Backend Guyacanes

Estado al **14 abril 2026**: backend listo para demo end-to-end sin frontend.

---

## Arrancar de cero

```bash
# 1. Limpiar contenedores previos (si existen)
docker rm guyacanes_db guyacanes_redis 2>/dev/null

# 2. Levantar Docker + servidor Django
make dev

# 3. En otra terminal: migrate + cargar todo + seed denuncias
make demo
```

`make demo` ejecuta: `migrate` → fixtures → `load_communes` → `load_sweeping` → `load_green_zones` → `seed_complaints`.

---

## Datos cargados tras `make demo`

| Recurso | Cantidad | Origen |
|---------|----------|--------|
| Comunas | 9 | `U2_COMUNAS.shp` |
| Servicios | 5 (2 activos Fase 1) | `fixtures/core_services.json` |
| Aspectos | 11 | `fixtures/core_aspects.json` |
| Macrorutas de barrido | 8 | `U18_VIAL.shp` + datos PPS 2024 |
| Microrutas de barrido | 1,731 | `U18_VIAL.shp` |
| Zonas verdes | 313 | 5 shapefiles U-19 + SEPARADOR |
| Denuncias de prueba | 14 | `seed_complaints` |
| Alertas SLA | 27 | Auto-generadas por signal |
| Violations | 2 | Auto-detectadas |
| Métricas por comuna | 5 | Auto-calculadas |

---

## Recorrido sugerido para demo

### 1. Panel Admin — `http://localhost:8000/admin`

Crear superusuario primero:
```bash
uv run python manage.py createsuperuser
```

**Mostrar en este orden:**

1. **Catálogo → Servicios y Aspectos**
   Los 5 servicios con sus aspectos. Mostrar que se puede cargar `ServiceContent` y `AspectContent` con icono, descripción, derechos ciudadanos.

2. **Operaciones → Macrorutas de Barrido**
   Las 8 macrorutas del PPS 2024 con su schedule. Abrir una (ej: B211) y mostrar las microrutas inline y el mapa Leaflet.

3. **Operaciones → Zonas Verdes**
   Las 313 zonas. Abrir "CAMPESTRE" — mostrar geometría en el mapa + CuttingSchedule vencido + Intervenciones.

4. **Veeduría → Denuncias**
   Las 14 denuncias de prueba. Filtrar por `status=received`. Abrir una con GPS y mostrar la ubicación en el mapa.

5. **Auditoría → Alertas SLA** (read-only)
   27 alertas. Filtrar por `violation=True` para ver los 2 incumplimientos. Destacar los campos `distance_meters` y `confidence`.

6. **Auditoría → Métricas de Comuna** (read-only)
   5 métricas. Mostrar `violation_rate` = 0.50 para Comuna 5 · green-zones.

### 2. API — Bruno o curl

**Portal ciudadano (lectura de catálogo):**
```bash
curl http://localhost:8000/api/v1/core/services/
curl "http://localhost:8000/api/v1/core/aspects/?service=sweeping-cleaning"
curl http://localhost:8000/api/v1/core/communes/
```

**Crear denuncia end-to-end:**
```bash
curl -X POST http://localhost:8000/api/v1/urbaser/complaints/ \
  -H "Content-Type: application/json" \
  -d '{
    "service_id": 1,
    "aspect_id": 2,
    "commune_id": 7,
    "latitude": 2.4675,
    "longitude": -76.5896,
    "location_source": "gps",
    "description": "Demo en vivo"
  }'
```

→ Retorna 201. Inmediatamente el pipeline genera alertas.

**Ver alertas generadas:**
```bash
curl http://localhost:8000/api/v1/urbaser/alerts/?violation=true
```

**Heatmap (métricas por comuna):**
```bash
curl http://localhost:8000/api/v1/urbaser/metrics/
```

**GeoJSON para el mapa del dashboard:**
```bash
curl http://localhost:8000/api/v1/urbaser/complaints/geojson/
```

### 3. Colección Bruno lista para importar

`docs/api/guyacanes.bruno/` — importar en Bruno y apuntar al environment `local`.

---

## Puntos clave para resaltar en el demo

1. **Snapshots soft FK**: las denuncias guardan `service_name`, `aspect_description`, `commune_name` como texto. Aunque se borre un servicio, las denuncias históricas conservan la info.

2. **Cascada de coordenada**: el serializer acepta GPS, pin manual o solo `commune_id`. Si no hay GPS, usa el centroide de la comuna como fallback. Siempre hay `location` (nunca null).

3. **Pipeline SLA automático**: al crear una denuncia, el signal `post_save` dispara receivers que ejecutan `ST_DWithin` en PostGIS (EPSG:3116 para metros reales) y generan SLA alerts + actualizan métricas. Todo síncrono en el mismo request.

4. **Admin read-only para auditoría**: SLAAlert y CommuneMetric son inmutables — no se pueden editar ni crear manualmente.

5. **Confianza según fuente GPS**: GPS = high, pin manual = medium, centroide = low. Las alertas incluyen esta clasificación.

---

## Flujo limpio entre demos

Para resetear el estado entre demos:

```bash
# Opción A: borra todo y vuelve a cargar
uv run python manage.py seed_complaints --clear
uv run python manage.py seed_complaints

# Opción B: flush completo
uv run python manage.py flush --no-input
make demo
```

---

## Lo que NO está en el demo (y por qué)

| Feature | Estado | Justificación |
|---------|--------|---------------|
| Autenticación JWT | Pendiente | Se agrega post-demo. Demo interno no requiere auth. |
| Frontend React | Pendiente template | Se muestra el backend con admin + Bruno/Postman. |
| Barrios con geometría | null | No bloquea: fallback a centroide de comuna. Ver `docs/barrios-opciones.md`. |
| Facturación | Fase 2 | Fuera de alcance. |
| Recolección de basura | Fase 2 | Fuera de alcance. |
| Inventario arbóreo | Fase 2 | Fuera de alcance (18,123 árboles pendientes). |
