---
description: 'Usar para estructurar la salida física del archivo mvp_[nombre_corto].md en la carpeta product-manager. Define las secciones canónicas obligatorias validadas por el Watcher de BMAD.'
applyTo: '**'
---

# Plantilla Determinista del Plan MVP

> Estructura estricta para el artefacto generado por el Product Manager (`mvp_[nombre_corto].md`).
> Las secciones señaladas son obligatorias y evaluadas por el contrato de handoff del Watcher.

---

## Convención de Nombres de Archivo
```
mvp_[nombre_corto].md
```
- `nombre_corto`: snake_case, máximo 4 palabras, derivado del nombre del archivo Product Brief (ej. de `pb_reserva_citas.md` se genera `mvp_reserva_citas.md`).

---

## Estructura Canónica Obligatoria

```markdown
# PLAN ESTRATÉGICO Y BACKLOG DEL MVP: {{TITULO_DEL_PRODUCTO}}

- **Documento Fuente:** {{NOMBRE_ARCHIVO_PRODUCT_BRIEF}}
- **Fecha de Elaboración:** {{FECHA_ACTUAL}}
- **Product Manager:** Agente Orquestador BMAD (Fase M)

---

## 1. VISIÓN ESTRATÉGICA DEL MVP
*(Sección evaluada por el Quality Gate del Watcher)*

- **Foco de Gestión:** {{Resumen analítico de 2 a 3 líneas describiendo cuál es la hipótesis transaccional crítica que el equipo ágil debe construir y validar primero}}.
- **Criterio de Éxito Rector:** {{Métrica cuantitativa o evidencia de negocio extraída del Product Brief que determina si el MVP fue exitoso}}.

---

## 2. BACKLOG INICIAL (ÉPICAS FUNCIONALES)
*(Sección evaluada por el Quality Gate del Watcher)*

Organización del alcance en bloques de valor estructurados bajo el estándar de Ruta Crítica (P1 a Pn):

### [P1] Épica: {{Nombre de la Funcionalidad Core}}
- **Descripción de Negocio:** {{Qué resuelve esta épica a nivel macro}}.
- **Justificación de Prioridad:** {{Por qué esta épica constituye el núcleo indispensable del MVP}}.
- **Trazabilidad PRD:** {{Sección o requerimiento del Product Brief que la origina}}.

### [P2] Épica: {{Nombre de la Funcionalidad Dependiente / Catálogo}}
- **Descripción de Negocio:** {{Qué resuelve}}.
- **Justificación de Prioridad:** {{Por qué ocupa el segundo nivel de prelación}}.
- **Trazabilidad PRD:** {{Referencia al brief}}.

### [P3] Épica: {{Nombre de Autogestión o Siguiente Prioridad}}
- **Descripción de Negocio:** {{Qué resuelve}}.
- **Justificación de Prioridad:** {{Motivo de prelación}}.
- **Trazabilidad PRD:** {{Referencia al brief}}.

<!-- Continuar con P4 y P5 según el alcance real del brief. Prohibido inventar épicas fuera del alcance -->

---

## 3. RIESGOS, DEPENDENCIAS Y PUNTOS ABIERTOS

### Bloqueantes Potenciales
- {{Listado de supuestos del PRD que, de resultar inválidos, detendrían el desarrollo}}.

### Ambigüedades de Negocio (Para Control del BA)
- {{Preguntas abiertas o vacíos del PRD que el Business Analyst debe tener la precaución de no inventar ni asumir sin etiquetar}}.

---

## 4. ORDEN DE DELEGACIÓN PARA EL BA Y GITOPS
*(Instrucción que se inyecta en tracker_bmad.md)*

⚠️ **REGLA ESTRICTA DE NOMENCLATURA (IDENTIFICADOR SECUENCIAL):**
Antes de generar la macro GitOps o el Handoff, el `@PM` DEBE leer obligatoriamente el archivo `specs/README.md` (Product State Ledger).
1. Analiza la columna "N°" de la tabla de funcionalidades para encontrar el correlativo numérico más alto.
2. Suma +1 a ese número y formatéalo con 3 dígitos (ej. si el último es `002`, el nuevo será `003`).
3. Este prefijo debe usarse obligatoriamente para crear el identificador universal de la Historia: `XXX-HU_[nombre_corto]`.
4. Si la tabla está vacía o es la primera funcionalidad, inicia en `001-HU_[nombre_corto]`.

Este identificador exacto debe inyectarse obligatoriamente en TRES (3) lugares:
1. En el registro de la nueva fila que actualizarás en `specs/README.md` (Ledger).
2. En la macro GitOps del Watcher para la creación de la rama aislada.
3. En la orden de delegación explícita para el `@BA`.

Obligatorio inyectar en el tracker en líneas separadas:
```markdown
@WATCHER: GITOPS-BRANCH-CREATE feat/XXX-HU_{{nombre_corto}}
{{Texto de delegación donde explícitamente se le ordena al @BA crear el archivo físico `XXX-HU_{nombre_corto}.md`}}.
```


---

### ⚠️ Directiva para Ecosistemas Preexistentes (Modo Brownfield)
Si existe el archivo `.specify/memory/constitution.md`:
1. **Sección 2 (Backlog del MVP):** Al definir y justificar la prioridad de las Épicas (P1, P2, ...), categorizar el tipo de impacto respecto al legado (ej. "Extensión de componente existente", "Nueva capacidad desacoplada" o "Integración con Core preexistente").
2. **Sección 3 (Riesgos y Dependencias):** Identificar explícitamente los riesgos de regresión, acoplamiento operativo y compatibilidad con el sistema heredado documentado.
3. **Si el archivo NO existe (Modo Greenfield):** Estructura el Backlog del MVP estándar basado únicamente en el Product Brief.


[IMPORT_SKILL: skills/tracker-logger/SKILL.md]
