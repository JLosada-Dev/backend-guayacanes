# Estado Actual del Proyecto

**Fecha:** 14 abril 2026
**Propósito:** fuente única de verdad del progreso. Consolida `plan-accion-fase1.md`, `plan-demo-completo.md`, `changelog-fase-a.md` y `frontend-changelog.md`.

---

## 1. Resumen ejecutivo

| Área | Completado | Pendiente |
|------|-----------|-----------|
| Backend — modelos y API | 100% | — |
| Backend — pipeline SLA | 100% | — |
| Backend — datos cargados | 95% | Barrios (sin shapefile) |
| Backend — documentación | 100% | — |
| Frontend — portal ciudadano | 95% | Validación en navegador post-cambios |
| Frontend — dashboard | 75% | Mapa real + GeoJSON overlay |
| Integración backend ↔ frontend | 90% | Mapa real (#6, #7) |
| Autenticación | 0% | JWT post-demo |

**Estado demo:** lista para presentar. Falta solo pulimiento visual (mapa real del dashboard).

---

## 2. Backend — completado

### 2.1 Modelos y migraciones

- 14 modelos registrados (6 core + 8 urbaser)
- 7 migraciones aplicadas
- Índices GiST en campos geométricos
- Soft FKs con snapshot de texto entre apps

### 2.2 API REST v1 — 12 endpoints funcionando

```
GET  /api/v1/core/services/              + content populado
GET  /api/v1/core/aspects/?service=slug  + content populado
GET  /api/v1/core/communes/
POST /api/v1/urbaser/complaints/
GET  /api/v1/urbaser/complaints/
GET  /api/v1/urbaser/complaints/{id}/
GET  /api/v1/urbaser/complaints/geojson/
POST /api/v1/urbaser/evidence/           (bug fix aplicado: campo complaint agregado al serializer)
GET  /api/v1/urbaser/alerts/
GET  /api/v1/urbaser/alerts/{id}/
GET  /api/v1/urbaser/metrics/
GET  /api/v1/urbaser/metrics/{id}/
```

### 2.3 Swagger / OpenAPI — 3 URLs

```
GET /api/schema/    OpenAPI 3.0 YAML
GET /api/docs/      Swagger UI interactivo
GET /api/redoc/     ReDoc navegable
```

### 2.4 Management commands — 5 implementados

| Comando | Fuente | Registros |
|---------|--------|-----------|
| `load_communes` | `U2_COMUNAS.shp` | 9 comunas |
| `load_sweeping` | `U18_VIAL.shp` + MACROROUTES_DEF | 8 macrorutas + 1,731 microrutas |
| `load_green_zones` | 5 shapefiles combinados | 313 zonas verdes |
| `load_cutting_schedule` | `cronograma-de-cesped-febrero-2026.pdf` | 31 schedules |
| `seed_complaints` | datos sintéticos | 14 denuncias de prueba |

### 2.5 Fixtures

```
core_services.json            5 servicios
core_aspects.json             11 aspectos
core_service_content.json     2 contenidos editoriales (sweeping + green-zones)
core_aspect_content.json      11 contenidos por aspecto con response_time
```

### 2.6 Pipeline SLA — validado end-to-end

Con el seed de 14 denuncias:
- 27 alertas SLA generadas automáticamente
- **24 violations** detectadas (post-fix de `end_time` en macrorutas)
- 5 métricas de comuna calculadas
- Ventana que cruza medianoche (ruta 631B 19:00-03:00) manejada correctamente

### 2.7 Admin Django — 15 modelos registrados

- `GISModelAdmin` con mapa Leaflet para modelos con geometría
- Inlines: `EvidenceInline`, `SweepingMicroRouteInline`, `CuttingScheduleInline`, `InterventionInline`
- Read-only: `SLAAlertAdmin` y `CommuneMetricAdmin`
- Fieldsets organizados: Qué / Dónde / Contexto en `ComplaintAdmin`

### 2.8 Colección Bruno — 13 requests

Covering all 12 endpoints de negocio + POST evidence con multipart.

### 2.9 Infrastructure

- `docker-compose.yml` con PostgreSQL 16 + PostGIS 3.4 + Redis 7
- `uv` para Python 3.13 + dependencias (incluye `pdfplumber`, `drf-spectacular`)
- `requirements.txt` y `requirements-dev.txt` sincronizados
- CORS `ALLOW_ALL_ORIGINS=True` en local (backend acepta Vite :5173)
- `Makefile` con targets: `dev`, `reset`, `data`, `seed`, `demo`, `shell`, `logs`

### 2.10 Documentación — 9 archivos técnicos

```
README.md                    setup + API summary + índice docs
docs/CONTEXT_GUYACANES.md    arquitectura, modelos, estado, tech stack
docs/api/README.md           referencia completa API + Swagger
docs/admin-guide.md          guía del panel admin
docs/demo-guide.md           recorrido paso a paso para demo
docs/geodatos.md             inventario shapefiles + CRS + commands
docs/guia-dependencias.md    setup uv + GDAL + VS Code
docs/rutas-y-servicios.md    contexto de negocio PPS 2024
docs/barrios-opciones.md     opciones para cargar barrios
docs/plan-accion-fase1.md    gaps, pendientes, info faltante
docs/plan-demo-completo.md   integración backend + frontend
docs/changelog-fase-a.md     changelog backend Fase A
docs/frontend-changelog.md   changelog frontend granular
docs/estado-actual.md        este archivo
```

---

## 3. Frontend — completado

### 3.1 Stack

React 19 + Vite 8 + TypeScript 6 + Tailwind 4 + Zustand 5 + Axios + Leaflet.

### 3.2 Portal Ciudadano (/)

**Wizard de 4 pasos funcional:**

| Paso | Componente | Consume | Cambios Fase A |
|------|-----------|---------|---------------|
| 1 | `Step1Service` | GET `/core/services/` | ➕ Badge de frequency · ➕ Botón "Ver más" |
| 2 | `Step2Aspect` | GET `/core/aspects/?service=` | Ya mostraba content + response_time |
| 3 | `Step3Location` | GET `/core/communes/` | Sin cambios |
| 4 | `Step4Confirm` | POST `/complaints/` + POST `/evidence/` | ➕ Subida de evidencias con preview |

**Nuevos componentes:**
- `ServiceInfoModal` — muestra `full_description` y `citizen_rights` con base legal
- `EvidenceUploader` — grid 4x con preview, validación cliente, upload secuencial

### 3.3 Dashboard Supervisor (/dashboard)

- Toggle servicio sweeping/green-zones
- Summary cards: complaints, alerts, violations, compliance
- Heatmap por comuna (botones con colores)
- Tabla de alertas SLA con filtros

### 3.4 Config

- `.env.example` creado — documenta `VITE_API_URL` y `VITE_API_TIMEOUT`
- Cliente axios compartido en `src/api/client.ts` (elimina duplicación)
- Proxy Vite `/api → localhost:8000` preservado para dev

### 3.5 Mejoras de código

- Refactor `<button>` anidado a `<div role="button">` en Step1Service (HTML válido + accesibilidad)
- `URL.createObjectURL` con cleanup en unmount del EvidenceUploader
- Manejo de errores parciales en upload (algunas fotos fallan sin perder la denuncia)

---

## 4. Pendientes

### 4.1 🔴 Granular #6 — Mapa real con polígonos de comunas

**Efecto:** el dashboard deja de ser un grid de botones y se convierte en un mapa geográfico real.

**Tareas:**
1. **Backend:** revisar `CommuneSerializer` — actualmente no retorna el campo `geom` (validar con `curl /api/v1/core/communes/`). Opción A: incluir `geom` en fields. Opción B: crear endpoint separado `/core/communes/geojson/` usando `GeoFeatureModelSerializer` (similar a `ComplaintGeoSerializer`)
2. **Frontend:** reemplazar `CommuneHeatmap` (botones) por `<MapContainer>` de react-leaflet con `<GeoJSON>` layer
3. **Frontend:** color de cada polígono según `violation_rate` (reusar la lógica de colores actual)
4. **Frontend:** click en polígono dispara `setSelectedCommune` en el store

**Esfuerzo:** 3-4 horas

**Bloqueante para:** #7

---

### 4.2 🔴 Granular #7 — Capa GeoJSON de denuncias en el mapa

**Efecto:** cada denuncia aparece como marcador en el mapa. Click abre popup con aspect + status.

**Tareas:**
1. **Frontend:** consumir `getComplaintsGeoJSON()` al cargar el dashboard
2. **Frontend:** agregar `<GeoJSON>` layer con `pointToLayer` personalizado (marker con color según servicio)
3. **Frontend:** popup al hacer click en un marker

**Esfuerzo:** 1 hora (depende del #6)

---

### 4.3 ⚠️ Validación manual end-to-end en navegador

**Los cambios #1-#5 compilan con TypeScript sin errores, pero falta:**
- Probar el wizard completo de denuncia con evidencias desde el navegador
- Probar el botón "Ver más" del servicio
- Probar que el `frequency` se ve bien en mobile (line-clamp)
- Probar upload con 4 fotos a 8MB cada una

**Esfuerzo:** 30 min — solo correr ambos servidores y navegar.

---

### 4.4 ⚠️ Información externa pendiente

Lo que sigue dependiendo de terceros:

| Item | Fuente | Impacto |
|------|--------|---------|
| Shapefile oficial de barrios | Alcaldía o DANE MGN | Medio — el sistema funciona sin esto (fallback a centroide de comuna) |
| Registro histórico de intervenciones | Urbaser/Alcaldía | Medio — sin esto no hay `days_since_intervention` real |
| Horarios de barrido validados | Urbaser | Bajo — usamos horarios inferidos del MD, razonables |
| Cronogramas marzo-diciembre 2026 | Urbaser | Bajo — febrero basta para el demo |

### 4.5 ⚪ Post-demo (Fase B)

- **Autenticación JWT** (`djangorestframework-simplejwt`)
  - Login screen en frontend
  - Permisos: ciudadano solo POST /complaints/, supervisor puede leer alerts/metrics, admin full
- **Tests**
  - Backend: pytest + pytest-django (ya instalado)
  - Frontend: Vitest + React Testing Library
  - E2E: Playwright sobre el flow completo
- **Deployment**
  - Settings de producción en el backend
  - Build del frontend + nginx o Vercel
  - Variables `.env.production`
- **Fase 2 de negocio**
  - Recolección de basura (35 rutas documentadas)
  - Inventario arbóreo (18,123 árboles)
  - Facturación (Celery + Redis)

---

## 5. Checklist para arrancar la demo hoy

### Setup (una vez por máquina)

```bash
# Backend
cd backend-guayacanes
docker compose up -d
uv sync
cp .env.example .env
make demo        # migrate + data + seed
uv run python manage.py createsuperuser

# Frontend
cd ../frontend-guayacanes
cp .env.example .env
npm install      # o pnpm install
```

### Correr la demo

```bash
# Terminal 1: backend
cd backend-guayacanes && make dev

# Terminal 2: frontend
cd frontend-guayacanes && npm run dev
```

### URLs

| Rol | URL |
|-----|-----|
| Portal ciudadano | http://localhost:5173/ |
| Dashboard supervisor | http://localhost:5173/dashboard |
| Admin Django | http://localhost:8000/admin/ |
| Swagger UI | http://localhost:8000/api/docs/ |
| ReDoc | http://localhost:8000/api/redoc/ |
| OpenAPI schema | http://localhost:8000/api/schema/ |

---

## 6. Métricas de lo logrado

| Métrica | Valor |
|---------|-------|
| Endpoints REST funcionando | 12 + 3 docs = **15** |
| Modelos Django | **14** |
| Fixtures JSON | **4** (5 servicios, 11 aspectos, 2 service content, 11 aspect content) |
| Zonas verdes cargadas | **313** |
| Microrutas de barrido | **1,731** |
| Cutting schedules | **31** |
| Denuncias de prueba | **14** |
| Alertas SLA auto-generadas | **27** |
| Violations detectadas | **24** |
| Componentes React | **13** |
| Requests Bruno | **13** |
| Archivos de documentación | **14** |
| Management commands | **5** |
| Frontend granulares completados | **5/7** |
| Bugs de backend descubiertos y resueltos | **2** (end_time null + EvidenceSerializer sin `complaint`) |

---

## 7. Decisiones pendientes de producto

Cosas que no son técnicas pero que afectan el scope:

- ¿Se hace la demo con los 2 servicios de Fase 1, o se activa algún servicio de Fase 2?
- ¿La demo es interna a la Alcaldía o incluye a Urbaser?
- ¿Requiere presencial o es vía video?
- ¿Hay tiempo para conseguir el shapefile de barrios antes de la demo?
- ¿Quién redacta el copy definitivo del portal (vs. el texto actual que es técnico)?
