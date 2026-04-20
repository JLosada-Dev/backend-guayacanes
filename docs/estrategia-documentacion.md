# Estrategia de Documentación — Backend + Frontend

**Fecha:** 14 abril 2026
**Estado:** provisional — a revisar cuando madure la estructura de repos

---

## Contexto

El proyecto tiene dos repos hermanos:

```
guyacanes/
  backend-guayacanes/     # Django + GeoDjango + PostgreSQL
  frontend-guayacanes/    # React + Vite + TypeScript
```

Inicialmente, toda la documentación se fue generando en `backend-guayacanes/docs/` porque es donde arrancó el trabajo técnico. Esto dejó el frontend sin README propio, lo cual es un problema si alguien clona solo ese repo.

---

## Decisión actual (14 abril 2026)

### Documentación distribuida

| Archivo | Ubicación | Propósito |
|---------|-----------|-----------|
| `README.md` | **backend** | Setup, stack, API summary, índice de docs del backend |
| `README.md` | **frontend** | Setup, stack, estructura, endpoints consumidos, troubleshooting del frontend |
| `CHANGELOG.md` | **frontend** | Log granular de cambios aplicados al frontend (copia) |
| `docs/frontend-changelog.md` | **backend** | Mismo contenido que `CHANGELOG.md` del frontend (copia) |

### Documentación solo en el backend

Los siguientes docs son del **sistema completo** (backend + frontend + infra + negocio), por eso viven solo en el backend para no duplicar:

- `docs/CONTEXT_GUYACANES.md` — arquitectura global
- `docs/estado-actual.md` — fuente única de verdad consolidada
- `docs/plan-accion-fase1.md` — gaps, pendientes, info externa
- `docs/plan-demo-completo.md` — integración backend + frontend
- `docs/changelog-fase-a.md` — changelog del backend
- `docs/admin-guide.md` · `docs/demo-guide.md` · `docs/rutas-y-servicios.md` · etc.

El `README.md` del frontend hace referencias explícitas a estos archivos en el repo backend:

```markdown
Ver plan completo en `../backend-guayacanes/docs/estado-actual.md`.
```

Esto funciona si el checkout local mantiene ambos repos como hermanos. Si alguien clona solo el frontend, los enlaces rotos son evidentes y llevan al nombre del repo backend.

---

## Riesgos conocidos

### 🔴 Desincronización del changelog

`frontend-guayacanes/CHANGELOG.md` y `backend-guayacanes/docs/frontend-changelog.md` son **dos copias físicas** con el mismo contenido.

Riesgo: si alguien actualiza uno y olvida el otro, divergen.

Mitigación hoy: **mantener las dos manualmente** tras cada cambio granular (vía `cp` después de editar).

### ⚠️ Enlaces relativos entre repos

`frontend-guayacanes/README.md` usa paths como `../backend-guayacanes/...`. Si el usuario renombra o mueve los directorios, los enlaces se rompen.

Mitigación hoy: documentar la convención en los READMEs.

### ⚠️ Docs del sistema completo solo en backend

Si alguien recibe solo el repo del frontend sin contexto, no tiene acceso directo a `CONTEXT_GUYACANES.md` ni `estado-actual.md`.

Mitigación hoy: el README del frontend menciona explícitamente dónde están esos docs.

---

## Opciones a futuro

Ordenadas de menor a mayor esfuerzo:

### Opción 1 — Mantener como está (estado actual)

Dos copias manuales del changelog, docs globales solo en backend.

**Pro:** cero setup.
**Contra:** desincronización silenciosa si se olvida `cp`.

### Opción 2 — Symlinks

```bash
cd frontend-guayacanes
ln -s ../backend-guayacanes/docs/frontend-changelog.md CHANGELOG.md
```

**Pro:** una sola fuente, siempre sincronizada.
**Contra:**
- No funciona en Windows sin permisos admin
- Git trata los symlinks diferente — requiere `git config core.symlinks true`
- Si se clona solo el frontend, el symlink queda roto

### Opción 3 — GitHub Actions para sincronizar

Workflow que detecta cambios en `frontend-changelog.md` del backend y los propaga al `CHANGELOG.md` del frontend via PR automático.

**Pro:** robusto, explícito en el historial de git.
**Contra:** infraestructura — requiere GitHub, PAT, configuración CI/CD.

### Opción 4 — Monorepo

Mover ambos proyectos a un solo repo:

```
guyacanes/
  backend/
  frontend/
  docs/              ← único lugar para toda la documentación del sistema
    CONTEXT.md
    estado-actual.md
    backend/
      README.md
      admin-guide.md
    frontend/
      README.md
      CHANGELOG.md
```

**Pro:** una sola verdad, versionado atómico entre backend y frontend, CI/CD unificado.
**Contra:**
- Migración no trivial (rewrite history, cambiar deploys)
- Requiere tooling adicional (pnpm workspaces, Turborepo, etc.)
- Decisión organizacional — afecta a todo el equipo

### Opción 5 — Paquetes NPM y documentación generada

Extraer los tipos TypeScript como paquete `@guyacanes/types` y auto-generar doc desde el código.

**Pro:** schemas compartidos, menos duplicación.
**Contra:** sobre-ingeniería para el tamaño actual del proyecto.

---

## Recomendación provisional

**Hoy:** mantener la Opción 1 (estado actual). Es suficiente mientras solo 1-2 personas editan los docs y se hacen cambios frecuentes.

**Si el equipo crece o se vuelve a editar el changelog con frecuencia:** migrar a Opción 4 (monorepo). Es la que mejor escala para un sistema que debe versionar backend + frontend + infra juntos.

**Descartadas por ahora:**
- Opción 2 (symlinks) — problemas de portabilidad
- Opción 3 (CI sync) — overengineer para el tamaño actual
- Opción 5 (paquetes) — premature optimization

---

## Acciones pendientes

- [ ] Revisar esta estrategia cuando el cronograma-de-cesped de marzo llegue o haya otro cambio grande en fixtures (¿se sigue duplicando manualmente?)
- [ ] Si se empieza a crear docs en `frontend-guayacanes/docs/` también, reevaluar
- [ ] Discutir con el equipo si monorepo es viable antes de una Fase 2
- [ ] Si hay más de 3 docs compartidos, considerar una carpeta `docs/` en la raíz del directorio padre `guyacanes/` con los docs globales
