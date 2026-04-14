# Guía del Panel de Administración — Guyacanes

URL: `http://localhost:8000/admin`
Crear superusuario: `python manage.py createsuperuser`

---

## Resumen de modelos registrados

| App | Modelo | Admin Class | Tipo | Editable |
|-----|--------|-------------|------|----------|
| core | Commune | `CommuneAdmin` | GISModelAdmin | Sí |
| core | Neighborhood | `NeighborhoodAdmin` | GISModelAdmin | Sí |
| core | Service | `ServiceAdmin` | ModelAdmin | Sí |
| core | Aspect | `AspectAdmin` | ModelAdmin | Sí |
| core | ServiceContent | `ServiceContentAdmin` | ModelAdmin | Sí |
| core | AspectContent | `AspectContentAdmin` | ModelAdmin | Sí |
| urbaser | Complaint | `ComplaintAdmin` | GISModelAdmin | Sí |
| urbaser | Evidence | `EvidenceAdmin` | ModelAdmin | Sí |
| urbaser | SweepingMacroRoute | `SweepingMacroRouteAdmin` | GISModelAdmin | Parcial |
| urbaser | SweepingMicroRoute | `SweepingMicroRouteAdmin` | GISModelAdmin | Solo `active` |
| urbaser | GreenZone | `GreenZoneAdmin` | GISModelAdmin | Sí |
| urbaser | CuttingSchedule | `CuttingScheduleAdmin` | ModelAdmin | Parcial |
| urbaser | Intervention | `InterventionAdmin` | ModelAdmin | Sí |
| urbaser | SLAAlert | `SLAAlertAdmin` | ModelAdmin | **Read-only** |
| urbaser | CommuneMetric | `CommuneMetricAdmin` | ModelAdmin | **Read-only** |

---

## GISModelAdmin — Mapa integrado

Los modelos marcados como `GISModelAdmin` muestran un mapa Leaflet/OpenStreetMap dentro del formulario de edición. Esto permite:
- Ver la geometría existente del registro
- Dibujar o editar geometrías directamente en el mapa

Los modelos con geometrías pendientes (`null=True`) muestran el mapa vacío hasta que se carguen datos via management commands.

---

## App: core — Catálogo transversal

### Commune (GISModelAdmin)

- **Lista:** número, nombre, área en hectáreas
- **Búsqueda:** por nombre y número
- **Orden:** por número de comuna
- **Mapa:** muestra el polígono de la comuna (cargado con `load_communes`)
- **Datos:** cargados desde `U2_COMUNAS.shp` — no editar manualmente

### Neighborhood (GISModelAdmin)

- **Lista:** nombre, comuna, código DANE, OSM ID
- **Filtros:** por comuna
- **Búsqueda:** por nombre
- **Orden:** por número de comuna, luego por nombre
- **Campo especial:** `raw_id_fields = ['commune']` — selección de comuna con popup de búsqueda
- **Geometría:** `null=True` — pendiente cargar desde shapefile DANE

### Service (ModelAdmin)

- **Lista:** nombre, slug, activo, orden
- **Filtros:** por estado `active`
- **Búsqueda:** por nombre y slug
- **Orden:** por campo `order`
- **Inline:** `ServiceContentInline` (StackedInline) — permite cargar el contenido editorial del servicio directamente desde la misma pantalla
- **Flujo operacional:** los líderes de operaciones usan este formulario para cargar `ServiceContent`

**ServiceContentInline — campos:**

| Campo | Descripción |
|-------|-------------|
| `icon` | Nombre del ícono Lucide para el portal ciudadano |
| `summary` | Descripción corta (máx 300 chars) |
| `full_description` | Texto completo del servicio |
| `frequency` | Frecuencia del servicio según contrato |
| `citizen_rights` | Derechos del ciudadano según PPS 2024 |

### Aspect (ModelAdmin)

- **Lista:** descripción, servicio, slug, activo
- **Filtros:** por servicio y estado `active`
- **Búsqueda:** por descripción y slug
- **Orden:** por `service.order`, luego descripción
- **Inline:** `AspectContentInline` (StackedInline) — contenido editorial por aspecto

**AspectContentInline — campos:**

| Campo | Descripción |
|-------|-------------|
| `icon` | Nombre del ícono Lucide |
| `what_is` | Explicación del problema para el ciudadano |
| `how_to_evidence` | Cómo documentar con fotos |
| `response_time` | Tiempo de respuesta según contrato |

### ServiceContent y AspectContent (ModelAdmin)

Registrados individualmente además de los inlines. Permiten edición directa sin pasar por el Servicio o Aspecto padre. Principalmente para búsquedas y auditoría de contenido.

---

## App: urbaser — Veeduría

### Complaint (GISModelAdmin)

El modelo central del sistema. Muestra un mapa con la ubicación de la denuncia.

**Lista:** `id`, `service_slug`, `aspect_description`, `commune_name`, `status`, `location_source`, `created_at`

**Filtros:** `status`, `service_slug`, `location_source`, `is_rural`

**Búsqueda:** `aspect_description`, `commune_name`, `neighborhood_name`

**Orden:** `-created_at` (más reciente primero)

**Campos read-only:** `created_at`

**Inline:** `EvidenceInline` — muestra las fotos adjuntas a la denuncia

**Fieldsets (secciones del formulario):**

| Sección | Campos |
|---------|--------|
| **Qué** | `service_id`, `service_slug`, `service_name`, `aspect_id`, `aspect_slug`, `aspect_description` |
| **Dónde** | `commune_id`, `commune_name`, `neighborhood_id`, `neighborhood_name`, `is_rural`, `hamlet_name`, `location`, `location_source` |
| **Contexto** | `description`, `status`, `created_at` |

> Los campos `_slug` y `_name` son snapshots — se llenaron automáticamente al crear la denuncia desde el catálogo. Modificarlos manualmente rompe la consistencia.

### Evidence (ModelAdmin)

- **Lista:** id, complaint (FK), uploaded_at
- **Orden:** `-uploaded_at`
- **Read-only:** `uploaded_at`
- Normalmente se accede via el inline de Complaint, no directamente

---

## App: urbaser — Operaciones

### SweepingMacroRoute (GISModelAdmin)

Rutas de barrido del PPS 2024. Cargadas con `load_sweeping`.

- **Lista:** código, nombre, tipo de zona, días, hora inicio, activo
- **Filtros:** `zone_type`, `active`
- **Búsqueda:** código, nombre
- **Orden:** por código
- **Read-only:** `code` — identificador oficial inmutable
- **Inline:** `SweepingMicroRouteInline` — muestra las microrutas asociadas

**SweepingMicroRouteInline:**
- Solo muestra `layer` y `active`
- `layer` es read-only (valor del shapefile)
- `can_delete = False` — las microrutas solo se gestionan via `load_sweeping`
- `max_num = 0` — no se pueden agregar manualmente desde el admin
- Etiqueta: _"Microrutas (solo lectura — cargadas desde shapefile)"_

### SweepingMicroRoute (GISModelAdmin)

Microrutas individuales del vial (LineStrings del U18_VIAL.shp).

- **Lista:** id, macroruta, layer, activo
- **Filtros:** `macroroute`, `layer`, `active`
- **Orden:** por código de macroruta
- **Read-only:** `macroroute`, `layer`, `geom` — datos del shapefile, no editar
- El único campo editable es `active`

### GreenZone (GISModelAdmin)

Zonas verdes del espacio público POT. **313 zonas cargadas** desde 5 shapefiles combinados (parques, nodos, corredores verdes, separadores).

- **Lista:** `external_id`, nombre, tipo de zona, área m², ciclo días, activo
- **Filtros:** `zone_type`, `active`
- **Búsqueda:** nombre, external_id
- **Orden:** por nombre
- **Inlines:** `CuttingScheduleInline` + `InterventionInline`

**CuttingScheduleInline:**
- Muestra el cronograma de cortes programados de la zona
- `scheduled_date`, `month`, `year` son read-only (del PDF de cronograma)
- Solo `executed` es editable — para marcar cortes realizados manualmente

**InterventionInline:**
- Registra intervenciones ejecutadas (cortes reales)
- `extra = 1` — siempre muestra un formulario vacío para agregar intervención
- Al guardar una intervención, el sistema marca automáticamente el `CuttingSchedule` correspondiente como `executed = True`

### CuttingSchedule (ModelAdmin)

Cronograma de cortes programados por zona verde.

- **Lista:** zona, fecha programada, mes, año, ejecutado
- **Filtros:** `executed`, `year`, `month`
- **Búsqueda:** nombre de la zona
- **Orden:** por `scheduled_date`

### Intervention (ModelAdmin)

Registro de intervenciones ejecutadas (cortes reales realizados por Urbaser).

- **Lista:** zona, fecha ejecución, tipo de intervención, responsable
- **Filtros:** `intervention_type`
- **Búsqueda:** nombre de zona, responsable
- **Orden:** `-execution_date`

---

## App: urbaser — Auditoría (Read-Only)

### SLAAlert (ModelAdmin) — Solo lectura

**NUNCA se crean manualmente.** Se generan automáticamente via signal `post_save` de `Complaint`.

- **Lista:** id, complaint_id, service_slug, route_type, macroroute_code, violation, distance_meters, confidence, generated_at
- **Filtros:** `violation`, `service_slug`, `route_type`, `confidence`
- **Búsqueda:** `complaint_id`, `macroroute_code`
- **Orden:** `-generated_at`
- **Todos los campos son read-only**
- `has_add_permission = False` — no aparece el botón "Agregar"
- `has_change_permission = False` — no se puede editar ningún campo

**Uso del admin:** Solo consulta y monitoreo. Para depurar alertas incorrectas, revisar `receivers.py`.

### CommuneMetric (ModelAdmin) — Solo lectura

**NUNCA se crean manualmente.** Se recalculan automáticamente al generar un `SLAAlert`.

- **Lista:** commune_name, service_slug, total_complaints, total_violations, violation_rate, period, updated_at
- **Filtros:** `service_slug`, `period`
- **Orden:** `-period`, luego `commune_id`
- **Todos los campos son read-only**
- `has_add_permission = False`
- `has_change_permission = False`

**Uso del admin:** Verificar que las métricas del heatmap sean correctas. Si `violation_rate` parece incorrecto, revisar los `SLAAlert` de esa comuna y periodo.

---

## Flujo operacional recomendado

### Onboarding inicial (una vez)

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py loaddata fixtures/core_services.json
python manage.py loaddata fixtures/core_aspects.json
python manage.py load_communes
python manage.py load_sweeping
```

### Cargar contenido editorial (líder de operaciones)

1. Ir a `/admin/core/service/`
2. Seleccionar el servicio
3. Completar el inline `ServiceContent` con textos para el portal ciudadano
4. Repetir en `/admin/core/aspect/` para cada aspecto

### Monitorear denuncias

1. Ir a `/admin/infra_servicios_publicos_urbaser/complaint/`
2. Filtrar por `status=received` para ver denuncias pendientes
3. Cambiar `status` a `under_review` al asignar al equipo
4. Cambiar a `closed` al resolver

### Monitorear cumplimiento SLA

1. Ir a `/admin/infra_servicios_publicos_urbaser/slaalert/`
2. Filtrar por `violation=true` para ver incumplimientos
3. Cruzar con `/admin/infra_servicios_publicos_urbaser/communemetric/` para ver tendencias por comuna
