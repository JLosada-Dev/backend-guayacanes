# Guayacanes

Backend del sistema de gestión de infraestructura y servicios públicos — Popayán.

Stack: Django 6 + GeoDjango · DRF · PostGIS · Redis · Python 3.13

---

## Requisitos del sistema

- **Docker + Docker Compose**
- **Python 3.13**
- **GDAL** (requerido por GeoDjango)

```bash
# Ubuntu / Debian
sudo apt install gdal-bin libgdal-dev

# macOS
brew install gdal
```

---

## Configuración inicial

### 1. Clonar el repositorio

```bash
git clone <url-del-repo>
cd guayacanes
```

### 2. Crear el archivo `.env`

```bash
cp .env.example .env
```

Editar `.env` con los valores correspondientes:

```env
SECRET_KEY=una-clave-secreta-segura
DB_NAME=guyacanes_dev
DB_USER=guyacanes
DB_PASSWORD=guyacanes
DB_HOST=localhost
DB_PORT=5432
```

### 3. Crear `config/settings/local.py`

Este archivo no está en el repositorio. Crearlo manualmente:

```python
from .base import *

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']
```

### 4. Levantar la base de datos

```bash
docker compose up -d
```

Esto levanta **PostgreSQL 16 con PostGIS** en el puerto `5432` y **Redis** en el `6379`.

---

## Instalación de dependencias

### Con pip (recomendado para el equipo)

```bash
# Crear y activar entorno virtual
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows

# Instalar dependencias
pip install -r requirements.txt        # producción
pip install -r requirements-dev.txt   # desarrollo (incluye pytest)
```

### Con uv

```bash
uv sync
```

---

## Correr el proyecto

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

---

## Tests

```bash
pytest
```

---

## Datos geográficos (shapefiles POT)

Los shapefiles del POT de Popayán **no están en este repositorio** por su tamaño.
Se gestionan en Google Drive. Solicitarlos al equipo si se necesitan para desarrollo.

---

## Variable de entorno `DJANGO_SETTINGS_MODULE`

Por defecto el proyecto usa `config.settings.local`. Para producción:

```bash
export DJANGO_SETTINGS_MODULE=config.settings.production
```
