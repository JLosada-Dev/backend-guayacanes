# Frontend Changelog

Log granular de mejoras aplicadas al frontend (`/frontend-guayacanes`) durante la Fase A.

El directorio del frontend es externo a este repo. Este archivo documenta los cambios para trazabilidad desde el backend.

---

## #1 — Cliente axios con variables de entorno

**Fecha:** 2026-04-14
**Esfuerzo:** 20 min

### Problema
- Dos instancias separadas de axios (`core.ts` y `urbaser.ts`)
- `baseURL` hardcoded a `/api/v1` en ambos
- Sin forma limpia de cambiar el endpoint para staging/production
- Sin archivo `.env.example` para documentar configuración

### Cambios

**Nuevo:** `src/api/client.ts`

Cliente axios compartido que lee configuración desde variables de entorno de Vite:

```typescript
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? '/api/v1',
  timeout: Number(import.meta.env.VITE_API_TIMEOUT ?? 15000),
})
```

**Modificado:** `src/api/core.ts` y `src/api/urbaser.ts`

Ambos importan `apiClient` desde `./client` en vez de crear su propia instancia.

**Nuevo:** `.env.example`

```
VITE_API_URL=/api/v1
VITE_API_TIMEOUT=15000
```

### Validación
- `npx tsc --noEmit` pasa sin errores
- Dev mode sigue funcionando (proxy de Vite intacto)
- Production ready: basta con crear un `.env.production` apuntando al dominio real

### Beneficios
- Una sola fuente de verdad para la configuración de HTTP
- Timeout configurable (antes era default de axios = 0 / infinito)
- `.env.example` documenta las variables esperadas
- Deploy a staging/prod ya no requiere modificar código

---

## #2 — Mostrar `response_time` en modal de aspecto

**Fecha:** 2026-04-14
**Esfuerzo:** 0 min (verificación — ya estaba implementado)

### Hallazgo
Durante la auditoría del frontend reporté que `response_time` no se mostraba en el `AspectModal`. Al revisar el código real, **ya está implementado** en `src/components/AspectModal.tsx` líneas 59-67, con icono `Clock` de lucide-react y estilo destacado en fondo amber. El tipo `AspectContent` ya incluye el campo.

### Estado
No se requiere ningún cambio. La auditoría inicial fue inexacta en este punto — el frontend tenía esta feature completa desde antes.

---

## #3 — Mostrar `frequency` en cards de servicio

**Fecha:** 2026-04-14
**Esfuerzo:** 15 min

### Problema
Las cards del paso 1 del wizard (`Step1Service`) mostraban solo el icono + título + summary del servicio. El campo `frequency` (ej: "Residencial: 2 veces por semana · Vías principales: diario Lu-Sá · ...") estaba en el backend pero no se mostraba en ningún lado.

### Cambios

**Modificado:** `src/components/complaint/Step1Service.tsx`

- Agregado `CalendarClock` al import de lucide-react
- Después del summary, renderizar un pill/badge con icono + frecuencia si `service.content.frequency` existe

```tsx
{service.content?.frequency && (
  <div className="flex items-center gap-1.5 mt-2 text-xs text-gray-600 bg-gray-100 rounded-full px-2.5 py-1 w-fit">
    <CalendarClock size={12} className="flex-shrink-0" />
    <span className="line-clamp-1">{service.content.frequency}</span>
  </div>
)}
```

### Validación
- `npx tsc --noEmit` pasa
- El pill es opcional: si el servicio no tiene `content` o no tiene `frequency`, no se renderiza
- `line-clamp-1` evita que textos largos rompan el layout

### Beneficios
- El ciudadano sabe de antemano la frecuencia contractual antes de abrir el servicio
- Aprovecha contenido editorial ya cargado (fixtures `core_service_content.json`)
- Refuerza el concepto "deber ser" del sistema — el ciudadano ve la promesa contractual

---

## #4 — Modal "Ver más" con `full_description` y `citizen_rights`

**Fecha:** 2026-04-14
**Esfuerzo:** 30 min

### Problema
Los campos `full_description` y `citizen_rights` del `ServiceContent` (con referencias a Ley 1755/2015, Decreto 1077/2015, Resolución CRA 720) se cargaban desde el backend pero nunca se mostraban al ciudadano. Esto es información importante legalmente — el ciudadano debe conocer sus derechos antes de presentar una PQR.

### Cambios

**Nuevo:** `src/components/ServiceInfoModal.tsx`

Modal modal similar a `AspectModal` pero centrado en información del servicio:
- Icono `FileText` + `full_description` en párrafo principal
- Icono `Scale` + `citizen_rights` en caja destacada azul con estilo legal
- `whitespace-pre-line` para respetar saltos de línea del texto fuente
- Scroll interno si el contenido es largo (`max-h-[90vh] overflow-y-auto`)
- Botón único "Entendido" (no hay acción destructiva)

**Modificado:** `src/components/complaint/Step1Service.tsx`

Cambios:
- `<button>` externo reemplazado por `<div role="button" tabIndex={0}>` (HTML válido — no se puede anidar button dentro de button)
- Manejo de teclado agregado para accesibilidad (Enter/Space)
- Botón "Ver más" con icono `Info` alineado a la derecha del nombre del servicio
- `e.stopPropagation()` en el botón para no disparar la selección del servicio
- `ServiceInfoModal` renderizado al final con estado `infoService`

### Validación
- `npx tsc --noEmit` pasa
- El modal aparece solo si el servicio tiene `content` (graceful fallback)
- La selección del servicio (click en la card completa) sigue funcionando
- El botón "Ver más" no dispara la selección (stopPropagation)

### Beneficios
- **Cumplimiento legal:** el ciudadano puede consultar sus derechos y base normativa antes de presentar la PQR
- **Educación:** el `full_description` explica qué cubre el servicio (222 rutas, 9 frecuencias, etc.) sin saturar la card principal
- **Patrón consistente:** el mismo diseño que `AspectModal`, reforzando la navegabilidad
- **Accesibilidad mejorada:** `role="button"` + `tabIndex` + `onKeyDown` mantienen la card navegable por teclado

### Comportamiento visual

```
┌─────────────────────────────────────────────────┐
│ 🗑️  Barrido y Limpieza              [ℹ️ Ver más]│
│    Barrido de vías, separadores...              │
│    🕐 Residencial: 2x semana · Vías...          │
└─────────────────────────────────────────────────┘
                                              ↓ click Ver más
┌─────────────────────────────────────────────────┐
│ Barrido y Limpieza                         [✕] │
├─────────────────────────────────────────────────┤
│ 📄 SOBRE ESTE SERVICIO                          │
│    El servicio de Barrido y Limpieza cubre...   │
│                                                 │
│ ┌───────────────────────────────────────────┐   │
│ │ ⚖️  TUS DERECHOS                           │   │
│ │    Usted tiene derecho a:                 │   │
│ │    (1) Que las vías y áreas públicas...   │   │
│ │    ...                                    │   │
│ │    Base legal: Decreto 1077 de 2015...    │   │
│ └───────────────────────────────────────────┘   │
├─────────────────────────────────────────────────┤
│              [ Entendido ]                      │
└─────────────────────────────────────────────────┘
```

---

## #5 — Subida de evidencias con preview

**Fecha:** 2026-04-14
**Esfuerzo:** 1h 30min (incluye bug fix en backend)

### Problema
El backend expone `POST /api/v1/urbaser/evidence/` para subir fotos de evidencia, y acabamos de poblar `how_to_evidence` con instrucciones para el ciudadano sobre cómo documentar el problema. **Pero el frontend nunca llamaba el endpoint** — el ciudadano leía las instrucciones y se quedaba sin forma de subir la foto. Contradicción directa.

### Bug encontrado en backend durante la implementación

Al probar el endpoint con curl apareció un `IntegrityError: null value in column "complaint_id"`. La causa: el `EvidenceSerializer` no incluía `complaint` en `Meta.fields`, por lo que el campo nunca se procesaba desde el request.

**Fix:** agregado `'complaint'` a `fields` en `apps/infra_servicios_publicos_urbaser/serializers.py`. Validado con curl → HTTP 201 + evidencia visible en `/complaints/15/`.

### Cambios en frontend

**Tipos actualizados** (`src/types/index.ts`):
- Nueva interfaz `Evidence { id, image, uploaded_at }`
- `Complaint.evidence?: Evidence[]` añadido como opcional

**API** (`src/api/urbaser.ts`):
```typescript
export const uploadEvidence = (complaintId: number, file: File) => {
  const form = new FormData()
  form.append('complaint', String(complaintId))
  form.append('image', file)
  return apiClient.post<Evidence>('/urbaser/evidence/', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then(r => r.data)
}
```

**Store** (`src/store/complaintStore.ts`):
- `evidenceFiles: File[]` + `setEvidenceFiles()` agregados
- Limpieza de `evidenceFiles` en `reset()`

**Nuevo componente** (`src/components/EvidenceUploader.tsx`):
- Grid responsive con preview de hasta 4 fotos (aspect-square)
- Botón "Agregar" con placeholder diferenciado (primer slot vs siguientes)
- Validaciones del lado del cliente:
  - Máximo 4 archivos
  - Máximo 8 MB por archivo
  - Solo tipo `image/*`
- Remove per-file con botón X sobre cada preview
- Mensajes de error inline si una validación falla
- `URL.createObjectURL` con cleanup en el `useEffect` unmount

**Step4Confirm actualizado** (`src/components/complaint/Step4Confirm.tsx`):
- `EvidenceUploader` renderizado después de la descripción
- Flow de submit actualizado:
  1. `createComplaint()` → obtiene `result.id`
  2. Si hay archivos, bucle secuencial `uploadEvidence(id, file)`
  3. Track de progreso en `uploadProgress = { done, total }`
  4. Si alguna foto falla, se registra en `failed[]` y se muestra warning pero no bloquea
- Botón del submit cambia texto según fase:
  - `"Enviar denuncia"` → `"Enviando..."` → `"Subiendo fotos 2/4..."`
- Pantalla de éxito muestra warning ambar si hay `partialError`

### Validación
- `npx tsc --noEmit` pasa en frontend
- `curl` test exitoso: `POST /evidence/` retorna 201 + URL absoluta
- `GET /complaints/15/` confirma que el evidence aparece en la lista
- Flow end-to-end manual pendiente de confirmación en el navegador

### Beneficios
- **Cierra el loop ciudadano:** ahora el `how_to_evidence` que lee el usuario culmina en una acción real
- **UX robusta:** preview antes de enviar, límites claros, errores amigables
- **Tolerancia a fallos:** si falla una foto individual no se pierde la denuncia
- **Progreso visible:** el usuario sabe cuántas fotos faltan por subir
- **Mobile-friendly:** `accept="image/*"` abre la cámara directamente en iOS/Android

### Comportamiento visual

```
Paso 4 — Confirma tu denuncia
┌─────────────────────────────────────────────┐
│ Servicio:       Barrido y Limpieza          │
│ Problema:       Frecuencia no cumplida      │
│ Ubicación:      GPS                         │
├─────────────────────────────────────────────┤
│ Descripción adicional (opcional)            │
│ [textarea]                                  │
├─────────────────────────────────────────────┤
│ Fotos de evidencia (opcional · hasta 4)     │
│ ┌────┐ ┌────┐ ┌────┐ ┌────┐                 │
│ │ ✕  │ │ ✕  │ │ 📷 │ │    │                 │
│ │IMG │ │IMG │ │+   │ │    │                 │
│ └────┘ └────┘ └────┘ └────┘                 │
├─────────────────────────────────────────────┤
│  [  Subiendo fotos 2/3...  ]                │
└─────────────────────────────────────────────┘
```
