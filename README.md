# 🏛️ Ecosistema Multi-Agente BMAD v2.0 (con SDD y Herdr)

> Framework y plugin organizacional para la definición integral, autónoma y desacoplada de software bajo metodología BMAD (Business, Management, Architecture, Development). Orquestado sobre terminales independientes en **Herdr**, automatización Git Headless y herramientas MCP.

---

## 🚀 Arranque Rápido (Quick Start)

El ecosistema v2.0 asume control estricto de repositorios. Para instanciar y correr un proyecto limpio:

1. **Clonar de forma segura:**
   ```bash
   python utils/clone_template.py "D:\ruta\a\nuevo-proyecto"
   ```
2. **Inicializar Repositorio y Entorno (en la nueva ruta):**
   ```bash
   cd "D:\ruta\a\nuevo-proyecto"
   git init && git add . && git commit -m "chore: inicialización BMAD"
   python init_bmad.py "Mi Nuevo Sistema"
   ```
3. **Arrancar el Motor Orquestador:**
   ```bash
   python watcher_bmad.py --branch feat/modulo-registro
   ```
4. **Levantar la Flota de Agentes en Herdr (en otra terminal):**
   ```bash
   python utils/start_agents.py
   ```

---

## 🛠️ Bitácora de Herramientas de Mantenimiento (`/utils`)

La carpeta `utils/` contiene los scripts operativos que le dan al humano el control absoluto sobre el ciclo de vida del framework:

| Script | Propósito y Comportamiento |
|---|---|
| **`clone_template.py`** | Script automatizado de *Scaffolding*. Utiliza una lista blanca estricta para clonar el motor BMAD hacia una nueva ruta. Evita arrastrar historiales (`.git/`), archivos transitorios (`plan.md`) o cachés de proyectos anteriores. |
| **`start_agents.py`** | Despliega simultáneamente a los 15 agentes de IA. Crea 3 pestañas temáticas en **Herdr** (Negocio, Arquitectura y Delivery), divide los paneles inyectando el contexto de las instrucciones y arranca los bucles de escucha. |
| **`stop_agents.py`** | *Kill-switch* controlado. Busca y cierra limpiamente todas las pestañas, paneles y procesos residuales de Herdr asociados al ecosistema para liberar memoria de la terminal. |
| **`approve_step.py`** | Motor del *Human-in-the-Loop (HITL)*. Cuando el framework se pausa obligatoriamente (ej. tras el Product Brief o la auditoría Spec Kit), este script permite al humano revisar los artefactos y autorizar matemáticamente la transición hacia el siguiente agente en el tracker. |
| **`clean_files.py`** | Utilidad interactiva de mantenimiento. Permite purgar selectivamente los entregables (Markdowns, PDFs, Códigos) generados en la carpeta `files/` para resetear un pipeline fallido, conservando intactos el Tracker y la Constitución. |
| **`delete_agents.py`** | Limpiador del Meta-Agente. Borra los archivos `AGENTS.md` compilados dinámicamente para forzar al orquestador a re-inyectar las skills (`[IMPORT_SKILL]`) en el siguiente arranque. |
| **`response_sa.py`** | Herramienta de *mocking* o debugging interno utilizada para simular las respuestas del Arquitecto de Soluciones y destrabar cuellos de botella en la fase de pruebas de handoff. |

---

## 🌟 Características Fundamentales

* **Integración Nativa SDD (Spec-Driven Development vía GitHub Spec Kit):** El framework incorpora un puente determinista llamado **SDD Auto-Runner**. Tras la validación de QA Documental, el orquestador congela automáticamente el diseño (`git commit -m "[SPEC-FREEZE]"`) ejecutando de manera desatendida `/speckit.specify -> /clarify -> /plan -> /tasks -> /analyze`.
* **Commits Atómicos Headless:** Durante la Fase D, los agentes programadores carecen de capacidades interactivas. Ejecutan código e inyectan commits en Git aislando lógicamente cada característica (`git add . && git commit -m "feat: [TASK-ID]"`).
* **Estrategia Dual-Output de Requisitos (Business Analyst):** Generación simultánea de Historias Técnicas (Gherkin puro para Spec Kit) y Funcionales (Narrativas amigables para Stakeholders).
* **Fase D (Ingeniería) como Cartucho Intercambiable:** Arquitectura desacoplada con segregación entre Constructores (`DEV-BACK`, `DEV-FRONT`) y Auditores (`QA-AUTO`, `CODE-REVIEW`). Todos dotados con `execute_command` para operar físicamente la máquina del host.
* **Lógica de Bypass Inteligente:** El `config_bmad.json` decide rutas. En `project_type: ui` pasa al diseñador `@UX:`. En `project_type: headless`, salta directamente al `@SA:` ahorrando tiempo.
* **El Tracker como Único Bus de Datos:** Eliminación de alucinaciones inter-agente. Se comunican exclusivamente anexando texto (*read -> concat -> write*) en `files/tracker_bmad.md`.

---

## 🔄 Flujo Secuencial del Ciclo BMAD

```mermaid
flowchart TD
    Idea["💡 Idea Cruda del Stakeholder"] --> BS["1. Business Storyteller (BS)<br><i>Discovery y Optimización</i>"]
    BS -->|"idea_*.md"| PA["2. Product Analyst (PA)<br><i>Product Brief (PRD)</i>"]
    PA -->|"pb_*.md"| HITL["👤 Pausa Obligatoria HITL<br><i>(approve_step.py -> @PM:)</i>"]
    HITL -->|"Aprobado por Humano"| PM["3. Product Manager (PM)<br><i>MVP y Backlog de Épicas</i>"]
    PM -->|"mvp_*.md"| BA["4. Business Analyst (BA)<br><i>Dual-Output (Técnica & Stakeholders)</i>"]
    BA -->|"hu_*.md"| QA{"5. QA Documental (QA)<br><i>Auditoría de Requisitos</i>"}
    QA -->|"Rechazo / Feedback"| BA
    
    %% Puente SDD Gatekeeper
    QA -->|"Aprobado: SDD Auto-Runner"| SDD_PAUSE["🤖 Ejecución Autónoma de Spec Kit<br><i>(Si falla -> HITL Manual)</i>"]
    subgraph SPEC_SUITE ["⚙️ GitHub Spec Kit"]
        direction TB
        SDD_PAUSE --> SPEC_CMD["/specify -> /clarify -> /plan -> /tasks -> /analyze"]
        SPEC_CMD --> FREEZE["git add .specify/ && git commit [SPEC-FREEZE]"]
    end
    FREEZE -->|"Bypass Flag en JSON"| ROUTE{"Ruta de Proyecto"}
    
    ROUTE -->|"UI"| UX["6. Designer UX (UX)<br><i>Wireframes ASCII (tasks.md)</i>"]
    UX -->|"MVP Concluido"| SA["7. Solutions Architect (SA)<br><i>Stack, Gobernanza & ADRs (plan.md)</i>"]
    ROUTE -->|"Headless"| SA
    
    SA -->|"tech_guidelines.md"| DA["8. Data Architect (DA)<br><i>MER y Persistencia (spec.md)</i>"]
    DA -->|"Requiere APIs"| API["9. API Architect (API)<br><i>Contratos REST/GraphQL</i>"]
    API -->|"api_*.md"| QT["10. QA-Tech (QT)<br><i>Auditoría Cruzada TDD</i>"]
    DA -->|"Headless sin APIs"| QT
    
    QT -->|"tech-design_*.md"| IMP["⚡ /speckit.implement<br><i>(Gatillo Fase D)</i>"]
    
    subgraph FASE_D ["🤖 Fase D: Ingeniería Headless (execute_command + Git)"]
        direction TB
        IMP --> DevBack["11. Dev Backend (DEV-BACK)<br><i>Lógica & Endpoints</i>"]
        IMP --> DevFront["12. Dev Frontend (DEV-FRONT)<br><i>UI & Clientes</i>"]
        IMP --> DevOps["13. DevOps & SRE (DEVOPS)<br><i>Compose & CI/CD</i>"]
        DevBack & DevFront --> QAAuto["14. QA Automation (QA-AUTO)<br><i>Tests Zero-Tautology</i>"]
        QAAuto -->|"Pruebas Verificadas"| CR{"15. Code Review (CR)<br><i>Quality Gate & SecOps</i>"}
    end
    
    CR -->|"Rechazo de Calidad"| DevBack
    CR -->|"Aprobado"| Fin["🚀 Software en Producción (Commits Atómicos Listos)"]
    QT -.->|"Context Distillation"| Legacy[("🏛️ .specify/memory/constitution.md<br><i>Memoria Invariante para Iteraciones Brownfield</i>")]
```

---

## 🛡️ Gobernanza Arquitectónica Automatizada (Lex Superior) y Blindaje Anti-Sycophancy

En sistemas multi-agente operados con modelos fundacionales (LLMs), un riesgo latente es la **complacencia algorítmica (*sycophancy*)**: la tendencia del modelo a obedecer sumisamente las solicitudes inmediatas de un usuario, incluso cuando contradicen directamente las invariantes técnicas preexistentes.

BMAD instituye el principio jurídico-técnico de **Lex Superior** y un sistema de **Defensa en Profundidad**:

```mermaid
flowchart TD
    subgraph JerarquiaNormativa ["Pirámide de Jerarquía Normativa (Lex Superior)"]
        direction TB
        L1["🏛️ Nivel 1 (Constitución Inviolable):<br><b>.specify/memory/constitution.md</b><br><i>(Stack, Motores DB, Patrones Base)</i>"]
        L2["📐 Nivel 2 (Directiva de Solución):<br><b>tech_guidelines.md</b><br><i>(ADRs MADR subordinados al Nivel 1)</i>"]
        L3["💾 Nivel 3 (Diseño de Persistencia y Red):<br><b>db_*.md / api_*.md</b><br><i>(Modelado MER y Contratos REST/GraphQL)</i>"]
        L4["💬 Nivel 4 (Peticiones Transitorias):<br><b>files/tracker_bmad.md</b><br><i>(Instrucciones en caliente)</i>"]
    end
    
    L1 ==>|Prevalece sobre| L2
    L2 ==>|Prevalece sobre| L3
    L3 ==>|Prevalece sobre| L4
```

1. **Barrera 1 - Solutions Architect (SA):** Anula de plano peticiones transitorias si contradicen el archivo físico de Constitución.
2. **Barrera 2 - Data & API Architects:** Tienen inmunidad jerárquica para desobedecer directrices del SA si detectan desviación constitucional.
3. **Barrera 3 - QA Tech (Guardián Inflexible):** Rechaza sumariamente diseños que violen la constitución emitiendo error 🔴 **CRÍTICO: Complacencia Ilegal (Sycophancy Breach)**.

---

## 📚 Documentación de Referencia

| Documento / Archivo | Propósito Principal |
|---|---|
| [**`framework_bmad.md`**](./framework_bmad.md) | **[DOCUMENTO MAESTRO] Arquitectura técnica profunda, Git Headless y topología de componentes.** |
| [**`SETUP.md`**](./SETUP.md) | Guía de parametrización estricta para crear y clonar proyectos con `clone_template.py`. |
| [**`GUIDE.md`**](./GUIDE.md) | Manual operativo paso a paso y solución de incidentes del día a día. |
| [**`PLUGGABLE_PHASE_D.md`**](./PLUGGABLE_PHASE_D.md) | Especificación de Cartucho Intercambiable (Cambio de Lenguaje/Stack de los agentes programadores). |
| [**`BMAD_AUDIT_REPORT.md`**](./BMAD_AUDIT_REPORT.md) | Reporte interno de certificación de salud arquitectónica del framework. |
