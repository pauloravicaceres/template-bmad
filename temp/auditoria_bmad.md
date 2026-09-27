# 🏛️ AUDITORÍA DE INTEGRIDAD ESTRUCTURAL — FRAMEWORK BMAD v2.0 (SDD)

> **Fecha:** 2026-09-27 | **Auditor:** BMAD Core Architect (Meta-Agente)  
> **Alcance:** Escaneo de Solo Lectura post-migración a Spec-Driven Development (Fase 2)  
> **Repositorio:** `template-bmad` | **Agentes Registrados:** 15 + 1 Meta-Agente  

---

## 1. RESUMEN EJECUTIVO

La arquitectura del framework BMAD ha sido sometida a un **Escaneo de Integridad Estructural** evaluando 5 pilares críticos tras la integración completa de **Spec-Driven Development (SDD)** vía GitHub Spec Kit.

### Veredicto Global

| Pilar | Descripción | Veredicto |
|:---:|:---|:---:|
| 1 | El Puente del Orquestador (Python & HITL) | ✅ Cumple |
| 2 | Gobernanza y Lex Superior | ⚠️ Advertencia |
| 3 | Discovery & Estrategia Dual-Output (Fase M) | ✅ Cumple |
| 4 | Transición de Arquitectura (Fase A) | ✅ Cumple |
| 5 | Delivery y Prevención de Bloqueos (Fase D) | ✅ Cumple |

> [!IMPORTANT]
> **Estado General: ECOSISTEMA OPERACIONAL CON BRECHA MENOR.**  
> El ecosistema está correctamente orquestado en sus 5 pilares funcionales. Se detectó **1 brecha documental no bloqueante** en el Pilar 2 (`AGENTS.md`) que no afecta la ejecución del enjambre pero sí la trazabilidad del catálogo de agentes.

---

## 2. RESULTADOS POR PILAR

---

### PILAR 1: El Puente del Orquestador (Python & HITL)

**Veredicto: ✅ CUMPLE**

#### 1.1 — SDD Gatekeeper en `watcher_bmad.py`
- **Archivo:** [`watcher_bmad.py`](file:///D:/Paulo/Cursos/DMC/template-bmad/watcher_bmad.py)
- **Evidencia (Líneas 171–201):** Existe la lógica de intercepción `SDD GATEKEEPER` que:
  - Detecta patrones de aprobación de QA Documental (`aprobado_qa_`, `aprobada por qa`).
  - Intercepta la transición hacia `@UX:` o `@SA:` cuando coincide con la aprobación.
  - **Detiene el flujo** devolviendo `return []` (cola vacía), impidiendo avance autónomo.
  - Imprime en consola la secuencia requerida de Spec Kit: `/speckit.specify → /clarify → /plan → /tasks → /analyze`.
  - Indica al operador usar `python utils/approve_step.py` para liberar la compuerta.

```python
# Líneas 184–201 — Intercepción determinista
if es_transicion_a_arquitectura and es_aprobacion_qa:
    print("🛑 [PAUSA SDD INTERCEPTADA] CERTIFICADO QA DOCUMENTAL REGISTRADO")
    # ... guía de Spec Kit ...
    return []  # ← Detención obligatoria
```

- **Salvaguarda anti-disparo accidental (Líneas 164–170):** Si el Handoff está dirigido a `@HUMANO:`, no despacha ningún agente, respetando el Principio 7.
- **Mapeo de 15 agentes (Líneas 139–159):** Diccionario completo con todas las etiquetas `@BS:`, `@PA:`, `@PM:`, `@BA:`, `@QA:`, `@UX:`, `@SA:`, `@DA:`, `@API:`, `@QT:`, `@DEV-BACK:`, `@DEV-FRONT:`, `@QA-AUTO:`, `@CODE-REVIEW:`, `@DEVOPS:` (con aliases `@DEV-BACKEND:`, `@DEV-FRONTEND:`, `@CR:`, `@DEV:`).
- **Despacho secuencial vía `herdr`:** Candado `candado_disparo` asegura un único agente por ciclo (token-passing).

#### 1.2 — Compuertas HITL en `utils/approve_step.py`
- **Archivo:** [`utils/approve_step.py`](file:///D:/Paulo/Cursos/DMC/template-bmad/utils/approve_step.py)
- **15 compuertas HITL parametrizadas** cubriendo todas las transiciones:

| # | Compuerta | Transición |
|:---:|:---|:---|
| 1 | BS → PA | Idea revisada → Product Brief |
| 2 | PA → PM | Product Brief aprobado → MVP Backlog |
| 3 | PM → BA | Backlog autorizado → Redacción HUs |
| 4 | BA → QA | HUs escritas → Auditoría QA Documental |
| 5 | Spec Kit → UX | Ciclo SDD completado → Diseño interfaces |
| 6 | Spec Kit → SA | Ciclo SDD (Headless) → Arquitectura directa |
| 7 | UX → PM | Wireframes validados → Siguiente Épica |
| 8 | UX → SA | MVP visual completo → Solutions Architect |
| 9 | SA → DA | Directrices aprobadas → Data Architect |
| 10 | QT → /speckit.implement | Tech Design aprobado → Gatillo Fase D |
| 11 | QT → DEV-BACK | Fallback directo Backend |
| 12 | QT → DEV-FRONT | Fallback directo Frontend |
| 13 | Devs → QA-AUTO | Código implementado → Suite de pruebas |
| 14 | QA-AUTO → CODE-REVIEW | Pruebas certificadas → Auditoría SecOps |
| 15 | CODE-REVIEW → DEVOPS | Veredicto aprobado → Despliegue |

- **Apertura automática de artefactos** en el SO para inspección humana antes de confirmar.
- **Confirmación interactiva exigida:** Solo con input `'s'` se inyecta la orden al `tracker_bmad.md`.

#### 1.3 — Topología en `config_bmad.json`
- **Archivo:** [`config_bmad.json`](file:///D:/Paulo/Cursos/DMC/template-bmad/config_bmad.json)
- Mapea los 15 agentes con sus rutas en `routes_bmad`.
- Vincula la constitución SDD: `"context": ".specify/memory/constitution.md"`.
- Vincula el bus de datos: `"tracker": "files/tracker_bmad.md"`.

---

### PILAR 2: Gobernanza y Lex Superior

**Veredicto: ⚠️ ADVERTENCIA (1 brecha documental menor)**

#### 2.1 — Constitución Técnica `.specify/memory/constitution.md`
- **Archivo:** [`.specify/memory/constitution.md`](file:///D:/Paulo/Cursos/DMC/template-bmad/.specify/memory/constitution.md)
- **Estado:** ✅ **CUMPLE**
- Existe como Lex Superior del ecosistema (54 líneas, ratificada 25-09-2026).
- Define invariantes técnicas inmutables:
  - **Principio I:** Zero External APIs + Pre-renderizado Total (SSG).
  - **Principio II:** Zero JavaScript by Default.
  - **Principio III:** Resiliencia y Degradación Elegante.
  - **Principio IV:** Estrategia Anti-FOUT Estricta.
- **Stack blindado:** Astro 4.x, Tailwind CSS 3.x, TypeScript 5.x, Zod 3.x, Node.js 20.x LTS, Vercel/GitHub Pages.
- **ADRs registrados:** 12 decisiones arquitectónicas inmutables (ADR-001 a ADR-012).
- **Cláusulas de Excepción:** ❌ **No existen** — deliberadamente. El blindaje es 100% estricto. Cualquier propuesta divergente es nula y debe ser rechazada por QA Tech con severidad 🔴 CRÍTICO.

> [!NOTE]
> La ausencia de cláusulas de excepción es **intencional** para este proyecto SSG, reforzando el blindaje anti-sycophancy del Principio 8 de AGENTS.md. No es una brecha.

#### 2.2 — Catálogo de Agentes `AGENTS.md`
- **Archivo:** [`AGENTS.md`](file:///D:/Paulo/Cursos/DMC/template-bmad/AGENTS.md)
- **Estado:** ⚠️ **ADVERTENCIA**

**Lo que SÍ cumple:**
- ✅ Contiene los **10 Principios Inmutables** del framework compilados y actualizados.
- ✅ Referencia explícita al **SDD Gatekeeper** y `/speckit.implement` (Principio 10).
- ✅ Define la **Topología Dinámica** completa: con UI, Headless y Paralela DevOps (Principio 3).
- ✅ Documenta Lex Superior, Anti-Sycophancy y Segregación Fase D (Principios 6, 8, 9).
- ✅ Referencia 13 de los 15 agentes operativos.

**Lo que NO cumple:**
- ❌ **No es un catálogo compilado de los 15 agentes.** Funciona como el prompt operativo del meta-agente `bmad-architect` (frontmatter YAML: `name: 'bmad-architect'`), no como un registro exhaustivo con fichas, herramientas y prompts de cada agente.
- ❌ **Omite 2 agentes de la Fase B** en la topología dinámica (Líneas 21–22):
  - `business-storyteller` (BS) — No aparece en la cadena.
  - `product-analyst` (PA) — No aparece en la cadena.
  - La topología inicia en `BA → QA → ...` omitiendo la secuencia previa `BS → PA → PM → BA`.

> [!WARNING]
> **Impacto:** Esta omisión es **puramente documental** y no afecta la ejecución real del enjambre (el `watcher_bmad.py` SÍ tiene las etiquetas `@BS:` y `@PA:` mapeadas, y `approve_step.py` SÍ tiene las compuertas 1 y 2 configuradas). Sin embargo, un agente LLM que consuma exclusivamente `AGENTS.md` como contexto podría ignorar la existencia de la Fase B de descubrimiento.

---

### PILAR 3: Discovery & Estrategia Dual-Output (Fase M)

**Veredicto: ✅ CUMPLE**

#### 3.1 — Perfil del Business Analyst
- **Archivo:** [`business-analyst/agents/business-analyst.agent.md`](file:///D:/Paulo/Cursos/DMC/template-bmad/business-analyst/agents/business-analyst.agent.md)
- Documenta formalmente la **Estrategia Dual-Output** desde la línea 2 del frontmatter.
- Genera obligatoriamente **dos entregables por HU:**
  1. **HU Técnica (Spec Kit Ready):** `files/business-analyst/hu_[ID]_[nombre].md`
  2. **HU Stakeholders (Negocio):** `files/business-analyst/HUs-stakeholders/hu_[ID]_[nombre].md`
- Variables parametrizadas: `CARPETA_SALIDA` y `CARPETA_SALIDA_STAKEHOLDERS`.
- Flujograma Mermaid con bifurcación dual (Líneas 85–88): nodos `I1` (Gherkin) e `I2` (Stakeholders) en paralelo.
- Acciones MCP (Líneas 107–108): `write_file` obligatorio para ambas salidas.
- Delegación posterior determinista a `@QA:`.

#### 3.2 — Template Gherkin Técnico
- **Archivo:** [`business-analyst/instructions/hu-template.instructions.md`](file:///D:/Paulo/Cursos/DMC/template-bmad/business-analyst/instructions/hu-template.instructions.md)
- ✅ Formato Gherkin puro (`Feature`, `Scenario`, `Given`, `When`, `Then`, `And`).
- ✅ Optimizado para consumo por `/speckit.specify`.
- ✅ Incluye metadatos formales, matriz de casos borde, pre/postcondiciones y DoD.
- ✅ Directiva Backend/Headless: enfoque en persistencia, códigos HTTP y validación de esquemas.

#### 3.3 — Template Stakeholders
- **Archivo:** [`business-analyst/instructions/hu-stakeholders-template.instructions.md`](file:///D:/Paulo/Cursos/DMC/template-bmad/business-analyst/instructions/hu-stakeholders-template.instructions.md)
- ✅ Formato narrativo en español (`Como/Quiero/Para` + `Dado/Cuando/Entonces`).
- ✅ Sin jerga técnica de bajo nivel.
- ✅ Secciones exclusivas de negocio: Impacto Operativo, ROI, KPIs.
- ✅ Estructuralmente diferenciado del template Gherkin (sin `Feature`, sin códigos HTTP, sin Spec Kit refs).

#### 3.4 — Directorio de Salida Stakeholders
- **Ruta:** `files/business-analyst/HUs-stakeholders/.gitkeep`
- ✅ **Existe físicamente.** Placeholder `.gitkeep` presente para control de versiones.

---

### PILAR 4: Transición de Arquitectura (Fase A)

**Veredicto: ✅ CUMPLE (5/5 agentes)**

| Agente | Artefactos Spec Kit en Input | Constitución / SDD Bridge | Veredicto |
|:---|:---|:---|:---:|
| `designer-ux` | `spec.md`, `tasks.md`, `/speckit.analyze` | Ref. `constitution.md`, `CARPETA_SPECS` | ✅ |
| `solutions-architect` | `plan.md`, `tasks.md`, `/speckit.plan` | ADRs subordinados a `constitution.md` | ✅ |
| `data-architect` | `spec.md`, `tasks.md` | MER vinculado a contratos SDD | ✅ |
| `api-architect` | `spec.md`, `tasks.md` | Endpoints y Sad Paths desde SDD | ✅ |
| `qa-tech` | `spec.md`, `tasks.md`, `plan.md` | Guardián Constitucional + Anti-Sycophancy + Gatillo `/speckit.implement` | ✅ |

**Evidencias clave por agente:**

- **`designer-ux`** — Línea 2: `"traduce los requerimientos validados por Spec Kit (spec.md, tasks.md y reporte de /speckit.analyze)"`. Boot Sequence: lectura de `spec.md` y `tasks.md` como paso D. Mapeo 1:1 de escenarios spec a wireframes ASCII.
- **`solutions-architect`** — Línea 2: `"formaliza los ADRs en formato MADR a partir de plan.md (Spec Kit), tasks.md y constitution.md"`. Valida y enriquece `plan.md`, no parte de cero.
- **`data-architect`** — Línea 2: `"diseña el MER subordinado a spec.md y tasks.md de Spec Kit"`. Modela persistencia alineada a entidades de la descomposición SDD.
- **`api-architect`** — Línea 2: `"mapea endpoints requeridos por spec.md y tasks.md basándose en el MER"`. Sad Paths del Gherkin mapeados a códigos HTTP.
- **`qa-tech`** — Línea 36: Anti-Sycophancy constitucional (`🔴 CRÍTICO` para stack divergente sin cláusula física). Líneas 58–59: Gatillo `/speckit.implement` al aprobar `tech-design_*.md`. Auditoría adversarial cruzando DB vs API vs UX vs Spec Kit.

---

### PILAR 5: Delivery y Prevención de Bloqueos Interactivos (Fase D)

**Veredicto: ✅ CUMPLE (9/9 puntos)**

#### 5.1 — Herramienta `execute_command` en YAML

| Agente | Línea | Tools | Veredicto |
|:---|:---:|:---|:---:|
| [`dev-backend.agent.md`](file:///D:/Paulo/Cursos/DMC/template-bmad/dev-backend/agents/dev-backend.agent.md) | 4 | `['filesystem/read_file', 'filesystem/write_file', 'list_dir', 'execute_command']` | ✅ |
| [`dev-frontend.agent.md`](file:///D:/Paulo/Cursos/DMC/template-bmad/dev-frontend/agents/dev-frontend.agent.md) | 4 | `['filesystem/read_file', 'filesystem/write_file', 'list_dir', 'execute_command']` | ✅ |
| [`qa-auto.agent.md`](file:///D:/Paulo/Cursos/DMC/template-bmad/qa-auto/agents/qa-auto.agent.md) | 4 | `['filesystem/read_file', 'filesystem/write_file', 'list_dir', 'execute_command']` | ✅ |
| [`devops.agent.md`](file:///D:/Paulo/Cursos/DMC/template-bmad/devops/agents/devops.agent.md) | 4 | `['filesystem/read_file', 'filesystem/write_file', 'filesystem/list_dir', 'execute_command']` | ✅ |

#### 5.2 — Directivas Headless (Non-Interactive Mode)

| Archivo | Scope | Flags Clave | Veredicto |
|:---|:---|:---|:---:|
| [`dev-backend/.../cli-headless-execution.instructions.md`](file:///D:/Paulo/Cursos/DMC/template-bmad/dev-backend/instructions/cli-headless-execution.instructions.md) | .NET CLI | `--no-restore`, `-n`, `-o`, `--no-build`, `-verbosity:quiet` | ✅ |
| [`dev-frontend/.../cli-headless-execution.instructions.md`](file:///D:/Paulo/Cursos/DMC/template-bmad/dev-frontend/instructions/cli-headless-execution.instructions.md) | Angular/npm | `--defaults`, `--skip-git`, `-y`, `--standalone` | ✅ |
| [`devops/.../cli-headless-execution.instructions.md`](file:///D:/Paulo/Cursos/DMC/template-bmad/devops/instructions/cli-headless-execution.instructions.md) | Docker/Terraform/Git | `-d`, `--quiet`, `-auto-approve`, `-input=false`, `-NonInteractive` | ✅ |
| [`qa-auto/.../cli-headless-execution.instructions.md`](file:///D:/Paulo/Cursos/DMC/template-bmad/qa-auto/instructions/cli-headless-execution.instructions.md) | Test Runners | `--ci`, `--forceExit`, `--no-interactive`, `--headed=false` | ✅ |

#### 5.3 — Segregación Constructores vs. Auditores

- **`code-review.agent.md`:** Rol exclusivo de auditoría (Senior Tech Lead & SecOps). **No tiene** `execute_command` en su toolset — solo lectura y escritura de archivos.
- **Gating formal:** Matriz de auditoría que rechaza entregas con violaciones constitucionales.
- **Veredicto binario:** Emite `[APROBADO]` o `[RECHAZADO]` cruzando contra `constitution.md`.
- **Garantía anti-autoaprobación:** Los agentes `dev-backend`, `dev-frontend` y `qa-auto` no tienen autoridad para cerrar HUs; solo `code-review` puede emitir el veredicto final.

---

## 3. HALLAZGOS Y BRECHAS (GAPS)

### 🔴 Brechas Críticas
**Ninguna detectada.**

### 🟡 Brechas Menores (No Bloqueantes)

#### GAP-001: `AGENTS.md` omite agentes de Fase B en topología

| Campo | Detalle |
|:---|:---|
| **Archivo** | [`AGENTS.md`](file:///D:/Paulo/Cursos/DMC/template-bmad/AGENTS.md) |
| **Ubicación** | Principio 3, Líneas 21–22 (Topología Dinámica) |
| **Descripción** | La cadena de agentes inicia en `BA → QA → ...` omitiendo la Fase B previa: `BS → PA → PM → BA`. Los agentes `business-storyteller` y `product-analyst` no aparecen mencionados en ninguna parte del archivo. |
| **Impacto** | **Puramente documental.** El motor Python (`watcher_bmad.py`, Líneas 140–141) y las compuertas HITL (`approve_step.py`, Opciones 1–2) SÍ reconocen a ambos agentes. Un LLM que consuma exclusivamente `AGENTS.md` como contexto podría ignorar la Fase B de descubrimiento. |
| **Severidad** | 🟡 Menor / Cosmético |

---

## 4. PLAN DE ACCIÓN SUGERIDO

### Para GAP-001 — Completar topología en `AGENTS.md`

Actualizar el **Principio 3 (Topología Dinámica)** en las líneas 20–22 del archivo `AGENTS.md`, anteponiendo la Fase B completa:

**Estado actual (Líneas 21–22):**
```
- Proyectos con UI: BA -> QA -> [SDD Gatekeeper: Spec Kit] -> UX -> SA -> ...
- Proyectos Headless: BA -> QA -> [SDD Gatekeeper: Spec Kit] -> SA -> DA -> ...
```

**Estado propuesto:**
```
- Proyectos con UI: BS -> PA -> PM -> BA -> QA -> [SDD Gatekeeper: Spec Kit] -> UX -> SA -> DA -> API -> QT -> /speckit.implement -> (DEV-BACK / DEV-FRONT) -> QA-AUTO -> CODE-REVIEW
- Proyectos Headless (ETL, SSIS, APIs): BS -> PA -> PM -> BA -> QA -> [SDD Gatekeeper: Spec Kit] -> SA -> DA -> QT -> /speckit.implement -> DEV-BACK -> QA-AUTO -> CODE-REVIEW
```

> [!TIP]
> Este cambio es de **una sola línea por ruta** y no modifica la lógica del framework. Solo completa la documentación para que cualquier agente LLM que consuma `AGENTS.md` tenga visibilidad completa de la Fase B.

---

## 5. DICTAMEN FINAL

```
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   DICTAMEN: ECOSISTEMA OPERACIONAL                               ║
║   CON CORRECCIÓN DOCUMENTAL MENOR PENDIENTE                     ║
║                                                                  ║
║   • 5/5 Pilares funcionales verificados                         ║
║   • 0 brechas críticas                                          ║
║   • 1 brecha documental menor (GAP-001)                         ║
║   • 15 agentes operativos con routing correcto                  ║
║   • 15 compuertas HITL configuradas                             ║
║   • SDD Gatekeeper activo y determinista                        ║
║   • Constitución blindada (Zero Exceptions)                     ║
║   • Fase D 100% Headless con segregación auditores/builders     ║
║                                                                  ║
║   Tras aplicar GAP-001 → ECOSISTEMA CERTIFICADO                 ║
║   Y LISTO PARA PRODUCCIÓN                                       ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

---

> **Firmado digitalmente por:** BMAD Core Architect (Meta-Agente `bmad-architect`)  
> **Método:** Escaneo de Integridad Estructural — Modo Solo Lectura  
> **Fecha de emisión:** 2026-09-27T06:21:00-05:00  
> **Versión del Framework:** BMAD v2.0 + SDD (Spec Kit Integration)
