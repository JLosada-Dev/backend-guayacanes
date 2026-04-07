# Guia de manejo de dependencias

Este proyecto soporta dos formas de instalar dependencias: **uv** (recomendado) y **pip** (alternativa).

---

## Requisito previo: GDAL

GeoDjango requiere la libreria GDAL instalada en el sistema.

```bash
# macOS
brew install gdal

# Ubuntu / Debian
sudo apt install gdal-bin libgdal-dev
```

---

## Opcion A: uv (recomendado)

[uv](https://docs.astral.sh/uv/) es un gestor de paquetes y entornos virtuales rapido para Python. Es la forma preferida de trabajar en este proyecto.

### Instalar uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Instalar Python 3.13

uv gestiona versiones de Python sin necesidad de instalarlas globalmente:

```bash
uv python install 3.13
```

### Instalar dependencias

```bash
# Instala todas las dependencias (produccion + desarrollo)
uv sync

# Solo dependencias de produccion (sin pytest, etc.)
uv sync --no-dev
```

`uv sync` lee `pyproject.toml` y `uv.lock`, crea el entorno virtual automaticamente en `.venv/` e instala todo.

### Ejecutar comandos

Con uv no necesitas activar el entorno virtual manualmente. Usa `uv run` para ejecutar cualquier comando dentro del entorno:

```bash
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver
uv run pytest
```

### Agregar una dependencia nueva

```bash
# Dependencia de produccion
uv add nombre-del-paquete

# Dependencia de desarrollo (solo para tests, linters, etc.)
uv add --group dev nombre-del-paquete
```

Esto actualiza `pyproject.toml` y `uv.lock` automaticamente.

### Eliminar una dependencia

```bash
uv remove nombre-del-paquete
```

### Actualizar dependencias

```bash
# Actualizar todas
uv lock --upgrade
uv sync

# Actualizar una sola
uv lock --upgrade-package nombre-del-paquete
uv sync
```

### Regenerar requirements.txt (para quienes usen pip)

Si se modifican dependencias con uv, regenerar los archivos de requirements para mantener compatibilidad:

```bash
uv export --no-hashes -o requirements.txt
uv export --no-hashes --group dev -o requirements-dev.txt
```

---

## Opcion B: pip

Para quienes prefieran el flujo tradicional con pip.

### Crear y activar entorno virtual

```bash
python3.13 -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows
```

### Instalar dependencias

```bash
# Produccion
pip install -r requirements.txt

# Desarrollo (incluye pytest)
pip install -r requirements-dev.txt
```

### Ejecutar comandos

Con el entorno virtual activado:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
pytest
```

### Agregar una dependencia nueva (con pip)

Si agregas dependencias manualmente con pip, asegurate de tambien agregarla en `pyproject.toml` para que quede registrada como fuente de verdad del proyecto. Luego regenerar los archivos lock:

```bash
pip install nombre-del-paquete
# Editar pyproject.toml manualmente y agregar el paquete en [project.dependencies]
```

---

## Estructura de archivos de dependencias

| Archivo              | Proposito                                                  |
|----------------------|------------------------------------------------------------|
| `pyproject.toml`     | Fuente de verdad. Define el proyecto y sus dependencias    |
| `uv.lock`            | Lock file de uv. Versiones exactas resueltas               |
| `requirements.txt`   | Generado desde uv. Para compatibilidad con pip             |
| `requirements-dev.txt` | Generado desde uv. Incluye dependencias de desarrollo    |

> **Importante:** `pyproject.toml` es la fuente de verdad. Los archivos `requirements*.txt` se generan a partir de el. Si modificas dependencias, hazlo en `pyproject.toml` (o con `uv add`) y luego exporta.

---

## Solucionar errores de imports en VS Code (Pyright/Pylance)

Despues de ejecutar `uv sync`, es posible que VS Code muestre errores como:

```
Cannot find module `django.db`
Site package path queried from interpreter: [.../cpython-3.12.../site-packages]
```

Esto ocurre porque Pyright (el analizador de tipos de VS Code) esta usando el Python global del sistema en lugar del `.venv` del proyecto donde uv instalo las dependencias.

### Solucion 1: Seleccionar el interprete correcto en VS Code

1. Abrir la paleta de comandos: `Cmd+Shift+P` (macOS) o `Ctrl+Shift+P` (Linux/Windows)
2. Buscar **"Python: Select Interpreter"**
3. Seleccionar `./.venv/bin/python` (el entorno virtual del proyecto)

### Solucion 2: Configuracion en pyproject.toml (ya incluida)

El proyecto ya tiene esta configuracion en `pyproject.toml` para que Pyright detecte el `.venv` automaticamente:

```toml
[tool.pyright]
venvPath = "."
venv = ".venv"
```

Si aun asi persiste el error, recargar VS Code: `Cmd+Shift+P` → **"Developer: Reload Window"**.
