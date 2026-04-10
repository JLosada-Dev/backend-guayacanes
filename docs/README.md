# Guyacanes — Documentación del equipo

Sistema de supervisión de servicios públicos de aseo urbano — Alcaldía de Popayán / Urbaser.

---

## Índice

| Documento | Qué contiene |
|-----------|-------------|
| [CONTEXT_GUYACANES.md](CONTEXT_GUYACANES.md) | Arquitectura completa: modelos, signals, flujos, estado actual |
| [guia-dependencias.md](guia-dependencias.md) | Setup local paso a paso (uv, GDAL, Docker, local.py) |
| [geodatos.md](geodatos.md) | Inventario de shapefiles POT — cuáles están cargados, cuáles pendientes y cómo cargarlos |
| [rutas-y-servicios.md](rutas-y-servicios.md) | Contexto de negocio: 8 macrorutas de barrido, 35 de recolección, 290 zonas verdes, SLA |
| [api/README.md](api/README.md) | Endpoints v1 + cómo importar colecciones Bruno / Postman |

---

## Setup en 5 minutos

```bash
# 1. Dependencias Python
uv sync

# 2. Base de datos
docker compose up -d

# 3. Settings locales (copiar y editar rutas GDAL)
cp config/settings/local.py.example config/settings/local.py   # si existe
# o crear manualmente — ver guia-dependencias.md

# 4. Migraciones + fixtures de catálogo
uv run python manage.py migrate
uv run python manage.py loaddata fixtures/core_services.json
uv run python manage.py loaddata fixtures/core_aspects.json

# 5. Cargar comunas desde shapefile
uv run python manage.py load_communes

# 6. Superusuario
uv run python manage.py createsuperuser

# 7. Servidor
uv run python manage.py runserver 0.0.0.0:8000
```

Admin: http://localhost:8000/admin
API: http://localhost:8000/api/v1/

---

## Estado del proyecto

| Módulo | Estado | Notas |
|--------|--------|-------|
| `core` — Catálogo | ✓ Completo | 5 servicios, 11 aspectos, 9 comunas cargadas |
| `infra_servicios_publicos_urbaser` — Veeduría | ✓ Completo | Complaint + Evidence, API v1 activa |
| `infra_servicios_publicos_urbaser` — Operaciones | Pendiente | SweepingMacroRoute, GreenZone — ver CONTEXT |
| `infra_servicios_publicos_urbaser` — Auditoría | Pendiente | SLAAlert, CommuneMetric — ver CONTEXT |
| Frontend React + Vite | Pendiente | Esperando template |

---

## Geodatos disponibles

Los shapefiles del POT viven en `guayacanes_docs/SHAPESPOT/SHAPES POT/`.
Ver [geodatos.md](geodatos.md) para el inventario completo y comandos de carga.

Los datos contractuales (rutas, cronogramas) viven en `guayacanes_docs/urbaser-servicios-pdf/`.
Ver [rutas-y-servicios.md](rutas-y-servicios.md) para el resumen de negocio.
