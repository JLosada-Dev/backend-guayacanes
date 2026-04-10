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

Este archivo **no está en el repositorio** (está en `.gitignore`) porque cada desarrollador puede tener configuración distinta en local. Hay que crearlo manualmente.

Crear el archivo en la ruta `config/settings/local.py`. A continuación un ejemplo de referencia completo que puedes copiar y ajustar:

```python
from .base import *
from decouple import config, Csv

DEBUG = True

# GDAL / GEOS — GeoDjango necesita saber dónde están las librerías del sistema.
# brew install gdal instala en /opt/homebrew/opt/gdal/lib/ (macOS Apple Silicon).
# Si tu ruta es distinta, ajusta aquí o define la variable en .env.
GDAL_LIBRARY_PATH = config(
    'GDAL_LIBRARY_PATH',
    default='/opt/homebrew/opt/gdal/lib/libgdal.dylib',
)
GEOS_LIBRARY_PATH = config(
    'GEOS_LIBRARY_PATH',
    default='/opt/homebrew/opt/geos/lib/libgeos_c.dylib',
)

# En desarrollo puede dejarse este default. NUNCA usar en producción.
SECRET_KEY = config('SECRET_KEY', default='django-insecure-local-dev-key-change-in-production')

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': config('DB_NAME', default='guyacanes_dev'),
        'USER': config('DB_USER', default='guyacanes'),
        'PASSWORD': config('DB_PASSWORD', default='guyacanes'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

CORS_ALLOW_ALL_ORIGINS = True

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

> **Notas:**
> - **GDAL_LIBRARY_PATH / GEOS_LIBRARY_PATH:** GeoDjango necesita estas librerías del sistema. En macOS con Apple Silicon, brew las instala en `/opt/homebrew/opt/gdal/lib/` y `/opt/homebrew/opt/geos/lib/`. Si usas Intel Mac la ruta será `/usr/local/opt/...`. En Linux normalmente no hace falta configurarlas porque Django las encuentra automáticamente. Si tu ruta es diferente, puedes sobreescribirla en `.env` (ej: `GDAL_LIBRARY_PATH=/otra/ruta/libgdal.dylib`).
> - Los valores de BD deben coincidir con los del `.env` o, si usas Docker, con los definidos en `docker-compose.yml`.
> - `EMAIL_BACKEND` apunta a la consola en local — los emails se imprimen en la terminal en lugar de enviarse.
> - Si necesitas sobreescribir cualquier otra cosa para tu entorno (caché, storage, etc.) hazlo aquí, nunca en `base.py`.
>
> **¿Por qué existe este archivo?**
> El proyecto tiene tres settings: `base.py` (configuración común), `local.py` (desarrollo local, no versionado) y `production.py` (producción). Django carga `local.py` por defecto al correr `runserver`. Si no existe, el servidor no arranca.

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

Django necesita saber qué archivo de settings usar. El proyecto tiene tres:

| Archivo | Cuándo se usa |
|---|---|
| `config/settings/base.py` | Nunca directamente — es la base común |
| `config/settings/local.py` | Desarrollo local (cada dev lo crea en su máquina) |
| `config/settings/production.py` | Servidor de producción |

Por defecto `manage.py` apunta a `config.settings.local`, así que en desarrollo no hay que hacer nada extra.

Si en algún momento Django lanza un error como `ModuleNotFoundError: No module named 'config.settings.local'`, es porque la variable no está configurada o el archivo `local.py` no existe. Verificar que el paso 3 de la configuración inicial se haya completado.

Para cambiar de settings sin modificar código, exportar la variable antes de correr cualquier comando:

```bash
# Usar settings de producción
export DJANGO_SETTINGS_MODULE=config.settings.production
python manage.py runserver

# Volver a local (valor por defecto)
export DJANGO_SETTINGS_MODULE=config.settings.local
```

En servidores (Railway, VPS, Docker, etc.) configurar esta variable de entorno directamente en la plataforma.
