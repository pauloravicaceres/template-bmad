# 🧠 Framework BMAD v2.0 — Arquitectura Maestra

Este es el documento canónico del ecosistema **BMAD** (Business, Management, Architecture & Development). Define la topología, el motor de ejecución, y las reglas inmutables que gobiernan al enjambre de agentes de IA.

---

## 1. ¿Qué es BMAD v2.0?

BMAD es un framework de desarrollo de software estructurado como una "fábrica" determinista. En lugar de tener un único agente genérico, BMAD emplea un **enjambre de agentes hiper-especializados** que se comunican de forma secuencial y asíncrona a través de un bus de datos en texto plano (`files/tracker_bmad.md`).

En su versión 2.0, el framework integra **Spec-Driven Development (SDD)** nativo y un motor de **Ejecución Headless Automática**. Esto permite que el enjambre traduzca requerimientos abstractos de negocio en código de producción altamente testeado, controlado por un sistema Git determinista, minimizando la intervención humana a decisiones puramente estratégicas.

---

## 2. El Motor: Spec Kit y Control de Versiones (Git)

El corazón de BMAD v2.0 es el `watcher_bmad.py`, que actúa no solo como orquestador del tracker, sino como un **Compilador Modular** y **Gatekeeper**.

### A. Integración Git Segura y Autonómica
El framework impone políticas *Zero-Trust* sobre el control de versiones para proteger el repositorio:
1. **Arranque Aislado (`--branch`):** El orquestador requiere obligatoriamente que el humano especifique una rama al arrancar (`python watcher_bmad.py --branch feat/mi-rama`). El script ejecuta la verificación de idempotencia, y crea/reactiva la rama automáticamente. Ningún agente opera sobre `main`.
2. **Spec Freeze:** Al completar el diseño técnico, el propio orquestador realiza un commit congelando las especificaciones (`git commit -m "spec: [SPEC-FREEZE]"`).
3. **Commits Atómicos Headless:** Durante la Fase de Desarrollo, los agentes no pueden usar prompts interactivos, resolver conflictos de merge, ni hacer `git push`. Usan el skill inyectado (`git-commit`) para ejecutar estrictamente `git add {archivos}` y `git commit -m "{convencion} [{TASK-ID}]"`. El push al remoto se reserva como el privilegio final e indelegable del humano.

### B. SDD Auto-Runner y HITL por Excepción
En la versión 2.0, la transición entre el análisis de negocio y el diseño arquitectónico ya no es manual.
1. **Intercepción SDD Gatekeeper:** Cuando QA Documental emite su certificado de aprobación, el watcher intercepta el evento.
2. **Ejecución Autónoma:** Inicia silenciosamente el ciclo GitHub Spec Kit (`specify -> clarify -> plan -> tasks -> analyze`).
3. **HITL (Human-in-the-Loop) por Excepción:** El watcher *solo* pausa la ejecución y despierta al Humano si detecta símbolos de ambigüedad (preguntas o dudas en la fase de clarificación) o si la auditoría técnica falla por violación a la constitución. Si no hay fricción, el sistema hace el handoff directamente al Arquitecto de Soluciones (`@SA`) o de UI (`@UX`) leyendo el flag dinámico en `config_bmad.json`.

---

## 3. Flujo Narrativo por Agente (El Enjambre)

El ciclo de vida del software en BMAD atraviesa 4 grandes fases cronológicas:

### FASE B & M (Ideación, Análisis y QA Documental)
*   **`@BS` (Business Storyteller):** Recibe la idea abstracta del humano y la expande en una narrativa de negocio, analizando viabilidad y mercado.
*   **`@PA` (Product Analyst):** Estructura la narrativa en un Product Brief formal (PRD), definiendo objetivos, métricas y restricciones.
*   **`@PM` (Product Manager):** Extrae el alcance real, prioriza y diseña el documento del Producto Mínimo Viable (MVP).
*   **`@BA` (Business Analyst):** Emplea una estrategia "Dual-Output". Genera Historias de Usuario (HUs) técnicas en Gherkin puro, y en paralelo, versiones comprensibles para los stakeholders de negocio.
*   **`@QA` (QA Documental):** Ejerce de auditor de las HUs. Verifica la consistencia, el comportamiento no-tautológico y la coherencia general. Su "Aprobado" activa el SDD Auto-Runner.

### FASE A (Arquitectura y Diseño Técnico)
*(Esta fase es pre-alimentada por el Spec Freeze automático del SDD Auto-Runner).*
*   **`@UX` (Designer UX):** (Solo en proyectos con UI). Calca la funcionalidad de la HU en wireframes de texto (ASCII/Skeleton) y define jerarquías visuales.
*   **`@SA` (Solutions Architect):** Lee el `constitution.md` y dicta las Technical Guidelines, decidiendo el stack y los ADRs (Architecture Decision Records).
*   **`@DA` (Data Architect):** Modela las estructuras de persistencia, generando el MER y asegurando el aislamiento (ej. por schema).
*   **`@API` (API Architect):** Define los contratos REST o GraphQL, mapeando las fronteras del backend.
*   **`@QT` (QA Tech):** Actúa como el Compilador Humano. Cruza contratos y modelos, y genera el `tech-design.md` maestro. Tras su aprobación, se gatilla el implementador de la Fase D.

### FASE D (Delivery, Ejecución Headless)
Los constructores reciben tareas granulares del archivo `tasks.md` generado en el Spec Kit. Trabajan localmente y efectúan commits atómicos asíncronos.
*   **`@DEVOPS`:** Aprovisiona la infraestructura asíncrona (Docker, DBs, Keycloak) mediante scripts no interactivos.
*   **`@DEV-BACK`:** Modela los endpoints, la lógica de dominio (VSA) y la persistencia EF Core.
*   **`@DEV-FRONT`:** Desarrolla los componentes UI (ej. Angular 22 Zoneless) respetando el esqueleto dictado por UX.
*   **`@QA-AUTO`:** Escribe pruebas end-to-end e integración (xUnit, Jest, Playwright) con cobertura de casos felices y tristes.
*   **`@CODE-REVIEW`:** El Gatekeeper final. Audita seguridad (SecOps), adherencia a las reglas y decide si la rama puede ser liberada.

---

## 4. Diagramas de Arquitectura

### I. Arquitectura Lógica de Alto Nivel
```mermaid
flowchart TD
    subgraph Gobernanza["Gobernanza y Contexto Global"]
        CONST[ constitution.md ]
        CONF[ config_bmad.json ]
        SKILLS[ Skills Modulares ]
    end

    subgraph Ideacion["Fase B & M: Negocio"]
        BS[Business Storyteller] --> PA[Product Analyst]
        PA --> PM[Product Manager]
        PM --> BA[Business Analyst]
        BA --> QA_DOC[QA Documental]
    end

    subgraph SDD["SDD Bridge (Watcher Auto-Runner)"]
        SPEC_KIT[[GitHub Spec Kit]]
        HITL{HITL por Excepcion?}
    end

    subgraph Arq["Fase A: Arquitectura"]
        UX[Designer UX] --> SA[Solutions Architect]
        SA --> DA[Data Architect]
        DA --> API[API Architect]
        API --> QT[QA Tech]
    end

    subgraph Delivery["Fase D: Delivery y Git"]
        DEV_B[Dev Backend]
        DEV_F[Dev Frontend]
        DEVOPS[DevOps]
        QA_A[QA Auto]
        CR[Code Review]
    end

    QA_DOC -- "Certificado Aprobado" --> SPEC_KIT
    SPEC_KIT --> HITL
    HITL -- "Pausa Manual" --> Humano((Humano))
    Humano --> Arq
    HITL -- "Éxito (Spec Freeze)" --> Arq
    
    QT -- "/speckit.implement" --> Delivery
    Delivery --> CR

    Gobernanza -. "Dicta Reglas a" .-> Ideacion
    Gobernanza -. "Dicta Reglas a" .-> Arq
    Gobernanza -. "Dicta Reglas a" .-> Delivery
```

### II. Flujo de Trabajo Secuencial (Git + Agentes)
```mermaid
sequenceDiagram
    actor H as 🧑 Humano
    participant W as 🤖 Watcher (Orquestador)
    participant B as 🏢 Agentes de Negocio
    participant S as ⚙️ GitHub Spec Kit
    participant A as 📐 Agentes de Arquitectura
    participant D as 💻 Agentes Delivery
    participant G as 🌿 Repositorio Git

    H->>W: python watcher_bmad.py --branch feat/hu-01
    W->>G: git checkout -b feat/hu-01 (Idempotente)
    W->>B: Despierta Fase de Ideación
    B-->>W: Escribe HU en tracker (Aprobada por QA)
    
    note over W,S: SDD Auto-Runner (Intercepción)
    W->>S: Ejecuta /specify -> /clarify -> /plan -> /analyze
    
    alt Hay Ambigüedad o Fallo Constitucional
        S-->>W: Error/Duda
        W->>H: ⚠️ HITL: Requiere resolución manual
        H->>W: Resuelve y aprueba paso
    else Cero Fricción (analyze == 0)
        W->>G: git add .specify/ && git commit "spec: [FREEZE]"
        W->>A: Despierta Fase de Arquitectura
    end
    
    A-->>H: Entrega tech-design_maestro.md
    H->>G: git commit "arch: Diseño Técnico Aprobado"
    H->>W: /speckit.implement (Activa Fase D)
    
    W->>D: Despacha Tareas del tasks.md
    loop Cada Tarea Completada
        D->>G: git add {archivos} && git commit -m "feat: [TASK-ID]"
    end
    
    D->>W: Certificado Code-Review (Aprobado)
    W->>H: Turno de Push
    H->>G: git push origin feat/hu-01
```

### III. Capa Transversal (Modelo de Capas de Restricción)
```mermaid
flowchart TD
    subgraph L0 ["Capa de Ejecución Dinámica"]
        Agentes["Enjambre de 15 Agentes (.agent.md)"]
    end

    subgraph L1 ["Capa Táctica (Skills y Herramientas)"]
        SK1["skills/git-commit"]
        SK2["skills/hu-validator"]
        CMD["Herramientas (execute_command, write_file)"]
    end

    subgraph L2 ["Capa Estratégica (Instrucciones)"]
        INST["*.instructions.md (Ej: cli-headless-execution)"]
        CONF["config_bmad.json (Flag UI/Headless)"]
    end

    subgraph L3 ["Lex Superior (Constitución)"]
        CONST["constitution.md (Invariantes Tecnológicas y Reglas de Negocio Puras)"]
    end

    L3 ==> L2
    L2 ==> L1
    L1 ==> L0

    style L3 fill:#ffcccc,stroke:#ff0000,stroke-width:2px,color:#000
    style L2 fill:#ffe6cc,stroke:#ff9900,stroke-width:2px,color:#000
    style L1 fill:#ffffcc,stroke:#cccc00,stroke-width:2px,color:#000
    style L0 fill:#e6ffcc,stroke:#33cc33,stroke-width:2px,color:#000
```
