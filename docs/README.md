# Guyacanes — Documentación del equipo

Sistema de supervisión y veeduría ciudadana de servicios públicos — Alcaldía de Popayán / Urbaser.

---

## Índice

### Estado y contexto

| Documento | Qué contiene |
|-----------|-------------|
| [estado-actual.md](estado-actual.md) | **Fuente única de verdad del progreso** — completado vs pendiente |
| [CONTEXT_GUYACANES.md](CONTEXT_GUYACANES.md) | Contexto completo de Fase A: modelos, signals, flujos (ver nota V2 al inicio) |
| [rutas-y-servicios.md](rutas-y-servicios.md) | Contexto de negocio: contrato PPS 2024, macrorutas, zonas verdes, SLA |

### Arquitectura V2 (`refactor/`)

| Documento | Qué contiene |
|-----------|-------------|
| [refactor/ARQUITECTURA-V2.md](refactor/ARQUITECTURA-V2.md) | Diseño multiapp: core, geodata, veeduria, urbaser |
| [refactor/SECTION-REGISTRY.md](refactor/SECTION-REGISTRY.md) | Section en core + ownership de Service/Aspect por app |
| [refactor/REGISTRY-PATTERN.md](refactor/REGISTRY-PATTERN.md) | Patrón de handlers SLA vía signal `complaint_created` |
| [refactor/EVENTS.md](refactor/EVENTS.md) | Contrato del evento serializable (futuro Kafka) |
| [refactor/MAPA-MODELOS.md](refactor/MAPA-MODELOS.md) | Mapa de migración de modelos V1 → V2 |

### Operación y setup

| Documento | Qué contiene |
|-----------|-------------|
| [guia-dependencias.md](guia-dependencias.md) | Setup local paso a paso (uv, GDAL, Docker, VS Code) |
| [entorno-python-gdal.md](entorno-python-gdal.md) | Por qué hay varios Pythons en el sistema y cómo limpiar |
| [demo-guide.md](demo-guide.md) | Recorrido paso a paso para correr la demo |
| [admin-guide.md](admin-guide.md) | Guía del panel admin: inlines, fieldsets, flujo operacional |
| [api/README.md](api/README.md) | Referencia de endpoints v1 + colección Bruno |

### Datos

| Documento | Qué contiene |
|-----------|-------------|
| [geodatos.md](geodatos.md) | Inventario de shapefiles POT, CRS y comandos de carga |
| [barrios-opciones.md](barrios-opciones.md) | Opciones evaluadas para cargar geometrías de barrios |
| Comunas-Popayán.pdf | Documento fuente de las comunas de Popayán |

### Meta

| Documento | Qué contiene |
|-----------|-------------|
| [estrategia-documentacion.md](estrategia-documentacion.md) | Cómo se reparte la documentación entre los dos repos |
| [frontend-changelog.md](frontend-changelog.md) | Changelog del frontend (copia de `frontend-guayacanes/CHANGELOG.md`) |

---

## Setup en 5 minutos

```bash
# 1. Dependencias Python
uv sync

# 2. Base de datos + servidor (espera a PostgreSQL)
make dev

# En otra terminal:

# 3. Migraciones + fixtures + geodatos
make reset

# 4. Datos de demo (denuncias seed → alertas → métricas)
make demo

# 5. Superusuario
uv run python manage.py createsuperuser
```

Admin: http://localhost:8000/admin
API: http://localhost:8000/api/v1/
Swagger: http://localhost:8000/api/docs/

Detalle de GDAL y `local.py` en [guia-dependencias.md](guia-dependencias.md).

---

## Estado del proyecto

Ver [estado-actual.md](estado-actual.md) — fuente única de verdad. Resumen:

| Módulo | Estado |
|--------|--------|
| `core` — Section, geografía | ✓ Completo |
| `geodata` — espacios públicos POT | ✓ Completo |
| `veeduria` — denuncias, alertas SLA, métricas | ✓ Completo |
| `infra_servicios_publicos_urbaser` — catálogo y operaciones | ✓ Completo |
| Frontend React + Vite | ✓ Portal ciudadano + dashboard supervisor |
| Barrios (geometrías) | Pendiente — sin shapefile, ver [barrios-opciones.md](barrios-opciones.md) |

---

## Geodatos disponibles

Los shapefiles del POT viven en `guayacanes_docs/SHAPESPOT/SHAPES POT/`.
Ver [geodatos.md](geodatos.md) para el inventario completo y comandos de carga.

Los datos contractuales (rutas, cronogramas) viven en `guayacanes_docs/urbaser-servicios-pdf/`.
Ver [rutas-y-servicios.md](rutas-y-servicios.md) para el resumen de negocio.
