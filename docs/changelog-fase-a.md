# Changelog Fase A — 14 abril 2026

Cambios aplicados para completar el pipeline SLA end-to-end y habilitar contenido editorial.

---

## Endpoints de la API

### Endpoints nuevos — Documentación OpenAPI/Swagger

Agregados via `drf-spectacular`. No son endpoints de negocio, son metadata del schema.

| Método | URL | Descripción |
|--------|-----|-------------|
| GET | `/api/schema/` | OpenAPI 3.0 schema (YAML) — descargable |
| GET | `/api/docs/` | Swagger UI — prueba interactiva de endpoints |
| GET | `/api/redoc/` | ReDoc — referencia navegable |

### Endpoints de negocio — Sin cambios estructurales

**Todos los 12 endpoints v1 siguen existiendo con las mismas URLs.** La Fase A no agregó ni removió endpoints de negocio — se mantuvieron los mismos paths y verbos HTTP documentados en [api/README.md](api/README.md).

**Sin embargo, el payload de 2 endpoints cambió** (se pobló data que antes era null):

| Endpoint | Antes Fase A | Después Fase A |
|----------|--------------|----------------|
| `GET /api/v1/core/services/` | `content: null` | `content: {icon, summary, full_description, frequency, citizen_rights, updated_at}` |
| `GET /api/v1/core/aspects/?service=<slug>` | `content: null` | `content: {icon, what_is, how_to_evidence, response_time, updated_at}` |

Los frontends que ya consumen estos endpoints no necesitan cambios — el campo `content` ya existía en el serializer, solo ahora retorna datos en lugar de null.

---

## Correcciones de lógica

### 🔴 Fix — Ventanas horarias de macrorutas

**Archivo:** [apps/infra_servicios_publicos_urbaser/management/commands/load_sweeping.py](../apps/infra_servicios_publicos_urbaser/management/commands/load_sweeping.py)

**Problema:** las 8 macrorutas tenían `end_time=null`, lo que hacía que el pipeline SLA considerara cualquier hora entre 5am-11pm como "dentro de ventana". Ninguna denuncia de barrido generaba violation por horario.

**Fix:** agregado `end_time` a cada macroruta según el contrato PPS 2024:

| Código | Start | End | Notas |
|--------|-------|-----|-------|
| B211, B212, B213 | 06:00 | 14:00 | Residencial semanal |
| 611 | 05:00 | 13:00 | Vías principales |
| 621 | 13:00 | 21:00 | Centro histórico tarde |
| 631B | 19:00 | 03:00 | Centro histórico noche (cruza medianoche) |
| 117B | 09:00 | 13:30 | Centro histórico dominical |
| 127B | 10:00 | 14:30 | Mercados dominical |

### 🔴 Fix — Lógica de ventana que cruza medianoche

**Archivo:** [apps/infra_servicios_publicos_urbaser/receivers.py](../apps/infra_servicios_publicos_urbaser/receivers.py)

**Problema:** la ruta 631B opera 19:00-03:00, cruzando medianoche. El check `start_hour <= complaint_hour <= end_hour` fallaba para hours como 22:00 (si end=3, `22 <= 3` es false).

**Fix:** detectar el caso `start > end` y usar lógica OR:
```python
if start_hour <= end_hour:
    in_window = start_hour <= complaint_hour <= end_hour
else:
    # Cruza medianoche
    in_window = complaint_hour >= start_hour or complaint_hour <= end_hour
```

**Impacto medible:** violations detectadas pasaron de **2 a 24** en el mismo dataset de prueba.

---

## Nuevos comandos de gestión

### `load_cutting_schedule`

**Archivo:** [apps/infra_servicios_publicos_urbaser/management/commands/load_cutting_schedule.py](../apps/infra_servicios_publicos_urbaser/management/commands/load_cutting_schedule.py)

Parsea `cronograma-de-cesped-febrero-2026.pdf` con `pdfplumber` y crea `CuttingSchedule` para las zonas verdes que matcheen.

**Estrategia de matching:** fuzzy match por nombre con `difflib.SequenceMatcher` (threshold 0.70).

**Resultado:** 31 schedules creados (31 zonas matcheadas de 290 filas del PDF). La limitación es estructural — el PDF usa nombres de barrio y los shapefiles usan landmarks (parques, coliseos).

**Uso:**
```bash
make data                                        # incluye load_cutting_schedule
uv run python manage.py load_cutting_schedule    # standalone
uv run python manage.py load_cutting_schedule --clear --verbose-match
```

---

## Nuevas fixtures

### `core_service_content.json`

**Archivo:** [fixtures/core_service_content.json](../fixtures/core_service_content.json)

Contenido editorial para los 2 servicios activos de Fase 1:
- `sweeping-cleaning` — icon `trash-2`, descripción + frecuencias + derechos ciudadanos
- `green-zones` — icon `leaf`, descripción + cronograma + derechos ciudadanos

Incluye referencias legales (Ley 1755/2015, Decreto 1077/2015, Resolución CRA 720).

### `core_aspect_content.json`

**Archivo:** [fixtures/core_aspect_content.json](../fixtures/core_aspect_content.json)

Contenido editorial para los 11 aspectos:
- 7 aspectos de barrido (scope, frequency, cleanliness, sand-residue, weed-removal, bins, quality)
- 4 aspectos de zonas verdes (cutting-not-done, frequency-missed, pruning-waste-left, area-deteriorated)

Cada aspecto incluye: icon Lucide, `what_is`, `how_to_evidence`, `response_time`.

---

## Nuevas dependencias

| Paquete | Versión | Uso |
|---------|---------|-----|
| `drf-spectacular` | 0.29.0 | Schema OpenAPI + Swagger UI + ReDoc |
| `pdfplumber` | 0.11.9 | Parsing del cronograma de cesped |

Regenerado:
- `requirements.txt`
- `requirements-dev.txt`

---

## Makefile — comandos actualizados

```makefile
make data   # ahora incluye fixtures de contenido + load_green_zones + load_cutting_schedule
make seed   # 14 denuncias de prueba
make demo   # migrate + data + seed (setup completo)
```

---

## Impacto medible

| Métrica | Antes | Después |
|---------|-------|---------|
| Violations detectadas (seed de 14 denuncias) | 2 | **24** |
| Services con contenido editorial | 0 | 2 |
| Aspects con contenido editorial | 0 | 11 |
| CuttingSchedules cargados | 1 (hardcoded) | **32** |
| Macrorutas con ventana horaria correcta | 0/8 | **8/8** |
| Endpoints Swagger/OpenAPI | 0 | 3 |
| Dependencias `uv` | — | +2 (drf-spectacular, pdfplumber) |

---

## Archivos nuevos

```
apps/infra_servicios_publicos_urbaser/management/commands/
  load_cutting_schedule.py

fixtures/
  core_service_content.json
  core_aspect_content.json

docs/
  changelog-fase-a.md     (este archivo)
  plan-accion-fase1.md    (plan de trabajo)
```

## Archivos modificados

```
apps/infra_servicios_publicos_urbaser/management/commands/
  load_sweeping.py        (end_time en 8 macrorutas)

apps/infra_servicios_publicos_urbaser/
  receivers.py            (ventana que cruza medianoche)

Makefile                  (make data incluye nuevos fixtures y commands)
pyproject.toml            (drf-spectacular, pdfplumber)
requirements.txt          (regenerado)
requirements-dev.txt      (regenerado)
docs/README.md            (Swagger URLs)
docs/api/README.md        (sección de Swagger)
docs/demo-guide.md        (paso de Swagger en el recorrido)
```
