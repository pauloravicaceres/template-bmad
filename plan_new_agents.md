# 📋 Plan de Implementación: Integración de la Fase D (Development & Delivery) en el Ecosistema BMAD

> **Documento:** `plan_new_agents.md`  
> **Rol:** Ingeniero Principal de Plataforma y Arquitecto del Framework BMAD (CTO)  
> **Fecha:** 26-09-2026  
> **Estado:** 🟡 Pendiente de Aprobación por el Humano  
> **Alcance:** Integración y soporte operativo para `dev-backend`, `dev-frontend`, `qa-auto`, `code-review` y `devops`.

---

## 1. 🔍 Resumen Ejecutivo de Hallazgos y Diagnóstico de Reconocimiento

Tras la auditoría forense de los archivos de identidad (`*.agent.md`), directivas de política (`.instructions.md`) y habilidades (`SKILL.md`) de los 5 nuevos agentes de la Fase D, se determinaron los siguientes hallazgos funcionales, arquitectónicos y estructurales:

### 1.1 Roster Especializado de la Fase D: Constructores vs. Auditores

| Agente | Nombre | Clasificación | Misión y Rol Técnico | Stack / Herramientas Clave |
|---|---|:---:|---|---|
| **`dev-backend`** | Senior Backend Developer | 🏗️ Constructor | Transforma el `tech-design_*.md` en código fuente de producción siguiendo Vertical Slice Architecture (VSA). | .NET 8/10 Modulith, C# 12 moderno, Carter Minimal APIs, MediatR, FluentValidation, Mapster, PostgreSQL (Fluent API), Shared Interceptors, Redis (Scrutor decorator), Outbox con MassTransit/RabbitMQ. |
| **`dev-frontend`** | Senior Frontend Developer | 🏗️ Constructor | Construye interfaces reactivas zoneless consumiendo las APIs y replicando el esqueleto UI/UX. | Angular 22 Zoneless, Signals (`signal`, `computed`, `effect`, `toSignal`), Standalone Components, Modern Control Flow (`@if`, `@for`), inyección funcional (`inject()`), Reactive Forms tipados, PrimeNG v22.1.1. |
| **`qa-auto`** | Senior QA Automation Engineer | 🔬 Auditor | Destructor de código; diseña y ejecuta baterías de pruebas automáticas para certificar los Criterios de Aceptación de las HUs. | xUnit, NSubstitute, FluentAssertions, `WebApplicationFactory`, Testcontainers con PostgreSQL efímero (`IAsyncLifetime`), Jest para Angular Zoneless, Zero-Tautology Policy. |
| **`code-review`** | Senior Tech Lead & SecOps | 🔬 Auditor | Puerta de calidad (Quality Gate) final antes del cierre de HU. Audita físicamente el código para blindar contra fugas y fallos de seguridad. | Verificación física anti-rubber-stamping, detección de fugas (CancellationToken omitido, N+1 queries), prevención OWASP (IDOR, Mass Assignment, XSS), validación de VSA y pureza de schemas. |
| **`devops`** | Cloud, Infra & SRE | ⚙️ Plataforma | Dueño de la topología física, Dockerfiles, orquestación de compose y pipelines CI/CD. | Multi-stage builds, contenedores rootless (`USER appuser`), dependencias por `condition: service_healthy`, interpolación obligatoria de secretos (.env), GitHub Actions. |

---

### 1.2 Hallazgos Críticos de Plataforma y FileSystem

1. **Discrepancia de Nomenclatura en Carpetas de Skills (`skill/` vs `skills/`):**
   - `dev-backend` posee su habilidad en `dev-backend/skill/vsa-validator/SKILL.md` (singular `skill`).
   - `qa-auto` posee su habilidad en `qa-auto/skill/qa-strict-testing/SKILL.md` (singular `skill`).
   - Sin embargo, las etiquetas de importación dentro de los agentes usan la convención corporativa plural: `[IMPORT_SKILL: skills/vsa-validator/SKILL.md]` y `[IMPORT_SKILL: skills/qa-strict-testing/SKILL.md]`.
   - **Riesgo:** Si el motor compilador busca `skills/`, no encontrará los archivos y generará un error de ensamblaje en `AGENTS.md`.
   - **Solución Propuesta:** Normalizar físicamente las carpetas renombrándolas a `skills/` en `dev-backend` y `qa-auto`.

2. **Ausencia de Carpeta `instructions/` en `qa-auto` y Skill Embebido en Agent File:**
   - A diferencia del resto de los agentes modulares, `qa-auto` no tiene una subcarpeta `instructions/`; la etiqueta `[IMPORT_SKILL: skills/qa-strict-testing/SKILL.md]` se ubicó al final de su archivo de identidad `qa-auto/agents/qa-auto.agent.md`.
   - El compilador actual en `watcher_bmad.py` contiene la condición `if agent_file.exists() and instrucciones_dir.exists():`, por lo que **`qa-auto` era ignorado y no se compilaba**. Además, el regex de skills solo buscaba dentro de `*.instructions.md`.
   - **Solución Propuesta:** Flexibilizar el compilador para que procese e inyecte skills tanto en `agent_file` como en las instrucciones, y que genere el `AGENTS.md` aun si el agente no cuenta con archivos de instrucciones adicionales. Adicionalmente, crearemos formalmente `qa-auto/instructions/qa-strict-testing.instructions.md` para estandarizar la arquitectura modular de carpetas.

3. **Ausencia del Skill Universal `tracker-logger` en los 5 Nuevos Agentes:**
   - Ninguno de los 5 agentes tiene actualmente la directiva `[IMPORT_SKILL: skills/tracker-logger/SKILL.md]`.
   - **Riesgo:** Sin este skill, los agentes desconocen el estándar de bitácora determinista (`### [DD-MM-YYYY] {Agente}`, `- **Hora:**`, `- **Artefacto generado:**`, `- **Estado:**`, `- **Handoff:**`), lo que provocaría que escriban texto libre e invaliden el parser del orquestador.
   - **Solución Propuesta:** Inyectar el import de `skills/tracker-logger/SKILL.md` en los archivos de instrucciones de los 5 agentes.

4. **Etiquetas de Handoff Formales y Lógica de Enrutamiento:**
   - La secuencia en la Fase D se define como:
     ```text
     @QT: (Tech Design Aprobado)
        │
        ├──> @DEV-BACK: (Implementa Backend Slices) ──┐
        │                                             ├──> @QA-AUTO: ──> @CODE-REVIEW:
        └──> @DEV-FRONT: (Implementa Frontend UI) ───┘                        │
                                                                               ▼
                                                                     [APROBADO] / [RECHAZADO]
                                                                     (Hacia DEV correspondiente)
     
     * @DEVOPS: (Invocable en paralelo para infraestructura, Docker y CI/CD)
     ```
   - Mapeo de tokens deterministas para el parser:
     - `@DEV-BACK:` y `@DEV-BACKEND:` ➔ `dev-backend`
     - `@DEV-FRONT:` y `@DEV-FRONTEND:` ➔ `dev-frontend`
     - `@QA-AUTO:` ➔ `qa-auto`
     - `@CODE-REVIEW:` y `@CR:` ➔ `code-review`
     - `@DEVOPS:` ➔ `devops`

---

## 2. 🐍 Modificaciones Detalladas en Archivos Python (`.py`)

A continuación se detalla la intervención quirúrgica en cada uno de los scripts de la plataforma:

### 2.1 `watcher_bmad.py` (Orquestador Central y Compilador)

| Sección / Líneas | Cambio Requerido | Lógica y Justificación |
|---|---|---|
| **Líneas 21-24 (`compilar_agentes_modulares`)** | Ampliar la lista `agentes_modulares` de 10 a 15 agentes: añadir `"dev-backend"`, `"dev-frontend"`, `"qa-auto"`, `"code-review"`, `"devops"`. | Permite al watcher ensamblar automáticamente los 15 archivos `AGENTS.md` de la flota completa. |
| **Líneas 29-50 (`inyectar_skill`)** | Ampliar la búsqueda local: si `ruta_relativa` contiene `skills/` pero la carpeta física local se llama `skill/` (o viceversa), verificar ambas alternativas antes de fallar. | Resiliencia de compilación ante discrepancias de pluralización en carpetas locales. |
| **Líneas 57-78 (Ensamblaje)** | Cambiar condición `if agent_file.exists():`. Procesar `re.sub` de skills directamente sobre el contenido de `agent_file` antes de concatenar instrucciones. Si `instrucciones_dir` existe, concatenar cada archivo de instrucción procesando también sus skills. | Garantiza que agentes sin subcarpeta `instructions/` o con skills embebidos en el `.agent.md` (como `qa-auto`) se compilen perfectamente. |
| **Líneas 113-124 (`extraer_instrucciones`)** | Expandir el diccionario `agentes`: agregar `@DEV-BACK:`, `@DEV-BACKEND:`, `@DEV-FRONT:`, `@DEV-FRONTEND:`, `@QA-AUTO:`, `@CODE-REVIEW:`, `@CR:`, `@DEVOPS:`, y mantener `@DEV:` (alias histórico que deriva a `dev-backend`). | Enrutamiento determinista de los nuevos tokens hacia los paneles de Herdr correspondientes. |
| **Líneas 130-135 (Salvaguarda `@HUMANO:`)** | Al expandir `agentes`, la lista `todas_las_etiquetas` absorbe automáticamente los nuevos tokens, blindando el handoff humano frente a disparos accidentales de los agentes de Fase D. | Mantiene inviolable el Principio Inmutable 7 de aislamiento de handoffs humanos. |

### 2.2 `init_bmad.py` (Scaffolding e Inicialización de Proyectos)

| Sección / Líneas | Cambio Requerido | Lógica y Justificación |
|---|---|---|
| **Líneas 14-25 (`carpetas_agentes`)** | Incorporar los 5 agentes de Fase D a la lista: `"dev-backend"`, `"dev-frontend"`, `"qa-auto"`, `"code-review"`, `"devops"`. | Al ejecutar `python init_bmad.py`, se crean las carpetas `files/dev-backend/`, `files/dev-frontend/`, etc., y se indexan en el `config_bmad.json`. |

### 2.3 `utils/start_agents.py` (Despliegue de Paneles en Herdr y FinOps)

| Sección / Líneas | Cambio Requerido | Lógica y Justificación |
|---|---|---|
| **Líneas 13-27 (`AGENTS_CONFIG`)** | Reestructurar la grilla de terminales pasando de 2x5 (10 agentes) a una grilla de **3 Filas x 5 Columnas (15 agentes)**.<br>- **Fila 1 (Negocio y Producto):** `business-storyteller`, `product-manager`, `business-analyst`, `qa-documental`, `designer-ux`<br>- **Fila 2 (Arquitectura e Ingeniería A):** `product-analyst`, `solutions-architect`, `data-architect`, `api-architect`, `qa-tech`<br>- **Fila 3 (Fase D: Builders, Testers, SecOps & SRE):**<br>&nbsp;&nbsp;* `dev-backend`: `target: product-analyst`, `direction: down`<br>&nbsp;&nbsp;* `dev-frontend`: `target: solutions-architect`, `direction: down`<br>&nbsp;&nbsp;* `qa-auto`: `target: data-architect`, `direction: down`<br>&nbsp;&nbsp;* `code-review`: `target: api-architect`, `direction: down`<br>&nbsp;&nbsp;* `devops`: `target: qa-tech`, `direction: down` | Distribución visual simétrica y organizada en terminales Herdr para monitorear la ejecución en tiempo real sin colisiones de split. |
| **FinOps / Model Assignment** | Asignar modelos y niveles de esfuerzo de razonamiento adaptados a cada especialidad: <br>- `dev-backend`: `Gemini 3.7 Flash (High)` (código .NET, VSA y transaccionalidad)<br>- `dev-frontend`: `Gemini 3.7 Flash (High)` (código Angular 22 Zoneless y tipado estricto)<br>- `qa-auto`: `Gemini 3.7 Flash (High)` (análisis adversarial y testing xUnit/Jest)<br>- `code-review`: `Gemini 3.7 Flash (High)` (auditoría SecOps, OWASP y performance)<br>- `devops`: `Gemini 3.7 Flash (Medium)` (templates Docker y workflows CI/CD) | Optimización de tokens y potencia cognitiva según la complejidad operativa del agente. |

### 2.4 `utils/approve_step.py` (Sistema de Aprobación Manual HITL)

| Sección / Líneas | Cambio Requerido | Lógica y Justificación |
|---|---|---|
| **Líneas 74-78 (Opción 10)** | Actualizar la transición de `@QT:` para delegar específicamente hacia la Fase D: `QA Técnico (QT) -> Handoff a Desarrollo (@DEV-BACK: / @DEV-FRONT:)`. | Reemplaza el tag genérico `@DEV:` por la bifurcación explícita de especialidad. |
| **Nuevas Opciones (11 a 14)** | Incorporar opciones de menú para autorizaciones manuales en Fase D:<br>- `[11] Dev Backend -> QA Automation (@QA-AUTO:)`<br>- `[12] Dev Frontend -> QA Automation (@QA-AUTO:)`<br>- `[13] QA Automation -> Code Review (@CODE-REVIEW:)`<br>- `[14] Code Review -> DevOps / Despliegue (@DEVOPS:)` | Permite al humano auditar y certificar cada compuerta de la Fase D antes de dar paso al siguiente agente si se opera en modo HITL asistido. |

### 2.5 `utils/clean_files.py` y `utils/delete_agents.py` (Mantenimiento)

| Script | Cambio Requerido | Justificación |
|---|---|---|
| **`utils/clean_files.py`** | Añadir prefijos y carpetas: `"dev-back:": "dev-backend"`, `"dev-front:": "dev-frontend"`, `"qa-auto:": "qa-auto"`, `"code-rev:": "code-review"`, `"devops:": "devops"`. | Facilita la limpieza interactiva selectiva de entregables de código y pruebas en `files/`. |
| **`utils/delete_agents.py`** | Añadir los 5 nombres a la lista `AGENTS`. | Permite purgar de un solo comando los `AGENTS.md` generados en las 15 carpetas. |

---

## 3. 📄 JSON Exacto para `config_bmad.json`

Se actualizará el archivo central [`config_bmad.json`](file:///D:/Paulo/Cursos/DMC/template-bmad/config_bmad.json) para incluir las rutas absolutas de los 15 agentes, indexando los directorios de trabajo de la Fase D:

```json
{
  "project_name": "inventario",
  "created_at": "2026-09-22 23:10:42",
  "tracker": "D:\\Paulo\\Cursos\\DMC\\template-bmad\\files\\tracker_bmad.md",
  "context": "D:\\Paulo\\Cursos\\DMC\\template-bmad\\files\\context\\legacy_ecosystem.md",
  "routes_bmad": {
    "business-storyteller": "D:\\Paulo\\Cursos\\DMC\\template-bmad\\files\\business-storyteller\\",
    "product-analyst": "D:\\Paulo\\Cursos\\DMC\\template-bmad\\files\\product-analyst\\",
    "product-manager": "D:\\Paulo\\Cursos\\DMC\\template-bmad\\files\\product-manager\\",
    "business-analyst": "D:\\Paulo\\Cursos\\DMC\\template-bmad\\files\\business-analyst\\",
    "qa-documental": "D:\\Paulo\\Cursos\\DMC\\template-bmad\\files\\qa-documental\\",
    "designer-ux": "D:\\Paulo\\Cursos\\DMC\\template-bmad\\files\\designer-ux\\",
    "solutions-architect": "D:\\Paulo\\Cursos\\DMC\\template-bmad\\files\\solutions-architect\\",
    "data-architect": "D:\\Paulo\\Cursos\\DMC\\template-bmad\\files\\data-architect\\",
    "api-architect": "D:\\Paulo\\Cursos\\DMC\\template-bmad\\files\\api-architect\\",
    "qa-tech": "D:\\Paulo\\Cursos\\DMC\\template-bmad\\files\\qa-tech\\",
    "dev-backend": "D:\\Paulo\\Cursos\\DMC\\template-bmad\\files\\dev-backend\\",
    "dev-frontend": "D:\\Paulo\\Cursos\\DMC\\template-bmad\\files\\dev-frontend\\",
    "qa-auto": "D:\\Paulo\\Cursos\\DMC\\template-bmad\\files\\qa-auto\\",
    "code-review": "D:\\Paulo\\Cursos\\DMC\\template-bmad\\files\\code-review\\",
    "devops": "D:\\Paulo\\Cursos\\DMC\\template-bmad\\files\\devops\\"
  }
}
```

*Nota:* Se garantizará la creación física de las 5 carpetas correspondientes en `files/` (`files/dev-backend/`, `files/dev-frontend/`, `files/qa-auto/`, `files/code-review/`, `files/devops/`).

---

## 4. 🗂️ Estructura de Carpetas Resultante y Plan de Documentación

### 4.1 Árbol de Carpetas Estandarizado para los Agentes de Fase D

Para asegurar la homogeneidad del framework, normalizaremos las carpetas de habilidades a `skills/` e incluiremos `README.md` operativo en cada una:

```text
template-bmad/
├── dev-backend/
│   ├── README.md                                      ← [NUEVO] Manual del Senior Backend Developer
│   ├── agents/
│   │   └── dev-backend.agent.md                       ← Identidad, misión y directivas C# 12 / VSA
│   ├── instructions/
│   │   └── zero-hallucination-policy.instructions.md  ← Políticas anti-mock y anti-librerías fantasma
│   └── skills/                                        ← [RENOMBRADO de skill/ a skills/]
│       └── vsa-validator/
│           └── SKILL.md                               ← Checklist de auto-auditoría VSA
│
├── dev-frontend/
│   ├── README.md                                      ← [NUEVO] Manual del Senior Frontend Developer
│   ├── agents/
│   │   └── dev-frontend.agent.md                      ← Identidad, misión y directivas Angular 22
│   ├── instructions/
│   │   └── zero-hallucination-policy.instructions.md  ← Políticas anti-any y anti-legacy zone.js
│   └── skills/
│       └── zoneless-validator/
│           └── SKILL.md                               ← Checklist de auto-auditoría Zoneless & Signals
│
├── qa-auto/
│   ├── README.md                                      ← [NUEVO] Manual del Senior QA Automation Engineer
│   ├── agents/
│   │   └── qa-auto.agent.md                           ← Identidad, xUnit, Testcontainers, Jest
│   ├── instructions/
│   │   └── qa-strict-testing.instructions.md          ← [NUEVO] Estandarización de reglas de testing
│   └── skills/                                        ← [RENOMBRADO de skill/ a skills/]
│       └── qa-strict-testing/
│           └── SKILL.md                               ← Zero-Tautology Policy y cobertura adversarial
│
├── code-review/
│   ├── README.md                                      ← [NUEVO] Manual del Tech Lead & SecOps Reviewer
│   ├── agents/
│   │   └── code-review.agent.md                       ← Identidad, compuerta de calidad, veredictos
│   ├── instructions/
│   │   └── secops-strict-audit.instructions.md        ← CancellationToken, N+1, IDOR, XSS
│   └── skills/
│       └── code-review-gatekeeper/
│           └── SKILL.md                               ← Escaneo físico obligatorio y plantilla [APROBADO]/[RECHAZADO]
│
└── devops/
    ├── README.md                                      ← [NUEVO] Manual del Cloud & SRE Engineer
    ├── agents/
    │   └── devops.agent.md                            ← Identidad, Dockerfiles, compose, CI/CD
    ├── instructions/
    │   └── devops-strict-infra.instructions.md        ← Contenedores rootless, healthchecks y secretos
    └── skills/
        └── devops-validator/
            └── SKILL.md                               ← Checklist de verificación cloud-native
```

### 4.2 Contenido de los READMEs Individuales

Cada `README.md` individual contendrá:
1. **Identidad y Rol:** Descripción del agente, nivel de seniority y especialidad.
2. **Invocación en el Tracker:** Sintaxis del Handoff (`@DEV-BACK:`, `@DEV-FRONT:`, `@QA-AUTO:`, `@CODE-REVIEW:`, `@DEVOPS:`).
3. **Entradas Requeridas (Inputs):** Documentos de referencia obligatorios (`tech-design_*.md`, `hu_*.md`, `legacy_ecosystem.md`).
4. **Entregables Producidos (Outputs):** Rutas de guardado en `files/` o en el repositorio de código.
5. **Skills e Instrucciones Asociadas:** Explicación del checklist y políticas de Cero Alucinación.
6. **Ejemplo de Evento en el Tracker:** Plantilla de reporte con formato de bitácora estricto.

### 4.3 Actualización de la Documentación Global del Framework

1. **`AGENTS.md` (Raíz):**
   - Actualizar el contexto del Meta-Agente para reconocer formalmente las **4 Fases Canónicas de BMAD:**
     - **Fase B (Business):** `business-storyteller`, `product-analyst`
     - **Fase M (Management):** `product-manager`, `business-analyst`, `qa-documental`
     - **Fase A (Architecture):** `designer-ux`, `solutions-architect`, `data-architect`, `api-architect`, `qa-tech`
     - **Fase D (Development & Delivery):** `dev-backend`, `dev-frontend`, `qa-auto`, `code-review`, `devops`
   - Incorporar directiva de segregación entre constructores y auditores.

2. **`ARCHITECTURE.md`:**
   - Incorporar diagrama Mermaid con el flujo completo de 15 agentes, modelando la bifurcación paralela Frontend/Backend y el ciclo de revisión cerrado (`DEV ➔ QA-AUTO ➔ CODE-REVIEW ➔ [RECHAZADO / APROBADO]`).
   - Documentar la división de roles de Fase D: Builders (Devs), Testers (QA Auto), Security & Gatekeepers (Code Review) y Platform/Infra (DevOps).

3. **`README.md` (Raíz):**
   - Actualizar el número oficial de agentes a 15.
   - Reflejar la Fase D en el árbol de carpetas del proyecto.
   - Detallar la nueva compuerta de calidad de software (*Development & Delivery Quality Gate*).

4. **`SETUP.md` y `GUIDE.md`:**
   - Documentar el arranque de la grilla de 15 terminales con `python utils/start_agents.py`.
   - Explicar las opciones avanzadas del aprobador HITL `approve_step.py`.

---

## 5. 🚀 Plan de Ejecución Secuencial Paso a Paso (Post-Aprobación)

Una vez aprobado este plan, se ejecutará el despliegue en las siguientes fases atómicas:

1. **Paso 1 (Normalización de FileSystem):** Renombrar carpetas `skill` a `skills` en `dev-backend` y `qa-auto`. Crear `qa-auto/instructions/qa-strict-testing.instructions.md`. Crear directorios en `files/`.
2. **Paso 2 (Inyección de Tracker-Logger):** Agregar `[IMPORT_SKILL: skills/tracker-logger/SKILL.md]` en las instrucciones de los 5 agentes.
3. **Paso 3 (Actualización de Código Python):**
   - Modificar `watcher_bmad.py` (compilador, inyector resiliente y router).
   - Modificar `init_bmad.py` (scaffolding ampliado).
   - Modificar `utils/start_agents.py` (grilla 3x5 y FinOps).
   - Modificar `utils/approve_step.py` (nuevos handoffs de Fase D).
   - Modificar `utils/clean_files.py` y `utils/delete_agents.py`.
4. **Paso 4 (Configuración Central):** Actualizar `config_bmad.json`.
5. **Paso 5 (Compilación y Ensamblaje):** Ejecutar `compilar_agentes_modulares()` para ensamblar los 15 archivos `AGENTS.md`.
6. **Paso 6 (Generación de Documentación):**
   - Escribir los 5 `README.md` individuales en cada carpeta de agente.
   - Actualizar `AGENTS.md` (raíz), `ARCHITECTURE.md` y `README.md` (raíz).
7. **Paso 7 (Verificación Final):** Ejecutar validación de balance sintáctico de fences Markdown y comprobación de rutas en el orquestador.
