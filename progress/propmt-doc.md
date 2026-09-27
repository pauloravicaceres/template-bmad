# 🎯 ROL Y MISIÓN
Actúa como **Meta-Arquitecto y Guardián del Framework BMAD**. La mutación de código, inyección de herramientas CLI y reestructuración de agentes para la Fase 2 (SDD vía Spec Kit) ha concluido con éxito en el FileSystem.

Tu misión final es sincronizar la documentación global de la raíz del repositorio para que refleje con exactitud la nueva topología, la mecánica de intercepción y la gobernanza transversal.

---

# 🛠️ TAREAS DE DOCUMENTACIÓN A EJECUTAR

### 1. Refactor de `ARCHITECTURE.md`
Reescribe las secciones desactualizadas de este documento. Debes inyectar y explicar los siguientes conceptos clave:
- **Gobernanza Transversal (Lex Superior):** Explica que `.specify/memory/constitution.md` y las políticas `.instructions.md` actúan como *System Prompts* que auditan todas las fases.
- **Estrategia Dual-Output (Fase M):** Documenta que el `@BA` ahora genera HUs para stakeholders (en `files/business-analyst/HUs-stakeholders/`) y HUs técnicas en Gherkin estricto para la máquina.
- **SDD Gatekeeper (El Puente Spec Kit):** Explica la intercepción lógica del `watcher_bmad.py` tras el certificado del `@QA:` y cómo el CLI de Spec Kit toma el relevo (`/specify`, `/plan`, `/tasks`, `/analyze`).
- **Inyección del Diagrama Maestro:** Agrega este diagrama de flujo con esta topología exacta:

```mermaid
flowchart TD
    classDef gov fill:#2d3748,stroke:#cbd5e0,stroke-width:2px,color:#fff,stroke-dasharray: 5 5
    classDef bmad fill:#1a365d,stroke:#2b6cb0,stroke-width:2px,color:#fff
    classDef speckit fill:#276749,stroke:#48bb78,stroke-width:2px,color:#fff

    subgraph GOVERNANCE ["🏛️ CAPA TRANSVERSAL (SYSTEM PROMPTS)"]
        direction LR
        CONST["constitution.md"]:::gov
        POLICIES["*.instructions.md"]:::gov
        AGISTRY["AGENTS.md"]:::gov
    end

    subgraph DISCOVERY ["🤖 BMAD — Fases B y M (Ideación)"]
        direction TB
        BS(["bs"]) --> PA(["pa"]) --> PM(["pm"]) --> BA(["ba"]) --> QA_DOC(["qa"])
    end

    subgraph SPECKIT_PLAN ["⚙️ SPEC KIT — SDD Planning"]
        direction TB
        SPEC["/speckit.specify"]:::speckit --> CLAR["/speckit.clarify"]:::speckit
        CLAR --> PLAN["/speckit.plan"]:::speckit
        PLAN --> TASKS["/speckit.tasks"]:::speckit
        TASKS --> AN["/speckit.analyze"]:::speckit
    end

    subgraph ARCHITECTURE ["🤖 BMAD — Fase A (Diseño)"]
        direction TB
        UX(["ux"]) --> SA(["sa"]) --> DA(["da"]) --> API(["api"]) --> QT(["qt"])
    end

    IMP["⚡ /speckit.implement"]:::speckit

    subgraph DELIVERY ["🤖 BMAD — Fase D (Ingeniería y Entrega)"]
        direction TB
        DEVOPS(["devops"])
        DEV_B(["dev-back"])
        DEV_F(["dev-front"])
        QA_A(["qa-auto"])
        CR(["code-rev"])

        DEVOPS ~~~ DEV_B
        DEV_B --> QA_A
        DEV_F --> QA_A
        QA_A --> CR
    end

    %% Flujo Principal
    QA_DOC -- "Pausa SDD (Watcher)" --> SPEC
    AN -- "Liberación Manual (approve_step.py)" --> UX
    QT --> IMP
    IMP --> DEVOPS & DEV_B & DEV_F
    
    GOVERNANCE -. "Audita Reglas de Negocio y Calidad" .-> DISCOVERY & SPECKIT_PLAN & ARCHITECTURE & DELIVERY
```

1. Refactor de README.md
Actualiza la sección de "Cómo usar el framework" o "Flujo de Ejecución".

Añade un paso explícito explicando que la consola se pausará después de que el QA Documental apruebe, indicando al usuario humano que debe ejecutar los comandos CLI de specify y luego usar python utils/approve_step.py para reanudar el orquestador hacia la Fase A.

Menciona que los agentes de desarrollo ahora tienen capacidad de ejecución en terminal (execute_command).

3. Recompilación del AGENTS.md
Si no lo has hecho como parte de la ejecución del plan, ejecuta el script o lógica correspondiente (ej. watcher_bmad.compilar_agentes_modulares()) para que el AGENTS.md de la raíz refleje las nuevas herramientas (execute_command) y descripciones actualizadas de todos los agentes.

📦 ENTREGABLE EXIGIDO (OUTPUT)
Modifica los archivos ARCHITECTURE.md, GUIDE.md, SETUP.md, DIAGRAMAS.md y README.md directamente usando tus herramientas de escritura.

Compila el nuevo AGENTS.md.

Imprime un reporte conciso confirmando que la documentación refleja al 100% la Fase 2 (SDD).
