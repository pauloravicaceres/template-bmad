# 🧠 Framework BMAD v2.0 — Arquitectura Maestra

Este es el documento canónico del ecosistema **BMAD** (Business, Management, Architecture & Development). Define la topología, el motor de ejecución, y las reglas inmutables que gobiernan al enjambre de agentes de IA.

---

## 1. ¿Qué es BMAD v2.0?

BMAD es un framework de desarrollo de software estructurado como una "fábrica" determinista. En lugar de tener un único agente genérico, BMAD emplea un **enjambre de agentes hiper-especializados** que se comunican de forma secuencial y asíncrona a través de un bus de datos en texto plano (`files/tracker_bmad.md`).

En su versión 2.0, el framework integra **Spec-Driven Development (SDD)** nativo y un motor de **Ejecución Headless Automática**. Esto permite que el enjambre traduzca requerimientos abstractos de negocio en código de producción altamente testeado, controlado por un sistema Git determinista, minimizando la intervención humana a decisiones puramente estratégicas.

---

## 2. El Motor: Spec Kit y Control de Versiones (Git)

El corazón de BMAD v2.0 es el `watcher_bmad.py`, que actúa no solo como orquestador del tracker, sino como un **Compilador Modular** y **Gatekeeper**.

### A. Integración Git Segura y Autonómica (GitOps)
El framework impone políticas *Zero-Trust* sobre el control de versiones, delegando toda mutación del VCS al orquestador principal mediante *Event-Sourcing*:
1. **Arranque con State Hydration:** Al iniciar, el orquestador escanea la historia del `tracker_bmad.md`. Si detecta que una sesión fue interrumpida en plena creación de una feature, reanuda automáticamente comprobando y saltando a la rama huérfana.
2. **Feature Branching Automatizado:** El Watcher intercepta directivas macro en el tracker (ej. `@WATCHER: GITOPS-BRANCH-CREATE feat/hu`). Antes de procesarlas, verifica la limpieza del *working directory* (`git status --porcelain`), realiza auto-commits de seguridad (`chore: auto-commit pre-branch switch`) y bifurca el repositorio para aislar el diseño de la nueva HU.
3. **Auto-Merge Seguro y Degradación Elegante:** Al finalizar la auditoría (cuando el QT dicta `READY-FOR-DEV`), el Watcher intercepta la directiva `@WATCHER: GITOPS-MERGE-CLOSE`. Realiza la fusión a `dev` de manera síncrona mediante `try/except`. Si hay conflictos, aplica `git merge --abort` y solicita intervención humana inyectando un protocolo instruccional en el tracker. El sistema entra en "Amnesia Estratégica", delegando la jurisdicción de resolución al humano, quien completará el merge y simplemente reiniciará el Watcher sin manipular el bus de datos.
4. **Commits Atómicos Headless:** Durante la Fase de Desarrollo, los agentes no resuelven conflictos ni hacen push. Usan el skill inyectado (`git-commit`) para ejecutar estrictamente `git add {archivos}` y `git commit -m "{convencion} [{TASK-ID}]"`.

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

### II. Flujo de Trabajo Secuencial (GitOps + Agentes)
```mermaid
sequenceDiagram
    actor H as 🧑 Humano
    participant W as 🤖 Watcher (Orquestador)
    participant B as 🏢 Agentes de Negocio
    participant S as ⚙️ GitHub Spec Kit
    participant A as 📐 Agentes de Arquitectura
    participant D as 💻 Agentes Delivery
    participant G as 🌿 Repositorio Git

    H->>W: Inicia Watcher
    W->>B: Despierta Fase de Ideación (@BS -> @PA -> @PM)
    B->>W: @PM inyecta @WATCHER: GITOPS-BRANCH-CREATE feat/hu-01
    W->>G: git checkout -b feat/hu-01 (Transaccional)
    W->>B: Pasa token a @BA (Diseño de HU)
    B-->>W: Escribe HU en tracker (Aprobada por QA)
    
    note over W,S: SDD Auto-Runner (Intercepción)
    W->>S: Ejecuta /specify -> /clarify -> /plan -> /analyze
    
    alt Hay Ambigüedad o Fallo Constitucional
        S-->>W: Error/Duda
        W->>H: ⚠️ HITL: Requiere resolución manual
        H->>W: Resuelve y aprueba paso
    else Cero Fricción (analyze == 0)
        W->>G: git add .specify/ && git commit "spec: [FREEZE]"
        W->>A: Despierta Fase de Arquitectura (@UX -> @SA -> @DA -> @API -> @QT)
    end
    
    A->>W: @QT compila TDD y actualiza Ledger a READY-FOR-DEV
    A->>W: @QT inyecta @WATCHER: GITOPS-MERGE-CLOSE feat/hu-01
    W->>G: git merge --no-ff feat/hu-01 (Auto-Merge)
    W->>H: ⚠️ HITL (Opcional): Conflicto de Merge (si aplica)
    
    A-->>W: @QT inyecta @SPEC-KIT: para Implementación
    W->>D: Despacha Tareas del tasks.md
    loop Cada Tarea Completada
        D->>G: git add {archivos} && git commit -m "feat: [TASK-ID]"
    end
    
    D->>W: Certificado Code-Review (Aprobado)
    W->>H: Turno de Push al remoto
    H->>G: git push origin dev
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

## 5. Ledger de Estado del Producto (Mapa de Specs)

El ecosistema BMAD implementa un **Mapa de Specs** (ubicado en `specs/README.md`) que actúa como un Ledger inmutable del ciclo de vida de las funcionalidades. Este artefacto soluciona la pérdida de contexto en proyectos de larga duración.

### Gobernanza del Ledger:
1. **Lectura Obligatoria:** Los agentes de diseño (`@BA`, `@SA`) consumen este mapa antes de cualquier iteración para alinear las nuevas HUs con la topología existente y evitar solapamientos.
2. **Escritura Orquestada:** Los agentes de validación y gestión (`@PM`, `@QT`) utilizan la habilidad `update-specs-map` para actualizar determinísticamente el estado de las funcionalidades (ACTIVE, IN-PROGRESS, DEPRECATED) mediante manipulaciones precisas de Markdown.

Este mecanismo garantiza una fuente única de verdad libre de alucinaciones algorítmicas, esencial para la correcta transición de Modos Greenfield a Brownfield.

## 6. Ciclo de Vida de Ramas (GitOps Workflow)

El siguiente diagrama detalla cómo el ecosistema aisla el trabajo en ramas de *feature* y cómo el **Watcher** orquesta los cambios de estado en el control de versiones, incluyendo el protocolo de resiliencia ante conflictos (Amnesia Estratégica).

```mermaid
flowchart TD
    DEV(("Rama Base\n(dev/main)"))
    
    subgraph FASE_IDEACION ["Ideación (En rama base)"]
        PM["@PM estructura el MVP"]
    end
    
    subgraph INTERCEPCION_CREATE ["Watcher: Branch Create"]
        W1["Intercepta GITOPS-BRANCH-CREATE"]
        W2["Auto-Commit Seguridad"]
        W3["git checkout dev"]
        W4["git checkout -b feat/HU_x"]
    end
    
    subgraph FASE_DISENO ["Diseño Aislado (feat/HU_x)"]
        BA["@BA: Historias de Usuario"]
        QA["@QA: Aprobación Documental"]
        SA["@SA: Arquitectura (SDD Auto-Runner)"]
        QT["@QT: Aprobación Técnica (Tech Design)"]
    end
    
    subgraph INTERCEPCION_CLOSE ["Watcher: Merge Close"]
        W5["Intercepta GITOPS-MERGE-CLOSE"]
        W6["git checkout dev"]
        W7{"¿Hay Conflictos?"}
        W8["git merge --no-ff feat/HU_x\ngit branch -d feat/HU_x"]
        W9["git merge --abort"]
    end
    
    subgraph HUMANO ["Amnesia Estratégica (Fallback)"]
        H1["Humano resuelve conflicto en terminal"]
        H2["Humano fusiona a dev manualmente"]
        H3["Humano reinicia Watcher"]
    end
    
    DEV --> FASE_IDEACION
    PM -- "Emite macro" --> W1
    W1 --> W2 --> W3 --> W4
    W4 -- "Bifurcación exitosa" --> BA
    BA --> QA --> SA --> QT
    QT -- "Emite macro" --> W5
    W5 --> W6 --> W7
    
    W7 -- "Fusión Limpia (No)" --> W8
    W8 -- "Retorna control" --> DEV
    
    W7 -- "Sí (Colisión)" --> W9
    W9 -- "Emite @HUMANO: 🚨 ALERTA" --> H1
    H1 --> H2 --> H3
    H3 -- "Reanuda limpio" --> DEV

    style DEV fill:#f9f,stroke:#333,stroke-width:2px,color:#000
    style INTERCEPCION_CREATE fill:#d4edda,stroke:#28a745,stroke-dasharray: 5 5,color:#000
    style INTERCEPCION_CLOSE fill:#cce5ff,stroke:#007bff,stroke-dasharray: 5 5,color:#000
    style HUMANO fill:#f8d7da,stroke:#dc3545,color:#000
```
