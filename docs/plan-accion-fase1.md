# Plan de Acción — Completar Fase 1

Estado al **14 abril 2026**. Enfocado en **barrido y limpieza** + **zonas verdes** (los dos servicios activos).

El backend esta operativo con datos cargados y pipeline SLA funcionando end-to-end, pero hay gaps específicos que impiden que las alertas se generen con precisión contractual. Este documento lista lo que se puede hacer con la información que tenemos ahora y lo que requiere información externa.

---

## 1. Estado actual — lo que funciona

| Componente | Estado | Notas |
|------------|--------|-------|
| Modelos Django | ✅ Completo | 14 modelos registrados, migraciones aplicadas |
| API REST v1 | ✅ Completo | 12 endpoints validados con curl + Bruno |
| Pipeline SLA (signals) | ✅ Activo | ST_DWithin funciona en EPSG:3116 |
| Admin Django | ✅ Completo | 15 registros con GISModelAdmin |
| 9 comunas | ✅ Cargadas | Desde `U2_COMUNAS.shp` |
| 8 macrorutas de barrido | ✅ Cargadas | Con start_time correcto, `end_time=null` (bug) |
| 1,731 microrutas de barrido | ✅ Cargadas | Con geometría y asignación a macroruta |
| 313 zonas verdes | ✅ Cargadas | 96 con nombre real, 217 auto-generadas |
| 5 servicios + 11 aspectos | ✅ Cargados | Desde fixtures JSON |
| Demo end-to-end | ✅ Validado | 14 denuncias → 27 alertas → 5 métricas |

---

## 2. Gaps bloqueantes para Fase 1 completa

### 2.1 🔴 Ventanas horarias de barrido incorrectas

**Problema:** todas las macrorutas tienen `end_time=null`. El código en [receivers.py:112](../apps/infra_servicios_publicos_urbaser/receivers.py) interpreta null como 23:00, por lo que cualquier denuncia entre 5am y 11pm cae en la ventana. Resultado: **no se generan violations por horario en barrido**.

**Fix con información que TENEMOS:**

Los horarios están en `guayacanes_docs/urbaser-servicios-pdf/RUTAS-URBASER-2024.md` (basado en el PDF oficial del PPS 2024). Se pueden inferir las ventanas de trabajo a partir de las frecuencias documentadas:

| Código | Start | End (inferida) | Fuente |
|--------|-------|----------------|--------|
| B211 | 06:00 | 14:00 | Frecuencia "Lu·Ju 6:00–14:00" |
| B212 | 06:00 | 14:00 | Frecuencia "Ma·Vi 6:00–14:00" |
| B213 | 06:00 | 14:00 | Frecuencia "Mi·Sá 6:00–14:00" |
| 611 | 05:00 | 13:00 | Vías principales turno mañana |
| 621 | 13:00 | 21:00 | Centro histórico turno tarde |
| 631B | 19:00 | 03:00 | Centro histórico turno noche (cruza medianoche) |
| 117B | 09:00 | 13:30 | Centro histórico dominical |
| 127B | 10:00 | 14:30 | Plazas de mercado dominical |

**Acción:** actualizar `MACROROUTES_DEF` en [load_sweeping.py](../apps/infra_servicios_publicos_urbaser/management/commands/load_sweeping.py) con los `end_time`. Re-correr `make data`.

**Complejidad adicional:** ruta 631B cruza medianoche — hay que ajustar también `receivers.py` para manejar el caso `start_hour > end_hour` (ventana que cruza medianoche).

**Esfuerzo:** 45 min (30 min edit + 15 min test)

---

### 2.2 🔴 Cronograma de cortes de cesped sin cargar

**Problema:** el modelo `CuttingSchedule` existe pero está vacío. Sin schedules:
- No hay referencia para `overdue=True` en el pipeline
- Las denuncias de zonas verdes no pueden generar violations salvo por el único schedule creado manualmente en `seed_complaints`

**Fix con información que TENEMOS:**

El archivo `guayacanes_docs/urbaser-servicios-pdf/zonas-verdes/cronograma-de-cesped-febrero-2026.pdf` tiene la tabla completa de febrero 2026: 290 polígonos con ID, nombre, área, 1ª y 2ª fecha del mes.

**Acción:**
1. Parsear el PDF con `pdfplumber` o `pypdf2`
2. Por cada fila: matchear el polígono contra `GreenZone` por nombre (fuzzy match)
3. Crear `CuttingSchedule(zone=X, scheduled_date=fecha, executed=False)` para las 1ª y 2ª fechas
4. Idealmente iterar sobre los 12 PDFs mensuales (ENERO-2026.pdf a DICIEMBRE-2026.pdf) para tener el año completo

**Riesgo del fuzzy match:** 217 de 313 zonas verdes tienen nombre auto-generado ("Separador 001"), no matchean con el PDF. Solo las 96 de EP3 tienen nombre real y pueden matchearse.

**Mitigación:** empezar con las 96 matcheables. Los 217 separadores sin nombre quedan sin schedule pero no bloquean el pipeline (los schedules cubren los parques nombrados que es donde más denuncias ciudadanas habrá).

**Esfuerzo:** 2-3 horas (extracción PDF + matching + carga)

---

### 2.3 ⚠️ Microrutas de barrido sin macroruta asignada

**Problema:** el shapefile `U18_VIAL.shp` tiene 3,800 LineStrings, pero solo 1,731 quedaron asignados a una macroruta. 2,069 microrutas están sin asignar porque su `Layer` no matcheó ninguna de las 8 macrorutas conocidas.

**Fix con información que TENEMOS:**

Revisar qué valores únicos tiene el campo `Layer` en el shapefile vs el mapeo actual en [load_sweeping.py](../apps/infra_servicios_publicos_urbaser/management/commands/load_sweeping.py):

```python
# Mapeo actual (revisar)
LAYER_TO_MACROROUTE = {
    'VC1':     '611',
    'VARIANT': 'B211',
    'VAP-2':   'B212',
    # ...
}
```

**Acción:** inspeccionar los layers no mapeados y cruzarlos con las zonas geográficas reales. Algunos probablemente sean rutas de recolección (no barrido), que hay que descartar en lugar de mapearlas.

**Esfuerzo:** 1-2 horas (investigación + ajuste del mapeo)

**Impacto:** aumenta cobertura del SLA de barrido. Actualmente hay rutas de barrido reales que no disparan alertas porque no están en la BD.

---

## 3. Mejoras no bloqueantes (nice-to-have)

### 3.1 Contenido editorial del portal ciudadano

`ServiceContent` y `AspectContent` existen pero están vacíos. El PDF `PPS-POPAYAN-2024.pdf` contiene:
- Descripción oficial de cada servicio
- Frecuencias contractuales
- Derechos del ciudadano
- Tiempos de respuesta

**Acción:** leer el PPS y poblar via admin o fixtures.

**Esfuerzo:** 3-4 horas (lectura + redacción del texto + carga)

**Impacto:** el campo `content` de los endpoints de `/services/` y `/aspects/` dejan de retornar `null`. El portal ciudadano tiene texto real.

---

### 3.2 Nombres reales para los 217 separadores sin nombre

217 zonas verdes tienen nombre auto-generado tipo "Separador 001". El PDF de febrero 2026 tiene 290 nombres reales.

**Acción:** fuzzy match por proximidad geográfica entre centroide del polígono shapefile y la ubicación descrita en el PDF. Para los separadores, intentar matchear por los tramos de vía.

**Esfuerzo:** 3-5 horas (requiere análisis caso por caso)

**Impacto:** mejora la identificación de zonas en las alertas SLA. No afecta la detección de violations.

---

### 3.3 Historial de intervenciones ejecutadas

Actualmente `Intervention` está vacío. Sin historial, el pipeline no puede calcular `days_since_intervention` correctamente — siempre cae en el branch `overdue` que requiere schedules.

**Si conseguimos registros de intervenciones realizadas** (ver sección 4.3), se carga con un command similar a `load_cutting_schedule`.

---

## 4. Información que NECESITAMOS CONSEGUIR

Esta sección lista lo que no tenemos y por qué.

### 4.1 🔴 Horarios de barrido validados oficialmente

**Qué tenemos:** `RUTAS-URBASER-2024.md` lista 9 frecuencias con start_time pero no siempre end_time explícito por ruta.

**Qué falta:** confirmación oficial de las ventanas exactas de trabajo por cada código (B211 dura desde las 6:00 hasta ¿cuándo exactamente?).

**Cómo conseguirlo:**
- Preguntar directamente a Urbaser Popayán (Supervisión de operaciones)
- Revisar el `Macrorutas-Publicar-Barrido-2024.pdf` página por página (no lo hemos abierto a profundidad)
- Validar con el Plan de Prestación (PPS-POPAYAN-2024.pdf)

**Mientras tanto:** usar los horarios inferidos de la sección 2.1. Son razonables pero no oficiales.

---

### 4.2 🔴 Registro histórico de cortes ejecutados (intervenciones)

**Qué tenemos:** cronograma *planeado* (cuándo debían cortar) en PDFs mensuales.

**Qué falta:** registro de cuándo **efectivamente** cortaron cada zona. Sin esto, `days_since_intervention` siempre es null.

**Cómo conseguirlo:**
- Pedir a la Alcaldía los reportes de cumplimiento/interventoría que Urbaser entrega mensualmente
- Pedir acceso a bitácoras de campo del operador
- Plan B: registrar intervenciones prospectivamente (de acá en adelante) via admin

**Mientras tanto:** asumir que los schedules vencidos no ejecutados = violation. El pipeline ya soporta esta lógica.

---

### 4.3 🔴 Shapefile oficial de barrios de Popayán

**Qué tenemos:** 189 secciones censales DANE sin nombre + PDF de estratificación con 79 barrios nombrados sin geometría.

**Qué falta:** una capa única con nombre + geometría de cada barrio.

**Cómo conseguirlo:**
- Solicitar a Secretaría de Planeación Municipal — Alcaldía de Popayán
- Alternativa: descargar MGN 2022 de DANE y cruzar códigos con el PDF de estratificación (ver [barrios-opciones.md](barrios-opciones.md))
- Alternativa: OpenStreetMap (cobertura incompleta)

**Mientras tanto:** `Neighborhood.geom = null`. El sistema funciona con fallback a centroide de comuna. Las denuncias con coordenada GPS se guardan sin `neighborhood_id`.

**Impacto si no se consigue:** la precisión del `location_source` se mantiene en nivel comuna. No bloquea el pipeline SLA.

---

### 4.4 ⚠️ Mapeo oficial de microrutas de barrido (shapefile ↔ macrorutas)

**Qué tenemos:** 3,800 LineStrings con campo `Layer` (VC1, VARIANT, VAP-2, etc).

**Qué falta:** tabla oficial que asocie cada `Layer` del shapefile a un código de macroruta del PPS 2024. Actualmente inferimos 1,731 pero 2,069 quedan sin asignar.

**Cómo conseguirlo:**
- Pedir a Urbaser la leyenda del shapefile (qué significa cada `Layer`)
- Revisar los PDFs `Macrorutas-Publicar-Barrido-2024.pdf` con más detalle (posiblemente incluye tabla de equivalencias)
- Cruzar visualmente con QGIS superponiendo las macrorutas del PDF sobre el shapefile

**Mientras tanto:** la cobertura SLA es parcial. Funciona para las rutas asignadas, las 2,069 restantes no generan alertas (no es error, es cobertura incompleta).

---

### 4.5 ⚠️ Ruta oficial de zonas verdes (633, 631A, 631C)

**Qué tenemos:** mención en `RUTAS-URBASER-2024.md` de que la ruta 633 es la principal y 631A/631C son complementarias.

**Qué falta:** polígonos de cobertura de estas rutas. Las zonas verdes no están agrupadas por ruta en el sistema.

**Cómo conseguirlo:**
- Similar al 4.4 — pedir shapefile o asociación formal a Urbaser
- Inferir de la distribución geográfica de las 290 zonas

**Impacto:** no crítico. Las zonas verdes funcionan como polígonos independientes. La "ruta" es más para reportes operativos que para SLA.

---

### 4.6 ⚠️ Contenido editorial del PPS para portal ciudadano

**Qué tenemos:** el PDF `PPS-POPAYAN-2024.pdf` completo (665 KB).

**Qué falta:** extraer los textos relevantes para `ServiceContent` y `AspectContent`. Requiere lectura detallada del PDF, no es solo parsing automático.

**Cómo conseguirlo:**
- Asignar a alguien del equipo que lea el PDF y redacte los textos
- El PPS tiene esta información, solo hay que curarla

**Mientras tanto:** el campo `content` de la API retorna `null`. El portal debe manejar este caso.

---

## 5. Plan de acción priorizado

### Fase A — Fix del pipeline SLA (1 día)

**Prioridad máxima.** Desbloquea la detección real de violations.

1. ✅ Completado: `load_green_zones` + `seed_complaints`
2. 🔴 Pendiente: corregir `end_time` de macrorutas en `load_sweeping.py`
   - Actualizar `MACROROUTES_DEF` con los valores de la tabla 2.1
   - Manejar caso de ruta 631B (ventana que cruza medianoche) en `receivers.py`
3. 🔴 Pendiente: implementar `load_cutting_schedule.py`
   - Parsear `cronograma-de-cesped-febrero-2026.pdf` con `pdfplumber`
   - Fuzzy match contra `GreenZone.name`
   - Crear `CuttingSchedule` para las 96 zonas con nombre real
4. Re-correr `make demo` y validar que ahora se generan violations por horario en barrido y por schedule vencido en zonas verdes

**Criterio de éxito:** `seed_complaints` genera ≥5 violations en barrido y ≥3 violations en zonas verdes con lógica correcta.

---

### Fase B — Calidad de datos (2-3 días)

5. Investigar los 2,069 layers de `U18_VIAL.shp` no asignados
6. Parsear los 11 PDFs de cronograma restantes (MARZO a DICIEMBRE 2026)
7. Intento de fuzzy match nombre para los 217 separadores sin nombre

---

### Fase C — Portal ciudadano (1-2 días)

8. Redacción de `ServiceContent` desde el PPS 2024
9. Redacción de `AspectContent` para los 11 aspectos

---

### Fase D — Requiere info externa (bloqueado)

10. Shapefile oficial de barrios → contactar Alcaldía
11. Registro histórico de intervenciones → contactar Urbaser/interventoría
12. Horarios exactos de barrido validados → contactar Urbaser

---

## 6. Resumen ejecutivo

### Lo que podemos hacer ya

- Fix del bug de `end_time` — 45 min
- Cargar cronograma de cortes de febrero 2026 — 2-3h
- Revisar mapeo de microrutas — 1-2h
- Redactar contenido editorial del PPS — 3-4h

**Total esfuerzo con info actual: ~1-2 días de trabajo enfocado.**

### Lo que requiere información que no tenemos

- Horarios de barrido oficialmente validados (Urbaser)
- Registro histórico de intervenciones ejecutadas (Urbaser/Alcaldía)
- Shapefile de barrios (Alcaldía o DANE)
- Mapeo completo de layers del shapefile (Urbaser)

### Qué es suficiente para la demo

**Lo que ya tenemos + Fase A basta para el demo.** Las demás son mejoras incrementales que pueden hacerse post-demo o en paralelo.
