# Plan de Acción — Demo Completo (Backend + Frontend)

Estado al **14 abril 2026**. Para una demo end-to-end con portal ciudadano + dashboard supervisor operativos.

---

## 1. Estado actual

### Backend — 95% listo

✅ Completado:
- 12 endpoints v1 + 3 de Swagger/OpenAPI
- Pipeline SLA funcionando (24 violations en seed de 14 denuncias)
- 313 zonas verdes + 31 cutting schedules cargados
- Contenido editorial de 2 servicios + 11 aspectos
- CORS configurado para dev (ALLOW_ALL_ORIGINS)
- Swagger UI en `/api/docs/`

🟡 Pendiente (no bloquea demo):
- JWT auth
- `load_neighborhoods` (sin shapefile DANE)
- Historial real de Intervenciones

### Frontend — 85% listo

✅ Completado:
- React 19 + Vite 8 + TypeScript 6 + Tailwind 4
- Portal ciudadano: wizard de 4 pasos funcional
- Dashboard supervisor: summary + tabla alertas + heatmap (botones)
- Axios + Zustand + Leaflet configurados
- 8 de los 12 endpoints v1 consumidos

🟡 Pendiente (ver sección 2):
- Subida de evidencias (endpoint sin usar)
- Mapa real del dashboard con polígonos de comunas
- Display completo de ServiceContent (citizen_rights, frequency, full_description)
- Variables `.env` (VITE_API_URL)

---

## 2. Gaps de integración Backend ↔ Frontend

### 2.1 🔴 Endpoint de evidencias sin integrar

**Backend:** `POST /api/v1/urbaser/evidence/` con multipart/form-data — funcional y testeado en Bruno.

**Frontend:** el Step 4 de `CitizenPortal` crea la denuncia pero no permite adjuntar fotos. El modal de aspect ya muestra `how_to_evidence` con instrucciones para documentar — el ciudadano lee cómo tomar la foto pero no puede subirla.

**Fix:** agregar un input `<input type="file" accept="image/*" multiple>` en Step4 o Step3 del portal, y tras recibir el `complaint.id` en la respuesta, hacer POST a `/evidence/` con cada foto.

**Esfuerzo:** 1-2 horas. Requiere:
- Nuevo método `uploadEvidence(complaintId, file)` en `urbaser.ts`
- Componente de previsualizacion de imagenes
- Logica de upload secuencial post-creacion de denuncia

---

### 2.2 ⚠️ Dashboard "mapa" no es un mapa real

**Actual:** la sección "Heatmap comunas" son botones en grid con fondo de color.

**Ideal:** renderizar un `MapContainer` de react-leaflet con los 9 polígonos de comunas (el endpoint `/core/communes/` ya retorna la geometría) y colorearlos según `violation_rate` de la métrica activa. Click en una comuna filtra la tabla.

**Consideración importante:** `/core/communes/` actualmente **no retorna el campo `geom`** en el serializer. Hay que verificar o modificar el `CommuneSerializer`.

**Esfuerzo:** 3-4 horas. Requiere:
- Revisar/ajustar CommuneSerializer para incluir geom (o crear endpoint GeoJSON específico)
- Componente `CommuneMapLayer` con react-leaflet
- Sincronizar el click del polígono con `selectedCommune` del store

---

### 2.3 ⚠️ GeoJSON de denuncias sin consumir

**Backend:** `GET /api/v1/urbaser/complaints/geojson/` retorna las 14 denuncias del seed como FeatureCollection.

**Frontend:** `getComplaintsGeoJSON()` existe en `urbaser.ts` pero ningún componente lo usa.

**Fix:** añadir capa de puntos (clusters o markers individuales) en el mapa del dashboard. Cada punto muestra el aspect_description + status en popup.

**Esfuerzo:** 2 horas (después de 2.2)

---

### 2.4 ⚠️ ServiceContent no se muestra completo

**Actual:** el portal muestra solo `icon` + `summary` en las cards de servicio.

**Tenemos pero no se usa:**
- `full_description` — texto largo del servicio
- `frequency` — "Residencial 2x/semana..."
- `citizen_rights` — derechos con base legal

**Fix propuesto:** agregar un botón "Más información" en la card del servicio que abra un modal similar al de aspecto, mostrando los 3 campos.

**Esfuerzo:** 1 hora

---

### 2.5 ⚠️ Sin `.env` en frontend

**Actual:** `vite.config.ts` tiene proxy hardcoded a `http://localhost:8000`. Esto funciona en dev pero no es configurable para staging/production.

**Fix:**
```
# frontend-guayacanes/.env.example
VITE_API_URL=/api/v1
VITE_BACKEND_URL=http://localhost:8000
```

Luego en `src/api/*.ts`:
```typescript
const client = axios.create({ baseURL: import.meta.env.VITE_API_URL })
```

**Esfuerzo:** 30 min

---

## 3. Plan priorizado para demo completo

### Demo mínima viable (1-2 horas)

**Suficiente para mostrar el flujo end-to-end completo:**

1. ✅ Ya listo: Wizard de 4 pasos → POST denuncia → SLA pipeline → visible en dashboard
2. 🔴 **Implementar subida de evidencias** (Gap 2.1) — 1-2h

**Criterio de éxito:** el ciudadano puede submitir una denuncia con foto, y el supervisor la ve en el dashboard con la foto accesible (vía admin o URL directa).

---

### Demo pulida (medio día adicional, 4-5h)

4. Modal "Más información" del servicio (Gap 2.4) — 1h
5. Variables `.env` del frontend (Gap 2.5) — 30 min
6. Dashboard con mapa real + polígonos de comunas (Gap 2.2) — 3-4h
7. Capa de denuncias GeoJSON en el mapa (Gap 2.3) — 1h (depende del 6)

**Criterio de éxito:** la demo se ve profesional con un mapa real y la información completa del servicio.

---

### Post-demo (Fase B)

- JWT auth + login para el dashboard
- Historial real de Intervenciones (requiere data de Urbaser)
- Carga de shapefile de barrios (requiere Alcaldía)
- Tests E2E con Playwright

---

## 4. Runbook para correr la demo

### Terminal 1 — Backend

```bash
cd backend-guayacanes
docker rm guyacanes_db guyacanes_redis 2>/dev/null || true
make dev         # levanta Docker + Django en :8000
```

En otra terminal (una vez):
```bash
cd backend-guayacanes
make demo        # migrate + data + seed
uv run python manage.py createsuperuser
```

### Terminal 2 — Frontend

```bash
cd frontend-guayacanes
npm install      # primera vez
npm run dev      # Vite en :5173
```

### URLs de la demo

| URL | Rol |
|-----|-----|
| `http://localhost:5173/` | Portal ciudadano (front) |
| `http://localhost:5173/dashboard` | Dashboard supervisor (front) |
| `http://localhost:8000/admin/` | Panel admin Django |
| `http://localhost:8000/api/docs/` | Swagger UI |
| `http://localhost:8000/api/redoc/` | ReDoc |

---

## 5. Información que aún NECESITAMOS conseguir

Copia del plan-accion-fase1.md, sigue siendo pendiente:

- 🔴 Shapefile oficial de barrios de Popayán (Alcaldía o DANE MGN)
- 🔴 Registro histórico de intervenciones ejecutadas (Urbaser/Alcaldía)
- 🔴 Horarios de barrido validados oficialmente (Urbaser)
- ⚠️ Mapeo layer → macroruta para las 2,069 microrutas sin asignar
- ⚠️ Cronogramas de marzo-diciembre 2026 (solo tenemos febrero)

Ninguno bloquea la demo — todos tienen mitigaciones funcionales ya implementadas.

---

## 6. Resumen ejecutivo

| Fase | Duración | Entrega |
|------|----------|---------|
| **Ya completado** | — | Backend 95% + Frontend 85% funcionando |
| **Demo mínima** | 1-2h | Subida de evidencias end-to-end |
| **Demo pulida** | +4-5h | Mapa real + ServiceContent completo + .env |
| **Post-demo** | TBD | JWT, tests, integración Fase 2 |

**Recomendación:** avanzar primero con "Demo mínima" (subida de evidencias) para cerrar el ciclo ciudadano-supervisor. El resto son pulimiento visual.
