# Rutas y servicios — Contexto de negocio

Resumen del contrato Urbaser Popayán 2024 para el equipo de desarrollo.
Fuente completa: `guayacanes_docs/urbaser-servicios-pdf/RUTAS-URBASER-2024.md` (1,389 líneas) y `PPS-POPAYAN-2024.pdf`.

---

## Servicios activos (Fase 1)

Estos son los dos servicios habilitados en el sistema ahora mismo (`active=true` en `core_service`):

| ID | Nombre | Slug | PPS ref. |
|----|--------|------|---------|
| 1 | Barrido y Limpieza | `sweeping-cleaning` | Tabla 9 |
| 2 | Corte de Césped y Zonas Verdes | `green-zones` | Tabla 12 |

### Aspectos de queja por servicio

**Barrido y Limpieza (7 aspectos):**

| ID | Slug | Descripción |
|----|------|-------------|
| 1 | `scope` | Alcance del barrido incompleto |
| 2 | `frequency` | Frecuencia de barrido no cumplida |
| 3 | `cleanliness` | Limpieza deficiente |
| 4 | `sand-residue` | Arenilla no recogida |
| 5 | `weed-removal` | Desmoñe sin realizar |
| 6 | `bins` | Cestas sin vaciado |
| 7 | `quality` | Calidad del barrido deficiente |

**Corte de Césped y Zonas Verdes (4 aspectos):**

| ID | Slug | Descripción |
|----|------|-------------|
| 8 | `cutting-not-done` | Corte de césped no realizado |
| 9 | `frequency-missed` | Frecuencia de corte incumplida |
| 10 | `pruning-waste-left` | Residuos de poda sin recoger |
| 11 | `area-deteriorated` | Área verde deteriorada o descuidada |

---

## Servicios Fase 2 (inactivos por ahora)

| ID | Nombre | Slug |
|----|--------|------|
| 3 | Recolección y Transporte | `waste-collection` |
| 4 | Lavado de Vías y Áreas Públicas | `street-washing` |
| 5 | Poda de Árboles | `tree-pruning` |

---

## Macrorutas de barrido (8 rutas)

Estas son las rutas activas en Fase 1. Corresponden a los `SweepingMacroRoute` del modelo de operaciones (pendiente de implementar). La geometría viene de `U18_VIAL.shp`.

| Código | Tipo | Días | Hora | Comunas principales |
|--------|------|------|------|---------------------|
| B211 | Residencial | Lu · Ju | 06:00 | 1, 2, 3, 8, 9 |
| B212 | Residencial | Ma · Vi | 06:00 | 2, 4, 5, 7, 8, 9 |
| B213 | Residencial | Mi · Sá | 06:00 | 3, 4, 5, 6, 7 |
| 611 | Diario | Lu – Sá | 05:00 | Todas (vías principales, centro, mercados) |
| 621 | Diario | Lu – Sá | 13:00 | 4 (centro histórico — tarde) |
| 631B | Diario | Lu – Sá | 19:00 | 4 (centro histórico — noche) |
| 117B | Dominical | Domingo | 09:00 | 4 (centro histórico) |
| 127B | Dominical | Domingo | 10:00 | 4 (plazas de mercado) |

> Detalle completo de barrios por ruta: `guayacanes_docs/urbaser-servicios-pdf/RUTAS-URBASER-2024.md` — sección "MACRORUTAS DE BARRIDO".

---

## Macrorutas de recolección (35 rutas — Fase 2)

35 rutas en total: 32 urbanas + 3 rurales. No implementadas aún.

**Resumen por turno:**

| Turno | Días | Hora | Rutas |
|-------|------|------|-------|
| Diurno LMV | Lu · Mi · Vi | 05:00 – 17:00 | 311, 313, 315, 316, 317, 318, 319 |
| Diurno MJS | Ma · Ju · Sá | 05:00 – 17:00 | 312, 314, 320, 321, 322, 323, 324 |
| Nocturno LMV | Lu · Mi · Vi | 17:00 – 05:00 | 331, 333, 334, 335, 336, 337, 338, 339 |
| Nocturno MJS | Ma · Ju · Sá | 17:00 – 05:00 | 332, 340, 341, 342, 343, 344, 345 |
| Rural | Variable | Variable | 211 (Occidente), 212 (Nororiente), 213 (Suroriente) |

> Detalle completo: `guayacanes_docs/urbaser-servicios-pdf/RUTAS-URBASER-2024.md` — sección "MACRORUTAS DE RECOLECCIÓN".

---

## Zonas verdes (290 polígonos)

| Dato | Valor |
|------|-------|
| Total polígonos | 290 |
| Área total | 1,648,366.47 m² (~165 ha) |
| Ciclo contractual | ~11 días entre cortes |
| Frecuencia | 2 cortes por mes (inicio y segunda quincena) |
| Ruta principal | 633 (complementarias: 631A, 631C) |

**Fuentes geométricas** (se cargan juntas en `urbaser_green_zone`):
- `U19_ESPACIO_PUBLICO2.shp` — 11 parques urbanos
- `U19_ESPACIO_PUBLICO3.shp` — 96 nodos de espacio público
- `U19_ESPACIO_PUBLICO5.shp` — 72 rondas de ríos y corredores verdes
- `U1_POPAYAN BASE/SEPARADOR.shp` — 132 separadores viales

**Cronograma:** `guayacanes_docs/urbaser-servicios-pdf/zonas-verdes/cronograma-de-cesped-febrero-2026.pdf`
Contiene los 290 polígonos con nombre, área y fechas previstas de intervención.

---

## Inventario arbóreo (Fase 2)

- **18,123 individuos** catastrados en Popayán
- Reportes mensuales 2026 en: `guayacanes_docs/urbaser-servicios-pdf/zonas-verdes/`
  - `ENERO-2026.pdf` … `DICIEMBRE-2026.pdf` (12 archivos, ~14 MB total)
- Tipo de datos: mes, tipo de intervención (poda/tala/siembra), barrio/sector, cantidad

---

## Reglas SLA (para el módulo de auditoría)

Estas reglas definen cuándo un `Complaint` genera un `SLAAlert` automático. Se implementan como signal `post_save` en `receivers.py`.

### Barrido (`sweeping-cleaning`)

```
Si la denuncia:
  • tiene location dentro de 50m de una SweepingMicroRoute activa  (ST_DWithin)
  • Y la hora de created_at está FUERA de la ventana de operación de esa ruta
→ crear SLAAlert(type='violation')
```

### Zonas verdes (`green-zones`)

```
Si la denuncia:
  • tiene location dentro de 30m de una GreenZone  (ST_DWithin)
  • Y (fecha_hoy - last_intervention_date) > cycle_days
→ crear SLAAlert(type='violation')
```

### Métrica por comuna

Después de cada `SLAAlert`, se recalcula `CommuneMetric.violation_rate` para la comuna afectada:

```
violation_rate = SLAAlerts(type='violation', commune) / Complaints(commune)
```

Rango: `0.0` (sin incumplimientos) → `1.0` (todos son incumplimientos).
Usado por el heatmap del dashboard de la Alcaldía.

---

## Comunas de Popayán

| # | Área (ha) | Zona |
|---|-----------|------|
| 1 | 643.01 | Noroccidente |
| 2 | 701.52 | Nororiente |
| 3 | 243.17 | Centro-oriente |
| 4 | 273.28 | Centro histórico |
| 5 | 76.25 | Centro-sur (más pequeña) |
| 6 | 203.12 | Suroccidente |
| 7 | 167.98 | Occidente |
| 8 | 132.27 | Sur |
| 9 | 284.58 | Suroriente |
