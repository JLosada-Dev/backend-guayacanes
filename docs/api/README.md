# Guyacanes API v1 — Colecciones

## Endpoints disponibles

| Método | URL | Descripción |
|--------|-----|-------------|
| GET | /api/v1/core/services/ | Servicios activos |
| GET | /api/v1/core/aspects/?service=\<slug\> | Aspectos por servicio |
| GET | /api/v1/core/communes/ | 9 comunas de Popayán |
| POST | /api/v1/urbaser/complaints/ | Crear denuncia |
| GET | /api/v1/urbaser/complaints/ | Listar denuncias |
| GET | /api/v1/urbaser/complaints/{id}/ | Detalle denuncia |
| GET | /api/v1/urbaser/complaints/geojson/ | Mapa GeoJSON |
| POST | /api/v1/urbaser/evidence/ | Subir foto |
| GET | /api/v1/urbaser/alerts/ | Alertas SLA (filtro: violation, service_slug, complaint_id) |
| GET | /api/v1/urbaser/alerts/{id}/ | Detalle alerta SLA |
| GET | /api/v1/urbaser/metrics/ | Métricas heatmap por comuna (filtro: service_slug, period) |
| GET | /api/v1/urbaser/metrics/{id}/ | Detalle métrica de una comuna |

## Importar en Postman
1. Abrir Postman
2. Import → Upload Files
3. Seleccionar `docs/api/guyacanes.postman_collection.json`
4. Configurar variable `base_url` = `http://localhost:8000`

## Importar en Bruno
1. Abrir Bruno
2. Open Collection
3. Seleccionar carpeta `docs/api/guyacanes.bruno/`
4. Activar environment `local`

## Variable de entorno
base_url = http://localhost:8000

## Campos de contenido informativo

### GET /api/v1/core/services/
El campo `content` incluye texto editorial para el portal ciudadano:
- `icon` — nombre del ícono Lucide (ej: `trash-2`, `leaf`)
- `summary` — descripción corta (máx 300 chars)
- `full_description` — descripción completa del servicio
- `frequency` — frecuencia del servicio
- `citizen_rights` — derechos del ciudadano según PPS 2024

### GET /api/v1/core/aspects/?service=\<slug\>
El campo `content` explica el aspecto al ciudadano:
- `icon` — nombre del ícono Lucide
- `what_is` — qué es este problema y cuándo ocurre
- `how_to_evidence` — cómo documentarlo con fotos
- `response_time` — tiempo de respuesta según contrato

> El campo `content` retorna `null` hasta que un líder de operaciones
> cargue el texto desde el admin de Django.

## Endpoints de auditoría SLA

### GET /api/v1/urbaser/alerts/
Alertas generadas automáticamente por el pipeline PostGIS al crear una denuncia.
- `violation` — `true` si hay incumplimiento SLA
- `distance_meters` — distancia en metros reales (EPSG:3116) entre denuncia y ruta
- `days_since_intervention` — solo zonas verdes: días desde el último corte
- `confidence` — `high` (GPS) / `medium` (manual) / `low` (centroide)
- `macroroute_code` — código oficial PPS (B211, 611, etc.)

### GET /api/v1/urbaser/metrics/
Caché estadístico por comuna y servicio. Alimenta el heatmap del dashboard.
- `violation_rate` — fracción 0.0–1.0 (violations / alerts del mes)
- `period` — primer día del mes calculado (ej: `2026-04-01`)
- Colores sugeridos: `> 0.70` rojo · `> 0.40` naranja · `≤ 0.40` verde
