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
- **Incluye:** {{Lista de capacidades que abarca la épica, tomadas del Product Brief}}.
- **Historias candidatas:** {{Una HU por capacidad coherente: nombre propuesto `NNN-HU_nombre`, marcada ⚠️ [PROPUESTO], con sus dependencias de otras épicas y los puntos abiertos ❓ que la bloquean}}.
- **Justificación de Prioridad:** {{Por qué esta épica constituye el núcleo indispensable del MVP}}.
- **Trazabilidad PRD:** {{Sección o requerimiento del Product Brief que la origina}}.

### [P2] Épica: {{Nombre de la Funcionalidad Dependiente / Catálogo}}
- **Descripción de Negocio:** {{Qué resuelve}}.
- **Incluye:** {{Lista de capacidades que abarca la épica, tomadas del Product Brief}}.
- **Historias candidatas:** {{Una HU por capacidad coherente: nombre propuesto `NNN-HU_nombre`, marcada ⚠️ [PROPUESTO], con sus dependencias de otras épicas y los puntos abiertos ❓ que la bloquean}}.
- **Justificación de Prioridad:** {{Por qué ocupa el segundo nivel de prelación}}.
- **Trazabilidad PRD:** {{Referencia al brief}}.

### [P3] Épica: {{Nombre de Autogestión o Siguiente Prioridad}}
- **Descripción de Negocio:** {{Qué resuelve}}.
- **Incluye:** {{Lista de capacidades que abarca la épica, tomadas del Product Brief}}.
- **Historias candidatas:** {{Una HU por capacidad coherente: nombre propuesto `NNN-HU_nombre`, marcada ⚠️ [PROPUESTO], con sus dependencias de otras épicas y los puntos abiertos ❓ que la bloquean}}.
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

## 4. CREACIÓN DE IDENTIFICADORES Y MAPA DE SPECS (DESCOMPOSICIÓN EN HISTORIAS)

Una épica agrupa **varias HU** y cada HU es la unidad que se delega al BA. En esta fase registras en el ledger **todas las historias candidatas de todas las épicas**, no solo la primera.

⚠️ **REGLA ESTRICTA DE NOMENCLATURA (IDENTIFICADOR SECUENCIAL):**
Lee obligatoriamente el archivo `specs/README.md` (Product State Ledger).
1. Analiza la columna "N°" de la tabla para encontrar el correlativo numérico más alto.
2. Cada HU recibe el siguiente correlativo, formateado con 3 dígitos (ej. si el último es `002`, el nuevo será `003`), concatenado con `HU_` y el nombre en snake_case: `XXX-HU_[nombre_en_snake_case]` (ej. `001-HU_tarjeta_identidad_digital`).
3. Si la tabla está vacía, inicia en `001`.

**Registro en el Ledger (con tu herramienta `update-specs-map`):**
1. Por cada épica, toma su campo "Historias candidatas" y registra **cada HU** como una fila nueva con estado `BACKLOG`: numeración consecutiva siguiendo el orden de prioridad de las épicas y, dentro de cada una, su orden lógico; *Épica Origen* con el formato `[Pn] Nombre de la épica`; *Qué aporta* tomado de tu plan con la marca `⚠️ [PROPUESTO]` y, si aplica, la dependencia o el punto abierto ❓ que la bloquea; *Rama* con `—`.
2. La **primera HU a trabajar** (la primera de la épica de mayor prioridad que no esté bloqueada por un punto abierto de negocio) pasa a `IN-PROGRESS`: su identificador es el `{{IDENTIFICADOR_ESTRICTO}}` con el que cierras el Stage-Gate de la sección 5.
3. Prohibido inventar historias fuera del alcance del Product Brief: cada HU debe desprenderse de una capacidad listada en la épica.

---

## 5. ORDEN DE APROBACIÓN (STAGE-GATE HITL)
*(Instrucción que se inyecta en tracker_bmad.md)*

⚠️ **REGLA CRÍTICA DE CIERRE:**
Al finalizar el Plan Estratégico y las Épicas, tienes estrictamente prohibido delegar el turno a otro agente. Tu única acción de cierre válida es escribir en el tracker:

```markdown
@HUMANO: El Plan Estratégico del MVP ha sido definido. La próxima épica a delegar es {{IDENTIFICADOR_ESTRICTO}}. Las historias de cada épica quedaron registradas en BACKLOG en el ledger (specs/README.md). Por favor, valida las Épicas y su descomposición en historias, y ejecuta el script de aprobación para autorizar la transición hacia el Business Analyst (@BA).
```


---

### ⚠️ Directiva para Ecosistemas Preexistentes (Modo Brownfield)
Si existe el archivo `.specify/memory/constitution.md`:
1. **Sección 2 (Backlog del MVP):** Al definir y justificar la prioridad de las Épicas (P1, P2, ...), categorizar el tipo de impacto respecto al legado (ej. "Extensión de componente existente", "Nueva capacidad desacoplada" o "Integración con Core preexistente").
2. **Sección 3 (Riesgos y Dependencias):** Identificar explícitamente los riesgos de regresión, acoplamiento operativo y compatibilidad con el sistema heredado documentado.
3. **Si el archivo NO existe (Modo Greenfield):** Estructura el Backlog del MVP estándar basado únicamente en el Product Brief.


[IMPORT_SKILL: skills/tracker-logger/SKILL.md]
