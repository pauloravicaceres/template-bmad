# Mejoras propuestas para `constitution.md`

Comparación entre `constitution-old.md` (constitución técnica global previa) y
`constitution.md` (política operativa actual del motor multiworkspace y multiproveedor).
Las propuestas no están aplicadas.

## 1. Reglas a rescatar

### 1.1 Ubicación del código de producción

**Origen:** sección «Estructura de carpetas del repositorio» de `constitution-old.md`, que fijaba
`app/backend/` y `app/frontend/` y exigía ese prefijo en `plan.md`, `tasks.md` y `tech-design_*.md`.

**Situación actual:** `constitution.md` no indica dónde reside el código. El runtime ya usa
`project.json.config.code_dirs` (por defecto `app/backend` y `app/frontend`) y en Brownfield admite
carpetas existentes como `server` o `web`.

**Propuesta:** añadir al final de «Brownfield, Greenfield y validación»:

```text
El código de producción reside solo en `code_dirs.backend` y `code_dirs.frontend`
del workspace (por defecto `app/backend` y `app/frontend`). Plan, tareas y diseño
técnico usan rutas con ese prefijo; ningún archivo de código va en la raíz del
workspace ni en sus directorios operativos.
```

### 1.2 No abrir una rama nueva con la anterior abierta

**Origen:** «Regla de ramas GitOps» de `constitution-old.md`: PM no emite `GITOPS-BRANCH-CREATE` si
la HU anterior no se cerró con `GITOPS-MERGE-CLOSE`.

**Situación actual:** `constitution.md` solo dice «No abrir múltiples HUs». El código no lo impide:
`gitops_branch_create()` (`bmad_runtime/workflow.py`) vuelve a la rama base y crea la rama nueva
aunque otra siga sin cerrar.

**Propuesta:** añadir en «Handoffs y ciclo BMAD/SDD», después de «cerrar prematuramente una rama.»:

```text
PM no emite `GITOPS-BRANCH-CREATE` mientras la rama de la HU anterior no se haya
cerrado con `GITOPS-MERGE-CLOSE`.
```

### Tamaño

Ambas adiciones suman unos 450 caracteres. `technical_context.assemble()` incluye el texto completo
de la política solo si ocupa 7000 caracteres o menos; con las adiciones sigue por debajo de ese límite.

## 2. Contenido que no conviene rescatar

| Regla de `constitution-old.md` | Motivo |
|---|---|
| Ramas `feat/HU_[nombre_corto]` | Reemplazada por `feat/XXX-HU_nombre_en_snake_case`, ya vigente |
| READY-FOR-DEV dispara el merge y el cierre de rama | Contradice el flujo actual: READY-FOR-DEV habilita desarrollo y la rama se cierra tras Code Review |
| QA Tech cierra la rama con `GITOPS-MERGE-CLOSE` | El cierre corresponde a la certificación final de Code Review |
| «Amnesia estratégica» tras conflicto de merge | El runtime actual no la cumple (ver sección 3) |
| Idioma, modo anti-conversacional, macros, ledger, identificador universal, vertical slicing y feature branch prolongada | Ya cubiertos en `constitution.md` |

Lo multiproveedor no aporta reglas nuevas: `constitution.md` ya prohíbe cambiar proveedor, modelo o
effort para eludir un error o una capacidad pendiente.

## 3. Defecto relacionado en el runtime (no constitucional)

Ante un conflicto de merge, `gitops_merge_close()` (`bmad_runtime/workflow.py`) aborta el merge,
anexa al tracker un aviso que afirma que, al reiniciar, «el sistema asumirá el cierre exitoso», y
termina con `sys.exit(1)`. Leyendo el código (sin reproducirlo):

- El evento de esa línea queda `in_flight` en `state/state.sqlite3` y el cursor no avanza, porque
  `save_cursor()` se ejecuta después de procesar el lote de líneas.
- Al reiniciar, el watcher relee la línea y `StateStore.claim()` lanzaría `ReconciliationRequired`,
  salvo que el operador marque el evento con
  `python -m bmad_runtime.state --workspace RUTA --acknowledge event:ID --confirm`.
- El aviso indica `python watcher_bmad.py` sin `--workspace`/`--project`, que falla porque el
  registro `projects` exige selección explícita.

Corrección sugerida, en `workflow.py` y no en la constitución: que el aviso describa la
reconciliación real (resolver el merge, inspeccionar y reconocer el evento, reiniciar el watcher con
la misma selección) y use el comando con `--workspace`/`--project`.
