# Entorno Python y GDAL — Auditoría y limpieza

Este documento explica por qué el sistema tiene varios Pythons instalados, por qué aparece Python 3.14, cómo encaja GDAL en el proyecto, y qué hacer al terminar el proyecto para limpiar el sistema.

---

## Por qué aparece Python 3.14

Al ejecutar `brew install gdal`, Homebrew instaló automáticamente `python@3.14` como **dependencia de GDAL**. No lo instalaste explícitamente — vino arrastrado.

```
brew install gdal
  └── instala python@3.14  (dependencia de gdal en brew)
  └── instala geos
  └── instala proj
  └── instala libspatialite
  └── instala libgdal.dylib  ← esto es lo que el proyecto realmente necesita
```

Como resultado, `python3` en el PATH apunta a `/opt/homebrew/bin/python3` que es Python 3.14.

---

## Mapa completo de Pythons en el sistema

| Ubicación | Versión | Origen | Tocar? |
|---|---|---|---|
| `/usr/bin/python3` | 3.9.6 | macOS (Apple) | Nunca |
| `/opt/homebrew/bin/python3` | 3.14.3 | `brew install gdal` (dependencia) | No (lo necesita GDAL) |
| `~/.local/share/uv/python/` | 3.12, 3.13 | uv (gestionado automáticamente) | No |
| `.venv/bin/python` | 3.13.12 | uv (proyecto) | Es el correcto |

**El proyecto usa correctamente Python 3.13.12** desde `.venv`, gestionado por uv. El 3.14 no interfiere.

---

## Para qué se usa GDAL en el proyecto

El proyecto usa GeoDjango (`django.contrib.gis`) para trabajar con datos geográficos. GeoDjango necesita dos librerías C del sistema:

- `libgdal.dylib` — para operaciones geoespaciales
- `libgeos_c.dylib` — para geometrías (puntos, polígonos, etc.)

Estas librerías las provee `brew install gdal` y están referenciadas en `config/settings/local.py`:

```python
GDAL_LIBRARY_PATH = '/opt/homebrew/opt/gdal/lib/libgdal.dylib'
GEOS_LIBRARY_PATH = '/opt/homebrew/opt/geos/lib/libgeos_c.dylib'
```

**No se usa el paquete Python de GDAL (`from osgeo import gdal`).** Solo se usa la librería C nativa que GeoDjango carga por su cuenta.

### Flujo real de uso geo en el proyecto

```
brew install gdal
  → libgdal.dylib + libgeos_c.dylib  (librerías C)
      → local.py apunta a esas rutas
          → GeoDjango las carga al arrancar Django
              → GEOSGeometry disponible en management commands
                  → load_communes.py y load_sweeping.py leen shapefiles con geopandas
                      → convierten geometrías con GEOSGeometry y guardan en PostGIS
```

---

## Estado del sistema al momento de la auditoría

### Saludable
- El `.venv` del proyecto está limpio y correctamente apuntado a Python 3.13.12
- `libgdal.dylib` y `libgeos_c.dylib` existen en los paths configurados
- `geopandas`, `djangorestframework-gis`, `shapely`, `pyproj` están correctamente en el venv

### Efecto secundario de brew install gdal
`pip3` (que pertenece al Python 3.14 de brew) tiene instalados:
- `GDAL 3.12.3`
- `numpy 2.4.4`

Estos fueron instalados globalmente como efecto secundario. No son necesarios — todo lo que el proyecto necesita está dentro del `.venv`.

---

## Limpieza al terminar el proyecto

### Paso 1 — Limpiar paquetes globales de pip (bajo riesgo)

```bash
pip3 uninstall gdal numpy -y
```

Esto elimina los paquetes Python instalados globalmente en el Python 3.14 de brew. No afecta el venv del proyecto ni las librerías C.

### Paso 2 — Desinstalar GDAL y dependencias geo de brew (si no los usas en otros proyectos)

```bash
brew uninstall gdal geos proj libspatialite
```

Esto elimina las librerías C geo. Solo hacer si ningún otro proyecto las necesita.

### Paso 3 — Desinstalar Python 3.14 de brew (opcional)

```bash
brew uninstall python@3.14
```

Brew puede negarse si otras fórmulas dependen de él. Si lo permite, `python3` en el PATH volverá al de macOS (3.9.6) — lo cual está bien para el uso general.

### Paso 4 — Limpiar Pythons de uv (opcional)

```bash
uv python uninstall 3.13
uv python uninstall 3.12
```

Solo si ya no vas a usar uv para ningún proyecto. Si sigues usando uv, déjalos — son ligeros y uv los gestiona solo.

### Paso 5 — Eliminar el venv del proyecto

```bash
rm -rf .venv
```

Simple. El `uv.lock` y `pyproject.toml` permiten recrearlo en cualquier momento con `uv sync`.

---

## Lo que NO tocar nunca

- `/usr/bin/python3` (3.9.6) — es de macOS, Apple lo gestiona, no se modifica
- Los Pythons de uv en `~/.local/share/uv/python/` — uv los gestiona automáticamente

---

## Resumen de comandos de limpieza

```bash
# 1. Paquetes globales (seguro, hacerlo ya si se quiere)
pip3 uninstall gdal numpy -y

# 2. Al terminar el proyecto — librerías geo
brew uninstall gdal geos proj libspatialite

# 3. Al terminar el proyecto — Python de brew (si no lo necesitas)
brew uninstall python@3.14

# 4. Opcional — limpiar Pythons de uv
uv python uninstall 3.13
uv python uninstall 3.12

# 5. Eliminar el venv del proyecto
rm -rf .venv
```

---

## Estado del sistema tras la limpieza

Después de ejecutar los pasos anteriores, el sistema queda así:

| Componente | Estado |
|---|---|
| `/usr/bin/python3` (3.9.6 macOS) | Permanece — es de Apple, no se toca |
| `python@3.14` de brew | Eliminado |
| `libgdal.dylib`, `libgeos_c.dylib` | Eliminados |
| Paquetes globales pip (GDAL, numpy) | Eliminados |
| uv y sus Pythons gestionados | Permanecen (ligeros, útiles para futuros proyectos) |

`python3` en el PATH vuelve a apuntar al de macOS (`/usr/bin/python3` 3.9.6), que no molesta y no se usa para desarrollo.

---

## Configuración de shell — no requiere cambios

El `zprofile` y `zshrc` ya están correctamente organizados y no necesitan modificarse:

- **`zprofile`** — gestiona brew, Java, Android, Flutter (fvm), Herd, y el PATH de uv (`$HOME/.local/bin`)
- **`zshrc`** — tiene el autocompletado de uv (`eval "$(uv generate-shell-completion zsh)"`)

No hay aliases ni entradas de PATH apuntando a versiones específicas de Python. uv está en `$HOME/.local/bin` que ya está en el PATH — funciona solo.

---

## Flujo de trabajo limpio con uv (para futuros proyectos)

Sin brew Python, sin pip global, sin activar venvs manualmente:

```bash
uv init mi-proyecto
cd mi-proyecto
uv python pin 3.13        # fija la versión de Python para el proyecto
uv add django             # instala dependencias (crea .venv automáticamente)
uv run python manage.py runserver
```

uv respeta el `.python-version` o `requires-python` de cada proyecto y descarga el Python necesario por su cuenta, sin tocar el sistema.
