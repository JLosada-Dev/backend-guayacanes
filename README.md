# Guyacanes

Sistema de supervisión y veeduría ciudadana para el servicio público
de aseo urbano — Alcaldía de Popayán, Cauca.

---

## ¿Qué es este sistema?

Cruza el "deber ser" (rutas contractuales del PPS 2024 de Urbaser) contra
la "realidad" (denuncias ciudadanas georeferenciadas) usando PostGIS para
detectar incumplimientos SLA automáticamente.

---

## Stack

- **Backend:** Django 6 + DRF + GeoDjango
- **Base de datos:** PostgreSQL 16 + PostGIS 3.4
- **Cache/Queue:** Redis 7
- **Python:** 3.13.12 (gestionado con uv)

---

## Arranque rápido

### Con uv (desarrollador principal)

```bash
git clone <url-del-repo>
cd guyacanes

# Levantar base de datos
docker compose up -d

# Instalar dependencias
uv sync

# Variables de entorno
cp .env.example .env
# Editar .env con las credenciales

# Migraciones y datos iniciales
uv run python manage.py migrate
uv run python manage.py loaddata fixtures/core_services.json
uv run python manage.py loaddata fixtures/core_aspects.json
uv run python manage.py load_communes
uv run python manage.py load_sweeping

# Servidor de desarrollo
uv run python manage.py runserver 0.0.0.0:8000
```

### Con pip (resto del equipo)

```bash
git clone <url-del-repo>
cd guyacanes

# Levantar base de datos
docker compose up -d

# Entorno virtual
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# Instalar dependencias
pip install -r requirements.txt

# Variables de entorno
cp .env.example .env
# Editar .env con las credenciales

# Migraciones y datos iniciales
python manage.py migrate
python manage.py loaddata fixtures/core_services.json
python manage.py loaddata fixtures/core_aspects.json
python manage.py load_communes
python manage.py load_sweeping

# Servidor de desarrollo
python manage.py runserver 0.0.0.0:8000
```

---

## Variables de entorno requeridas

Copiar `.env.example` a `.env` y completar:

| Variable | Requerida | Default |
|----------|-----------|---------|
| SECRET_KEY | Sí | — |
| DEBUG | No | False |
| ALLOWED_HOSTS | No | "" |
| DB_NAME | Sí | — |
| DB_USER | Sí | — |
| DB_PASSWORD | Sí | — |
| DB_HOST | No | localhost |
| DB_PORT | No | 5432 |
| CORS_ALLOWED_ORIGINS | No | "" |

---

## Requisitos del sistema

- Docker Desktop
- Python 3.13+
- GDAL 3.8+ (requerido por GeoDjango)
  - macOS: `brew install gdal`
  - Ubuntu: `sudo apt install gdal-bin libgdal-dev`

---

## Estructura del proyecto

```
guyacanes/
  apps/
    core/                                         # Catálogo transversal
    infra_servicios_publicos_urbaser/             # Servicio de aseo
    infra_servicios_publicos_urbaser_facturacion/ # Facturación (Fase 2)
  config/
    settings/
      base.py       # Settings comunes
      local.py      # Desarrollo
      production.py # Producción
  data/shapefiles/  # Geodatos POT Popayán
  docs/api/         # Colecciones Bruno y Postman
  fixtures/         # Datos iniciales del catálogo
  media_local/      # Archivos subidos en desarrollo
```

---

## API v1

Base URL: `http://localhost:8000/api/v1/`

### Core

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/core/services/` | Servicios activos |
| GET | `/core/aspects/?service=<slug>` | Aspectos por servicio |
| GET | `/core/communes/` | 9 comunas de Popayán |

### Veeduría

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/urbaser/complaints/` | Crear denuncia ciudadana |
| GET | `/urbaser/complaints/` | Listar denuncias |
| GET | `/urbaser/complaints/<id>/` | Detalle de denuncia |
| GET | `/urbaser/complaints/geojson/` | Denuncias como GeoJSON |
| POST | `/urbaser/evidence/` | Subir foto de evidencia |

### Auditoría

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/urbaser/alerts/` | Alertas SLA generadas |
| GET | `/urbaser/alerts/<id>/` | Detalle de alerta |
| GET | `/urbaser/metrics/` | Métricas heatmap por comuna |

Ver colecciones completas en `docs/api/`.

---

## Management commands

| Comando | Descripción |
|---------|-------------|
| `load_communes` | Carga 9 comunas desde U2_COMUNAS.shp |
| `load_sweeping` | Carga rutas de barrido desde U18_VIAL.shp |

---

## Agregar una dependencia

```bash
# Con uv (desarrollador principal)
uv add nombre-paquete

# Regenerar requirements.txt para el equipo
uv export --format requirements-txt --no-hashes -o requirements.txt
uv export --format requirements-txt --no-hashes --dev -o requirements-dev.txt

# Commitear los tres archivos
git add pyproject.toml uv.lock requirements.txt requirements-dev.txt
```

---

## Admin

Disponible en `http://localhost:8000/admin`
Crear superusuario: `python manage.py createsuperuser`
