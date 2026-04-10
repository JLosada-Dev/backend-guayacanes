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
