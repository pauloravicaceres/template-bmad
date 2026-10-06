# Inputs por agente (BMAD)

Qué lee cada agente para generar su entregable, de dónde sale cada entrada y si es obligatoria.
Se derivó de `<agente>/agents/*.agent.md` (variables de entorno y tabla de acciones MCP) y de las `instructions/` de cada uno.

**Leyenda de la columna "Tipo"**

| Tipo | Significado |
|---|---|
| **Obligatoria** | La regla del agente exige leerla siempre. |
| **Condicional** | Solo se lee si se cumple la condición indicada. |
| **Bloqueante si falta** | Es obligatoria y el agente se detiene si no puede leerla (protocolo de seguridad). |

**Entradas comunes a casi todos los agentes** (no se repiten en cada tabla salvo que cambien):

| Entrada | Para qué | Tipo | Fuente |
|---|---|---|---|
| `config_bmad.json` (`RUTA_CONFIGURACION`) | Resolver las rutas de lectura y escritura (`routes_bmad`) y la ruta del tracker | Obligatoria (paso 1 de todos los agentes del pipeline BMAD) | Variable `RUTA_CONFIGURACION` |
| `tracker_bmad.md` | Recibir la instrucción `@TAG:` y registrar el handoff al terminar | Obligatoria (lectura previa a escribir; el handoff se anexa, nunca se sobrescribe) | Variable `TRACKER` + skill `tracker-logger` |
| `.specify/memory/constitution.md` | Modo Brownfield: subordinar el trabajo al ecosistema existente | Condicional: solo si el archivo existe (si no, modo Greenfield) | Variable `CARPETA_CONTEXTO` |
| `AGENTS.md` del agente | Alma del agente: se ensambla desde `agents/` + `instructions/` + skills | Automática | Ensamblado del framework |

> Los agentes de desarrollo (DEV-BACK, DEV-FRONT) no son paneles: el Watcher los ejecuta con Spec Kit y les monta su `AGENTS.md` como directiva.

---

## 1. Business Storyteller (`@BS:`)

| Entrada | Para qué | Tipo | Fuente |
|---|---|---|---|
| Idea cruda del stakeholder (chat) | Materia prima de la narrativa | Obligatoria | `argument-hint` del agente |
| Respuestas a las 3–4 preguntas de descubrimiento | Completar una idea vaga | Condicional: solo si la idea es ambigua o muy breve (< 3 líneas) | Algoritmo operativo |
| `config_bmad.json` | Rutas | Obligatoria (solo cuando la idea ya está madura; en la fase de preguntas el uso de MCP está prohibido) | Tabla MCP paso 1 |
| `.specify/memory/constitution.md` | Alinear la narrativa al dominio existente | Condicional (Brownfield) | `CARPETA_CONTEXTO` |
| `instructions/bs-narrative-optimization`, `idea-template`, `anti-hallucination-policy` | Las 4 transformaciones, formato del archivo y reglas de no invención | Obligatoria | `instructions/` |

Entregable: `idea_[Nombre_Corto].md` → handoff `@PA:`.

## 2. Product Analyst (`@PA:`)

| Entrada | Para qué | Tipo | Fuente |
|---|---|---|---|
| `idea_*.md` | Única fuente del Product Brief | Bloqueante si falta (no se permite inventar la idea) | `CARPETA_ENTRADA` = `business-storyteller` |
| `config_bmad.json` | Rutas | Obligatoria | Paso 1 |
| `.specify/memory/constitution.md` | Delimitar alcance (§4) y restricciones duras (§5) | Condicional (Brownfield) | `CARPETA_CONTEXTO` |
| `instructions/pb-template`, `anti-hallucination-policy` | 8 secciones canónicas y etiquetas de incertidumbre | Obligatoria | `instructions/` |

Entregable: `pb_[Nombre_Corto].md` → handoff `@HUMANO:` (pausa HITL; el PM solo despierta con `approve_step.py`).

## 3. Product Manager (`@PM:`)

| Entrada | Para qué | Tipo | Fuente |
|---|---|---|---|
| `pb_*.md` (Product Brief) | Fuente de la verdad de épicas y alcance | Obligatoria | `CARPETA_ENTRADA` = `product-analyst` |
| `specs/README.md` (ledger) | Siguiente correlativo, estados de las HU, backlog | Obligatoria (lectura y escritura con `update-specs-map`) | Contexto y misión del agente |
| `mvp_*.md` (su propio plan) | Elegir la siguiente HU al cierre de una HU | Obligatoria en ciclos de iteración (tras el cierre de code-review) | `pm-strategic-prioritization` §3.2 |
| `.specify/memory/constitution.md` | Categorizar el impacto respecto al legado | Condicional (Brownfield) | `CARPETA_CONTEXTO` |
| `instructions/mvp-template`, `pm-strategic-prioritization`, `ledger-cierre-hu`, `anti-hallucination-policy` | Estructura del plan, heurística de selección, mantenimiento del ledger | Obligatoria | `instructions/` |

Entregables: `mvp_[nombre_corto].md`, filas del ledger y macro `GITOPS-BRANCH-CREATE` + handoff `@BA:` (o `@HUMANO:` si hay dos opciones razonables).

## 4. Business Analyst (`@BA:`)

| Entrada | Para qué | Tipo | Fuente |
|---|---|---|---|
| `pb_*.md` | Fuente de requisitos de negocio | Obligatoria | `CARPETA_ENTRADA_PB` |
| `mvp_*.md` | Plan de gestión: épica y alcance de la HU | Obligatoria | `CARPETA_ENTRADA_MVP` |
| `specs/README.md` | No duplicar ni romper specs `ACTIVE` | Obligatoria (lectura previa a redactar) | Ingestión del mapa de specs |
| Identificador `NNN-HU_nombre` del handoff | Nombre exacto del archivo (prohibido alterarlo) | Obligatoria | Regla del identificador universal |
| `feedback_qa_*.md` | Subsanar un rechazo | Condicional: solo si el turno viene de `@QA:` con rechazo | `CARPETA_ENTRADA_QA` |
| `.specify/memory/constitution.md` | Escenarios y DoD de no regresión | Condicional (Brownfield) | `CARPETA_CONTEXTO` |
| `instructions/hu-template`, `hu-stakeholders-template`, `business-analysis-standards`, `anti-hallucination-policy` | Plantilla técnica (incluye `Requiere interfaz: Sí\|No`), plantilla para stakeholders, INVEST | Obligatoria | `instructions/` |

Entregables: `documents/business-analyst/NNN-HU_nombre.md` y `.../HUs-stakeholders/NNN-HU_nombre.md` → handoff `@QA:`.

## 5. QA Documental (`@QA:`)

| Entrada | Para qué | Tipo | Fuente |
|---|---|---|---|
| `pb_*.md` | Única fuente de la verdad para auditar | Bloqueante si falta | `CARPETA_ENTRADA_PB` |
| `NNN-HU_*.md` (HU técnica del BA) | Documento auditado | Bloqueante si falta | `CARPETA_ENTRADA_HU` |
| `.specify/memory/constitution.md` | Auditoría en doble vía y ítem de no regresión en el DoD | Condicional (Brownfield) | `CARPETA_CONTEXTO` |
| `instructions/qa-validation-standards`, `qa-report-template`, `anti-hallucination-policy` | Rúbrica de 5 dimensiones (+1 Brownfield) y formato del dictamen | Obligatoria | `instructions/` |

Entregable: `aprobado_qa_*.md` o `feedback_qa_*.md`. El token de salida (`@UX:`/`@SA:`) es informativo: **la ruta real la decide el Watcher** con `ux_routing.py` (`project_type`, `ux_phase` y el campo `Requiere interfaz` de la HU). El QA solo verifica que la HU declare ese campo.

## 6. Designer UX (`@UX:`)

Solo interviene si el Watcher decide la ruta `@UX:` (ver `SETUP.md`: `project_type`, `ux_phase`, `Requiere interfaz`).

| Entrada | Para qué | Tipo | Fuente |
|---|---|---|---|
| `config_bmad.json` | Rutas (`CARPETA_ENTRADA_HU`, `CARPETA_SPECS`, `CARPETA_SALIDA`) | Obligatoria | Tabla MCP paso 1 |
| `.specify/feature.json` | Saber cuál es la carpeta de la HU en curso | Obligatoria | Tabla MCP paso 2 |
| `specs/NNN-HU_nombre/spec.md` | Fuente primaria de la especificación | Bloqueante si falta | `CARPETA_SPECS` |
| `specs/NNN-HU_nombre/checklists/requirements.md` | Requisitos verificables | Obligatoria | `CARPETA_SPECS` |
| `documents/business-analyst/NNN-HU_*.md` | Historia técnica (campo `Requiere interfaz`) | Obligatoria | `CARPETA_ENTRADA_HU` |
| `tracker_bmad.md` | Instrucción recibida y registro del handoff al `@SA:` | Obligatoria | `TRACKER` |
| `instructions/ux-design-standards`, `ux-deliverable-template`, `anti-hallucination-policy` | Reglas de diseño y formato del entregable | Obligatoria | `instructions/` |

Entregable: `ux_NNN_nombre.md` → handoff incondicional `@SA:` (no depende de cuántas épicas falten).

## 7. Solutions Architect (`@SA:`)

| Entrada | Para qué | Tipo | Fuente |
|---|---|---|---|
| `tracker_bmad.md` | Instrucción recibida y respuesta del humano al cuestionario | Obligatoria | Paso 2 |
| `spec.md` y `requirements.md` de Spec Kit | Input primario de la especificación validada | Obligatoria | Subordinación a Spec Kit |
| `ux_*.md` | Wireframes que condicionan la arquitectura | Condicional: solo si hubo diseño UX | Subordinación a Spec Kit |
| `.specify/memory/constitution.md` | Lex superior: stack e infraestructura heredados | Obligatoria si existe (gobierna sobre el tracker) | `CARPETA_CONTEXTO` |
| `specs/README.md` | Alinear con la topología documentada y evitar solapar con specs `DEPRECATED` | Obligatoria | Ingestión del mapa de specs |
| `pb_*.md` y `mvp_*.md` | Contexto de negocio y dimensionamiento | Condicional: "si se requiere" | Paso 3 |
| Respuestas del `@HUMANO:` (`utils/response_sa.py`) | Completar vacíos arquitectónicos | Condicional: solo si el SA formuló cuestionario | Fase de descubrimiento |
| `instructions/guidelines-template` | Estructura de los 12 puntos y ADR MADR | Obligatoria | `instructions/` |

Entregable: `tech_guidelines.md` → macro `@WATCHER: SDD-FREEZE [HU]` (prohibido invocar `@DA:` directamente) o `@HUMANO:` si faltan datos.

## 8. Data Architect (`@DA:`)

| Entrada | Para qué | Tipo | Fuente |
|---|---|---|---|
| `spec.md` y `tasks.md` congelados por el Watcher | Contratos de datos y tareas de persistencia | Obligatoria (input primario) | Subordinación a Spec Kit |
| `NNN-HU_*.md` | Historia técnica | Obligatoria | `CARPETA_ENTRADA_HU` |
| `tech_guidelines.md` | Stack y motor de persistencia | Obligatoria en Greenfield | Regla Greenfield del agente |
| `ux_*.md` | Auditar campos huérfanos UI → Data | Condicional: solo si existe diseño visual (en Headless se omite) | `CARPETA_ENTRADA_UX` |
| `.specify/memory/constitution.md` | Motor, dialecto y entidades heredados | Condicional (Brownfield) | `CARPETA_CONTEXTO` |
| `instructions/db-template` | Estructura del MER y ADR | Obligatoria | `instructions/` |

Entregable: `db_[nombre_corto].md` → handoff `@API:` (o `@QT:` si es ETL sin endpoints).

## 9. API Architect (`@API:`)

| Entrada | Para qué | Tipo | Fuente |
|---|---|---|---|
| `spec.md` y `tasks.md` | Requisitos de integración y tareas de contratos | Obligatoria | Subordinación a Spec Kit |
| `NNN-HU_*.md` | Historia técnica | Obligatoria | `CARPETA_ENTRADA_HU` |
| `db_*.md` | Entidades y columnas: base estricta de los payloads | Obligatoria | `CARPETA_ENTRADA_DB` |
| `.specify/memory/constitution.md` | Protocolos y topología de red heredados | Condicional (Brownfield) | `CARPETA_CONTEXTO` |
| `instructions/api-template` | Estructura del contrato y ADR | Obligatoria | `instructions/` |

Entregable: `api_[nombre_corto].md` → handoff `@QT:`.

## 10. QA Tech (`@QT:`)

| Entrada | Para qué | Tipo | Fuente |
|---|---|---|---|
| `tech_guidelines.md` | Auditar gobernanza y ADR del SA | Obligatoria | `CARPETA_ENTRADA_SA` |
| `db_*.md` | Auditoría cruzada DB vs API vs Spec Kit | Obligatoria | `CARPETA_ENTRADA_DB` |
| `api_*.md` | Idem | Obligatoria | `CARPETA_ENTRADA_API` |
| `spec.md` y `tasks.md` | Cobertura de entidades y endpoints | Obligatoria | `CARPETA_SPECS` |
| `ux_*.md` | Cruce UI → Data (cero campos huérfanos) | Condicional: solo si existe (Headless lo omite) | `CARPETA_ENTRADA_UX` |
| `.specify/memory/constitution.md` | Lex superior y detección de complacencia (sycophancy) | Obligatoria si existe; si el QT aprueba, también la **escribe/actualiza** | `CARPETA_CONTEXTO` |
| `specs/README.md` | Pasar la spec a `READY-FOR-DEV` | Obligatoria al aprobar (escritura con `update-specs-map`) | Modo escritura |
| `instructions/tech-design-template`, `qa-tech-feedback`, `constitution-template` | Formato del TDD, del rechazo y de la constitución | Obligatoria | `instructions/` |

Entregable: `tech-design_*.md` (aprobado) o `feedback_tech_*.md` (rechazo al causante `@DA:`/`@API:`/`@SA:`). Si aprueba, despacha `@DEV-BACK:` y/o `@DEV-FRONT:` según el alcance.

---

## Fase de implementación (Watcher + Spec Kit)

DEV-BACK y DEV-FRONT no son paneles: el Watcher los ejecuta de forma headless con `claude -p … "/speckit-<skill> …"`, apuntando explícitamente a la carpeta de la HU con `SPECIFY_FEATURE_DIRECTORY` y verificando `.specify/feature.json`.

| Paso del Watcher | Entrada | Para qué | Tipo |
|---|---|---|---|
| Fase de negocio (`specify` + `clarify`) | `documents/business-analyst/NNN-HU_*.md` (ruta extraída del mensaje de aprobación QA) | Generar `spec.md` de la HU | Obligatoria (sin ruta, se detiene) |
| Fase de negocio | Respuesta humana a la ambigüedad | Resolver `clarify` | Condicional: solo si Spec Kit detecta ambigüedad |
| `SDD-FREEZE` (plan, tasks, analyze) | `tech_guidelines.md` + `spec.md` + constitución | Congelar la arquitectura y generar `plan.md`/`tasks.md` | Obligatoria |
| Fase de implementación | Mensaje `@DEV-BACK:`/`@DEV-FRONT:` con "arquitectura" | Disparar `implement` con alcance (backend/frontend) | Obligatoria |
| Fase de implementación | `dev-backend/AGENTS.md` o `dev-frontend/AGENTS.md` montado en `.specify/memory/active_agent_directive.md` | Directiva del agente (alma) | Automática |
| Fase de implementación | `README.md` de la capa (`app/backend`, `app/frontend`, `code_dirs`) | Documentación viva obligatoria y verificada | Obligatoria |
| Retrabajo (rechazo de code-review o QA-AUTO) | Bloque de rechazo con etiquetas `[CAPA:SPEC/PLAN/TASKS/CODE]` | `analyze` → `converge` → `implement` acotado | Condicional: solo tras un rechazo (máximo 2 iteraciones por rama) |

### 11. DEV-BACK (`@DEV-BACK:`)

| Entrada | Para qué | Tipo | Fuente |
|---|---|---|---|
| `tech-design_*.md` | Único insumo de diseño (contratos copiados byte a byte) | Obligatoria | Algoritmo de ejecución |
| `.specify/memory/constitution.md` | Reglas inmutables (VSA, PostgreSQL, Carter, Mapster…) | Obligatoria | Misión |
| `Shared/Contracts` (código existente) | Clases base antes de programar | Obligatoria | Algoritmo paso 2 |
| `tasks.md`, `plan.md`, `spec.md` de la HU | Tareas a implementar (vía Spec Kit) | Obligatoria | Pipeline Spec Kit |
| `templates/backend-architecture-template.md` | Estructura de `documents/dev-backend/backend-architecture.md` | Obligatoria al terminar la HU | Regla de arquitectura viva |
| `README.md` de la capa | Actualizar si hubo cambios significativos | Condicional (gatillo de actualización) | Regla de documentación viva |
| `instructions/zero-hallucination-policy` | Cero placeholders, mocks ni librerías fantasma | Obligatoria | `instructions/` |

### 12. DEV-FRONT (`@DEV-FRONT:`)

| Entrada | Para qué | Tipo | Fuente |
|---|---|---|---|
| `tech-design_*.md` | Contratos API para tipar los modelos TypeScript | Obligatoria | Algoritmo de ejecución |
| `ux_*.md` (wireframes) | Esqueleto visual a calcar | Condicional: solo si hubo diseño UX | Algoritmo paso 1 |
| `.specify/memory/constitution.md` | Directivas visuales (Skeleton vs Theme) | Obligatoria | Misión |
| `tasks.md`, `plan.md`, `spec.md` de la HU | Tareas a implementar (vía Spec Kit) | Obligatoria | Pipeline Spec Kit |
| `templates/frontend-architecture-template.md` | Estructura de `documents/dev-frontend/frontend-architecture.md` | Obligatoria al terminar la HU | Regla de arquitectura viva |
| `README.md` de la capa | Actualizar si hubo cambios significativos | Condicional | Regla de documentación viva |
| `instructions/zero-hallucination-policy` | Sin `any`, sin legacy Angular, sin CSS de maquetación | Obligatoria | `instructions/` |

---

## Fase de certificación

## 13. QA Automation (`@QA-AUTO:`)

| Entrada | Para qué | Tipo | Fuente |
|---|---|---|---|
| Historial reciente de `tracker_bmad.md` | **Barrera Fork-Join**: esperar a los dos DEV si se despachó a ambos | Obligatoria; si falta uno, responde `@HUMANO:` esperando | Algoritmo paso 1 |
| Historia de Usuario (`hu_*.md` según el agente; hoy `NNN-HU_*.md`) | Criterios de aceptación a cubrir | Obligatoria | Algoritmo paso 2 |
| Código generado por los DEV | Objeto de las pruebas | Obligatoria | Algoritmo paso 2 |
| `qa-report.md` existente | Actualización con renderizado selectivo (solo la HU actual) | Obligatoria antes de dictaminar | Regla de calidad viva |
| `instructions/qa-strict-testing`, `qa-report-template`, `cli-headless-execution`, `rework-layer-labeling` | Rigor de pruebas, plantilla del reporte, CLI sin interactividad, etiquetas `[CAPA:*]` en rechazos | Obligatoria | `instructions/` |

## 14. Code Review (`@CODE-REVIEW:`)

| Entrada | Para qué | Tipo | Fuente |
|---|---|---|---|
| Todos los archivos generados durante el ciclo de la HU (`.cs`, `.ts`, `.html`, `.spec.ts`) | Lectura física obligatoria, sin aprobar por el resumen del DEV | Obligatoria (skill `code-review-gatekeeper`) | Algoritmo paso 1 |
| `.specify/memory/constitution.md` | Árbitro de las violaciones | Obligatoria | Algoritmo paso 2 |
| Pruebas del QA-AUTO | Detectar pruebas tautológicas | Obligatoria | Gatekeeper §3 |
| `documents/code-review/impact-analysis-report.md` | Actualización con renderizado selectivo | Obligatoria antes de aprobar o emitir el cierre | Regla de impacto |
| `specs/README.md` y `documents/product-manager/mvp_*.md` | Decidir si entrega el turno al `@PM:` (épicas con alcance pendiente) | Obligatoria al aprobar | `rework-layer-labeling` regla 9 |
| `instructions/secops-strict-audit`, `code-review-template`, `rework-layer-labeling` | Auditoría SecOps/rendimiento, formato del reporte, etiquetas de capa | Obligatoria | `instructions/` |

Si aprueba: macro de cierre de rama (como línea propia) + handoff `@PM:`. Si rechaza: hallazgos etiquetados `[CAPA:*]` al agente responsable.

## 15. DevOps (`@DEVOPS:`)

| Entrada | Para qué | Tipo | Fuente |
|---|---|---|---|
| `tech-design_*.md` | Infraestructura que debe aprovisionar | Obligatoria (o la instrucción del tracker) | Algoritmo paso 1 |
| `docker-compose.yml`, `Dockerfile`, `.env`/`.env.example`, pipelines | Archivos que modifica | Condicional: los que existan | Algoritmo paso 2 |
| `devops-architecture.md` | Actualización viva con renderizado selectivo | Obligatoria si cambia pipeline, contenedores, IaC o red | Regla de infraestructura viva |
| `instructions/devops-strict-infra`, `cli-headless-execution`, `devops-architecture-template` | Rootless, healthchecks, secretos, CLI headless | Obligatoria | `instructions/` |

---

## Puntos a revisar que salieron de esta extracción

Son inconsistencias entre los archivos de los agentes. Ninguna se corrigió en este documento; solo se registran.

| # | Hallazgo | Dónde |
|---|---|---|
| 1 | El SA, el DA, el API Architect y el QT declaran en `CARPETA_SPECS` un texto con codificación corrupta (`â€”`, `raÃ­z`). El SA además cita `requirements.md` en lugar de `checklists/requirements.md`. | `.agent.md` de `solutions-architect`, `data-architect`, `api-architect`, `qa-tech` |
| 2 | DA, API, QA-AUTO y QA Documental siguen nombrando `hu_*.md`; el estándar actual es `NNN-HU_nombre.md`. | `.agent.md` y `qa-report-template` de `qa-documental` (ejemplos `hu_01_…`) |
| 3 | La plantilla del QA Documental ya aclara que su token `@UX:`/`@SA:` es informativo, pero sus opciones siguen redactadas por headless/UI. La ruta real la decide el Watcher con `ux_routing.py` (`project_type`, `ux_phase`, `Requiere interfaz`). | `qa-documental` (`qa-report-template`) |
| 4 | La plantilla `tech-design-template` §8 del QT ordena cerrar la rama y gatillar `@SPEC-KIT:`, pero el agente `qa-tech` lo prohíbe y despacha a `@DEV-*`. | `qa-tech` |
| 5 | Las reglas de `README.md` de DEV-BACK y DEV-FRONT usan ejemplos de `venv`/`uvicorn`/Nuxt, que no corresponden al stack .NET/Angular del proyecto. | `dev-backend`, `dev-frontend` |
