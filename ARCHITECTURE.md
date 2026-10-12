# Arquitectura del framework BMAD

BMAD es un motor Python que orquesta agentes de IA por roles sobre workspaces de proyecto
aislados. El motor (`ENGINE_ROOT`) se instala una vez y aporta runtime, perfiles, skills,
plantillas y dashboard. Cada proyecto (`WORKSPACE_ROOT`) conserva su identidad, configuración,
entregables, código, especificaciones, tracker y estado. El framework no impone el stack de
la aplicación: cada workspace lo define o lo descubre en su propia constitución técnica.

Este documento describe la arquitectura implementada. Instalación y configuración están en
[SETUP.md](SETUP.md); operación diaria en [GUIDE.md](GUIDE.md); el contrato por módulo
(funciones, consumidores y efectos) en [bmad_runtime/README.md](bmad_runtime/README.md).

## 1. Contexto del sistema

```mermaid
flowchart LR
    OP(["Operador humano"])
    subgraph Motor["ENGINE_ROOT: framework compartido"]
        CLI["Scripts CLI<br/>init_bmad, start_agents,<br/>watcher_bmad, stop_agents"]
        RT["bmad_runtime"]
        DB["Dashboard<br/>bmad-control-center"]
        RES["Perfiles de rol, skills,<br/>plantillas, constitution.md"]
    end
    HERDR["Herdr<br/>servidor de paneles"]
    PROV["CLIs de proveedor<br/>Claude, Codex"]
    subgraph WS["WORKSPACE_ROOT: un proyecto"]
        FILES["docs, app, specs,<br/>handoffs, state, .specify"]
        GIT[("Repositorio Git<br/>propio del workspace")]
    end
    OP --> CLI
    OP --> DB
    OP -->|"idea y aprobaciones"| HERDR
    CLI --> RT
    RT --> RES
    RT -->|"verbos herdr"| HERDR
    HERDR -->|"agentes interactivos"| PROV
    RT -->|"operaciones headless"| PROV
    PROV -->|"escriben artefactos"| FILES
    RT --> FILES
    RT -->|"ramas, freeze, merge"| GIT
    DB -->|"lectura y decisiones HITL"| FILES
    DB -->|"telemetría de solo lectura"| GIT
```

- El operador entrega la idea en el panel de Business Storyteller y atiende las compuertas
  humanas desde CLI (`utils/approve_step.py`, `utils/response_sa.py`) o el dashboard.
- Gemini está registrado en el adaptador, pero no construye comandos ejecutables.
- El motor no instala Herdr ni los CLIs de proveedor; los invoca como procesos externos.

## 2. Componentes

```mermaid
flowchart TB
    subgraph Entradas["Entradas públicas"]
        INIT["init_bmad.py<br/>utils/manage_workspace.py"]
        START["utils/start_agents.py"]
        WATCH["watcher_bmad.py"]
        STOP["utils/stop_agents.py"]
        HUMAN["utils/approve_step.py<br/>utils/response_sa.py"]
        STATECLI["python -m bmad_runtime.state"]
    end
    subgraph Nucleo["bmad_runtime"]
        CTX["context.py<br/>ProjectContext"]
        WSP["workspace.py<br/>bootstrap y migración"]
        CFG["config.py<br/>RuntimeConfig"]
        REG["registry.py y providers.py<br/>ProviderFactory, adaptadores"]
        RUN["runtime.py<br/>Runtime"]
        CMD["commands.py<br/>CommandRunner"]
        CLIPY["cli.py<br/>launcher y spec_plan"]
        FLEET["fleet.py<br/>FleetOrchestrator"]
        HG["herdr.py<br/>HerdrGateway"]
        SVC["services.py<br/>SpecKitExecutor,<br/>AgentDispatcher, SessionManager"]
        TC["technical_context.py<br/>assemble, discover"]
        ST["state.py<br/>StateStore, project_lock"]
        WSV["watcher_service.py<br/>cursor y cola"]
        WF["workflow.py<br/>reglas BMAD/SDD y bucle"]
        GO["gitops.py<br/>GitService"]
        MNT["maintenance.py<br/>SessionMaintenance, Coordination"]
        GRD["guard.py<br/>Guard, recomendaciones"]
        HN["hu_naming.py<br/>contrato de nombres HU"]
    end
    UXR["ux_routing.py"]
    subgraph Dash["bmad-control-center"]
        API["backend FastAPI<br/>core, api, services"]
        UI["frontend Nuxt<br/>api_client.ts"]
    end
    INIT --> WSP
    START --> CLIPY --> FLEET
    WATCH --> WF
    STOP --> MNT
    HUMAN --> CTX
    STATECLI --> ST
    WSP --> CTX
    WSP --> CFG
    RUN --> CTX
    RUN --> CFG
    RUN --> REG
    RUN --> CMD
    RUN --> HG
    RUN --> ST
    RUN --> SVC
    CLIPY --> RUN
    WF --> RUN
    MNT --> RUN
    FLEET --> SVC
    FLEET --> HG
    FLEET --> UXR
    SVC --> TC
    SVC --> REG
    WF --> WSV --> ST
    WF --> GO --> CMD
    WF --> UXR
    HG --> CMD
    REG --> CMD
    RUN --> GRD
    MNT --> SVC
    MNT --> HG
    FLEET -->|"VERIFY inicial"| MNT
    WF --> GRD
    WF --> HN
    HUMAN --> HN
    UI -->|"HTTP y WebSocket"| API
    API --> CTX
    API --> CFG
    API --> TC
    API --> HN
```

| Componente | Módulos | Responsabilidad |
|---|---|---|
| Identidad y perímetro | `context.py` | Selección por CLI, entorno o registro; `output()` rechaza escapes, enlaces y rutas ambiguas; nombres de sesión `ID-hash-rol`; contrato de rutas para agentes |
| Bootstrap | `workspace.py`, `technical_context.initialize_constitution` | Scaffolding aditivo, constitución local neutral y migración legacy explícita |
| Configuración | `config.py` | Fusión global + `project.json`; resolución `defaults → fase → agente u operación` |
| Proveedores | `registry.py`, `providers.py` | Adaptadores Claude/Codex/Gemini, traducción de effort, verificación de flags y skills |
| Ejecución de procesos | `commands.py` | argv sin shell, timeout, límite de salida y de concurrencia por runner |
| Composición | `runtime.py` | Construye config, fábrica, runner, gateway, estado y servicios de un contexto |
| Flota interactiva | `cli.py`, `fleet.py`, `herdr.py` | 3 tabs y 13 paneles (12 sin UX); propiedad registrada en SQLite |
| Servicios | `services.py` | Spec Kit headless, despacho a paneles propios, resúmenes y plan de sesiones, verificación de mantenimiento |
| Contexto técnico | `technical_context.py` | Índice por rol/operación, descubrimiento acotado del stack y ensamblado del prompt |
| Estado | `state.py`, `watcher_service.py` | Registros JSON en SQLite, claims idempotentes, locks de SO, cursor y cola del tracker |
| Flujo BMAD/SDD | `workflow.py`, `ux_routing.py`, `gitops.py` | Interpretación del tracker, compuertas, fases SDD, retrabajo y macros GitOps |
| Nombres de HU | `hu_naming.py` | Contrato único `NNN-nombre-en-kebab-case.md` para watcher, GitOps, `approve_step.py` y dashboard; rechaza sin renombrar |
| Mantenimiento | `maintenance.py` | Cierre de tabs propios idle/done; VERIFY de identidad; CLEAR (Claude) y ROTATE confirmados por el operador, coordinados con el watcher |
| Presupuesto y bucles | `guard.py` | Eventos de progreso con calidad de métrica, presupuesto y loop guard; alertas `WARNING`/`PAUSE`/`REQUIRES_INTERVENTION`; en `enforce` retiene nuevos despachos; nunca limpia, rota ni reintenta |
| Dashboard | `bmad-control-center/` | Proyección de un workspace por proceso API: tracker, artefactos, gates, Git y eventos |

`watcher_bmad.py` reexporta `workflow` mediante `sys.modules`, por compatibilidad de imports.
El dashboard no consulta Herdr ni SQLite: lee el tracker, los archivos del perímetro y Git.

## 3. Estructura lógica de carpetas

```mermaid
flowchart LR
    subgraph E["ENGINE_ROOT (solo lectura para proyectos)"]
        E1["config_bmad.json<br/>global y registro projects"]
        E2["constitution.md<br/>política operativa"]
        E3["rol/AGENTS.md x15<br/>agents/, instructions/"]
        E4[".github/skills fuente<br/>.agents/skills Codex<br/>.claude/skills Claude"]
        E5[".specify/scripts<br/>.specify/templates"]
        E6["bmad_runtime/, utils/,<br/>ux_routing.py"]
        E7["bmad-control-center/"]
    end
    subgraph W["WORKSPACE_ROOT (todas las escrituras)"]
        W1["project.json<br/>identidad y overrides"]
        W2["AGENTS.md<br/>contrato de rutas"]
        W3["docs/rol/<br/>docs/architecture/"]
        W4["app/ o code_dirs"]
        W5["specs/README.md<br/>specs/XXX-nombre/"]
        W6[".specify/memory/constitution.md<br/>.specify/feature.json"]
        W7["handoffs/tracker_bmad.md"]
        W8["state/state.sqlite3<br/>state/*.lock<br/>state/config_bmad.json"]
        W9["logs/, temp/"]
    end
    E3 -.->|"perfil por ruta absoluta"| W2
    E4 -.->|"skill por ruta absoluta"| W5
    E5 -.->|"snapshot aditivo en init"| W6
    E1 -.->|"materialize_config"| W8
```

- Perfiles y skills se leen del motor por ruta absoluta; no se copian al workspace.
- `ProjectContext.validate()` rechaza un workspace igual al motor, que lo contenga o que se
  superponga con sus directorios compartidos.
- `state/config_bmad.json` es una vista generada; los orígenes editables son
  `config_bmad.json` del motor y `project.json`.
- En modo legacy (configuración sin registro `projects`) el tracker vive en `docs/` y el
  estado en `.bmad-runtime/`. El template incluye el registro, así que siempre exige selección.

## 4. Flujo de datos y persistencia

```mermaid
flowchart LR
    AG["Agente interactivo<br/>panel Herdr"] -->|"anexa bloque y Handoff"| TR[("handoffs/<br/>tracker_bmad.md")]
    AG -->|"escribe"| DOC[("docs/")]
    TR -->|"lectura cada ~2 s"| WT["Watcher<br/>workflow.py"]
    WT -->|"event, queued, tracker_cursor,<br/>followup"| SQL[("state/<br/>state.sqlite3")]
    WT -->|"AgentDispatcher.dispatch"| AG
    WT -->|"SpecKitExecutor.execute"| HL["CLI headless"]
    HL -->|"spec, plan, tasks, código"| SP[("specs/, .specify/,<br/>app o code_dirs")]
    HL -->|"run: estado"| SQL
    WT -->|"registros WATCHER"| TR
    WT -->|"freeze, ramas, merge"| GIT[("Git del workspace")]
    WT -->|"rework_state.json"| SP
    FL["FleetOrchestrator"] -->|"agent: y tab:"| SQL
    DASH["Dashboard backend"] -->|"lee"| TR
    DASH -->|"lee"| DOC
    DASH -->|"lee"| SP
    DASH -->|"decisión HUMANO"| TR
    DASH -->|"status, commits"| GIT
```

| Almacén | Contenido | Escritor |
|---|---|---|
| `handoffs/tracker_bmad.md` | Bus de handoffs: bloques `### [fecha] Autor` con artefacto, estado y línea `Handoff` | Agentes, watcher, scripts humanos, dashboard |
| `state/state.sqlite3`, tabla `records(id, data)` | `agent:`, `tab:`, `run:`, `dispatch:`, `event:`, `queued:`, `tracker_cursor`, `followup`, `session:`, `maintenance:`, `watcher`, `progress:`, `guard_alert:`, `guard_ack:`, `guard_artifacts`, `hu_lifecycle`, `hu_lifecycle:` (observación de HU, no autoritativa), `hu_authority`, `hu_op:`, `hu_resolution:` (Fase 4F-E4, solo con `enforce`) | Flota, servicios, watcher, mantenimiento, guard |
| `state/*.lock` | Locks de SO `bootstrap`, `fleet`, `watcher`, `speckit`, `maintenance`, `sessions` (el watcher lo toma en cada ciclo), `hu` (E4: apertura/cierre de HU, por proyecto) | `project_lock()`, `ProjectLock` |
| `.specify/memory/` | Constitución local, `rework_state.json`, `rework_last_classification.md` | Spec Kit, QT, watcher |
| `docs/`, `specs/`, `app/` | Entregables por rol, especificaciones y código | Agentes y CLIs headless |
| `logs/guard.log` | Alertas del guard (JSONL) cuando suben de nivel | `guard.py` |

SQLite guarda metadatos, no prompts ni credenciales. La cola persiste la referencia (línea,
hash y offsets) a la instrucción del tracker; al reanudar no se vuelve a extraer la línea, para
no repetir macros Git o fases SDD.

## 5. Ciclo de vida de un proyecto

El runtime no persiste un estado global del proyecto; el ciclo se deduce de artefactos,
registros y procesos en ejecución.

```mermaid
flowchart TD
    A["init_bmad.py --workspace --project"] --> B["Bootstrap aditivo:<br/>project.json, AGENTS.md, carpetas,<br/>tracker vacío, constitución neutral"]
    B --> C["Operador: project.json, constitución,<br/>tech-stack y Git propio"]
    C --> D["Dry-runs de flota y watcher<br/>sin procesos ni SQLite"]
    D --> E{"¿pending o rutas incorrectas?"}
    E -->|"Sí"| C
    E -->|"No"| F["start_agents.py: paneles en Herdr<br/>agent: starting, VERIFY y ready"]
    F --> G["watcher_bmad.py: lock watcher,<br/>verificación headless, cursor y cola"]
    G --> H["Idea en Business Storyteller"]
    H --> I["Ciclo BMAD/SDD por HU"]
    I --> J{"¿ReconciliationRequired<br/>o Ctrl+C?"}
    J -->|"No"| I
    J -->|"Sí"| K["Watcher detenido"]
    K --> L["Inspección: tracker, artefactos,<br/>bmad_runtime.state, paneles"]
    L --> M{"¿Sesiones válidas?"}
    M -->|"Sí"| G
    M -->|"No"| N["stop_agents.py --confirm<br/>cierra tabs propios idle/done"]
    N --> D
```

## 6. Flujo BMAD + SDD

BMAD reparte el trabajo en 15 roles y cuatro fases (B negocio, M gestión, A arquitectura,
D desarrollo, según `AGENT_PHASES`). SDD mantiene `spec.md`, `plan.md` y `tasks.md` por HU
mediante siete operaciones Spec Kit (`specify`, `clarify`, `plan`, `tasks`, `analyze`,
`converge`, `implement`) que el watcher ejecuta en modo headless.

```mermaid
flowchart TD
    BS["B · Business Storyteller<br/>idea-*.md"] --> PA["B · Product Analyst<br/>pb-*.md"]
    PA --> H1{{"HUMANO: aprueba<br/>Product Brief"}}
    H1 --> PM["M · Product Manager<br/>mvp-*.md, selección HU,<br/>GITOPS-BRANCH-CREATE"]
    PM --> BA["M · Business Analyst<br/>XXX-nombre.md"]
    BA --> QA{"M · QA Documental"}
    QA -->|"Feedback"| BA
    QA -->|"Aprobado"| SC["Watcher: specify y clarify"]
    SC --> H2{"¿Ambigüedad?"}
    H2 -->|"Sí"| H3{{"HUMANO: responde clarify"}}
    H3 --> SC
    H2 -->|"No"| UXD{"ux_routing:<br/>¿requiere UX?"}
    UXD -->|"Sí"| UX["A · Designer UX<br/>ux_*.md"]
    UXD -->|"No"| SA["A · Solutions Architect<br/>tech_guidelines.md"]
    UX --> SA
    SA -->|"@WATCHER: SDD-FREEZE"| FZ["Watcher: plan, tasks, analyze<br/>y commit de freeze"]
    FZ --> DA["A · Data Architect<br/>db_*.md"]
    DA --> API{"¿Contrato API?"}
    API -->|"Sí"| AA["A · API Architect<br/>api_*.md"]
    API -->|"No"| QT["A · QA Tech<br/>tech-design_*.md"]
    AA --> QT
    QT --> IMP["Watcher: implement<br/>backend y después frontend"]
    IMP --> QAA["D · QA Automation<br/>qa-report.md"]
    QAA --> CR{"D · Code Review"}
    CR -->|"Aprobado"| CL["GITOPS-MERGE-CLOSE<br/>siguiente HU"]
    CR -->|"Rechazo"| RW{"¿Iteración menor o igual a 2?"}
    QAA -->|"Rechazo"| RW
    RW -->|"Sí"| RE["Watcher: analyze, converge,<br/>implement"]
    RE --> QAA
    RW -->|"No"| H4{{"HUMANO: escalado"}}
```

Reglas de gobierno implementadas o exigidas por perfiles y watcher:

- **Vertical slicing:** una HU recorre el flujo completo antes de abrir la siguiente.
- **Identificador universal:** `XXX-nombre-en-kebab-case` se conserva en HU, carpeta
  `specs/XXX-nombre/`, rama `feat/XXX-nombre` y handoffs. El watcher fija
  `SPECIFY_FEATURE_DIRECTORY` y verifica `.specify/feature.json`; una divergencia detiene la fase.
  `bmad_runtime/hu_naming.py` valida el nombre en todos los consumidores (watcher, GitOps,
  `approve_step.py` y dashboard); un nombre inválido detiene solo el paso de esa HU, sin
  renombrar, sin carpeta elegida por Spec Kit y sin rama genérica.
- **Ledger:** `specs/README.md` con columnas `N° | Épica Origen | Nombre spec / HU | Qué aporta | Estado | Rama`.
- **UX:** `project_type=headless` o `ux_phase=off` omiten UX; `on` lo fuerza; `auto` lee
  `Requiere interfaz: Sí|No` en la HU y, si falta, diseña.
- **Implementación:** backend y frontend no tienen panel; Spec Kit `implement` monta sus perfiles
  como directiva y exige actualizar `docs/dev-backend/backend-architecture.md`,
  `docs/dev-frontend/frontend-architecture.md` y los README de cada `code_dirs`.
- **Retrabajo:** un rechazo de QA Automation o Code Review activa `analyze → converge → implement`
  sobre las tareas de corrección; tras dos iteraciones se escala al humano.
- **Cambio de stack:** no existe catálogo de stacks ni comando de sustitución. Se ajustan
  constitución local, guías y tareas del workspace.

## 7. Estados implementados

### Registro de agentes de la flota (`agent:<rol>`)

```mermaid
stateDiagram-v2
    [*] --> starting: fleet.launch registra panel
    starting --> ready: VERIFY inicial COMPLETED
    starting --> awaiting_trust: diálogo en pantalla al arrancar
    starting --> unverified: VERIFY inicial fallido o interrumpido
    starting --> uncertain: excepción al arrancar
    ready --> awaiting_trust: diálogo detectado antes de despachar
    ready --> maintenance: CLEAR o ROTATE QUIESCED
    ready --> unverified: --verify fallido
    maintenance --> ready: COMPLETED con generación + 1
    maintenance --> ready: FAILED, nada llegó al agente
    maintenance --> awaiting_trust: diálogo durante la operación
    awaiting_trust --> ready: --reconcile tras responder el humano
    unverified --> ready: --reconcile verificado
    maintenance --> ready: --reconcile de REQUIRES_INTERVENTION
    ready --> closed: stop_agents con tab idle/done
    uncertain --> [*]: reconciliación manual
    closed --> [*]
```

`HOLD_STATES` (`starting`, `awaiting_trust`, `unverified`, `maintenance`) retienen las tareas:
solo un registro `ready` recibe despachos, y solo si su panel, proveedor y modelo coinciden con
la selección vigente y su `agent_status` en Herdr es `idle` o `done`. VERIFY comprueba la
identidad de forma determinista (nombre de sesión, proveedor y modelo, panel, `cwd`, proceso y
contrato cargado) y después la respuesta del agente a una sonda `BMAD-VERIFICACION` (rol,
proyecto, workspace, digest del contrato y memoria). Ningún diálogo se responde de forma automática.

### Operaciones idempotentes (`event:`, `dispatch:`, `run:`)

```mermaid
stateDiagram-v2
    [*] --> in_flight: StateStore.claim
    in_flight --> done: éxito o entrega aceptada
    in_flight --> not_delivered: rechazo antes de enviar (dispatch)
    in_flight --> uncertain: excepción tras un posible envío
    in_flight --> fallo: run con quota, cli_error u otro error del runner
    not_delivered --> in_flight: nuevo claim, attempt + 1
    uncertain --> done: --acknowledge (event, dispatch) tras inspección
    in_flight --> done: --acknowledge (event, dispatch) si el proceso murió
    done --> [*]
    note right of in_flight
        Un claim sobre in_flight o uncertain
        lanza ReconciliationRequired: nunca se reintenta
    end note
```

`fallo` agrupa los valores de `provider.classify()` y del runner (`quota`, `cli_error`,
`cli_missing`, `native_executable_required`, `process_limit`, `spawn_failed`, entre otros).
No hay reintento automático: el workflow registra el error en el tracker y se detiene o pausa.
`--acknowledge` (`python -m bmad_runtime.state`) marca el registro como atendido y nunca lo repite.

### Handoff en cola (`queued:`) y confirmación

```mermaid
stateDiagram-v2
    [*] --> detectado: WatcherService.enqueue (state queued)
    detectado --> detectado: retenido (pausa, hold, seguimiento activo, agente ocupado)
    detectado --> reservado: agente ready e idle, sin seguimiento activo
    reservado --> despachado: entrega aceptada (state done)
    reservado --> fallido: diálogo antes de enviar o agente ausente
    fallido --> reservado: tras --reconcile o reinicio, sigue en cola
    reservado --> requiere_intervencion: entrega incierta
    despachado --> confirmado: bloque del agente en el tracker
    despachado --> requiere_intervencion: vigilante escala tras MAX_RECORDATORIOS
    confirmado --> [*]
    requiere_intervencion --> [*]: --acknowledge (y --release-followup)
```

El campo canónico `state` (`queued` o `done`) decide si la tarea sigue en cola; `stage` es
trazabilidad. Un despacho abre un seguimiento (`followup`) para el agente: mientras no aparezca
su bloque, ni la escalada del vigilante, el mismo agente no recibe otra tarea aunque Herdr lo
muestre `idle`, y la siguiente queda en `detectado`. El bloque confirmado registra el resumen
`session:<rol>`; un bloque de agente sin despacho es `protocol_violation:` y detiene los despachos.

### Watcher

```mermaid
stateDiagram-v2
    [*] --> Preparando: main y lock watcher
    Preparando --> Escuchando: ayuda headless verificada, cursor, cola y seguimientos restaurados
    Preparando --> Detenido: BMADRuntimeError
    Escuchando --> PausaMantenimiento: lock sessions tomado por maintenance
    PausaMantenimiento --> Escuchando: operación terminada
    Escuchando --> PausaHumana: último bloque con HUMANO pendiente
    PausaHumana --> Escuchando: bloque HUMANO o macro de cierre
    Escuchando --> Retenido: violación de protocolo sin reconciliar
    Retenido --> Escuchando: --acknowledge protocol_violation
    Escuchando --> EjecutandoSDD: aprobación QA, SDD-FREEZE, gatillo de implementación o rechazo
    EjecutandoSDD --> Escuchando: fase completada con handoff
    EjecutandoSDD --> Detenido: fase fallida
    Escuchando --> Detenido: Ctrl+C, tracker reescrito, agente sin propiedad, entrega incierta o conflicto de merge
    PausaHumana --> Detenido: Ctrl+C
    Detenido --> [*]
```

En cada ciclo (~2 s) el watcher toma el lock `sessions`, publica su latido (`watcher`, protocolo
`sessions-lock/1`) y lee solo líneas completas coherentes con el cursor. Además de las pausas
globales, cada tarea se retiene por agente: mantenimiento sin reconciliar, `HOLD_STATES`, alerta
del guard en modo `enforce`, seguimiento activo o agente ocupado en Herdr. La pausa humana no se
persiste: `is_tracker_paused_for_human()` la recalcula leyendo el último bloque con handoff. Una
detención por `ReconciliationRequired` sale con código 1 y exige inspección antes de reanudar.

### Una HU abierta por proyecto (Fase 4F-E4, `ai.hu_lifecycle.mode = enforce`)

Política: cada proyecto mantiene como máximo una HU abierta desde su `GITOPS-BRANCH-CREATE` autorizado
hasta que su `GITOPS-MERGE-CLOSE` se completa y Git lo verifica. Varios agentes trabajan sobre la HU
abierta; proyectos con repositorios independientes avanzan en paralelo (el lock `hu` está en el
directorio de estado de cada proyecto; no existe un bloqueo global). `observe` (por defecto) y `off`
conservan el comportamiento anterior. `enforce` solo se activa explícitamente: `ai.hu_lifecycle` del
motor o, para un proyecto aislado, `config.ai.hu_lifecycle` en su `project.json`.

```mermaid
stateDiagram-v2
    [*] --> free
    free --> opening: BRANCH-CREATE autorizado (reserva persistida antes de Git)
    opening --> active: rama verificada (existe y HEAD en ella)
    opening --> free: Git sin cambios (fallo o caída antes de Git)
    opening --> reconcile_required: Git cambió pero no se verifica
    active --> closing: MERGE-CLOSE autorizado tras la confirmación humana
    closing --> free: punta reservada integrada en la base (merge-base --is-ancestor)
    closing --> active: Git sin cambios (fallo o caída antes del merge)
    closing --> reconcile_required: conflicto, merge sin confirmar o evidencia dudosa
    reconcile_required --> free: reconciliación humana closed/abandoned con evidencia
    reconcile_required --> active: reconciliación humana active con evidencia
```

| Vista del proyecto | BRANCH-CREATE misma HU | BRANCH-CREATE otra HU |
| --- | --- | --- |
| `no_open_hu` | permitir (`HU_OPEN_ALLOWED`) | permitir |
| `one_open_hu` | reanudar sin abrir otra (`HU_OPEN_RESUME`) | rechazar (`HU_ANOTHER_OPEN`) |
| `opening` | reanudar | rechazar (`HU_OPENING_IN_PROGRESS`) |
| `closing` | rechazar (`HU_CLOSING_IN_PROGRESS`) | rechazar |
| `reconcile_required` / `unknown` | rechazar (`HU_RECONCILE_REQUIRED` / `HU_STATE_UNKNOWN`) | rechazar |

La vista combina la reserva `hu_authority` con la observación E3 en vivo; una reserva `active` que
Git no corrobora es `reconcile_required` y un fallo de observación es `unknown`, nunca "libre". El
watcher decide cada macro con el historial anterior a su línea. Secuencia autoritativa: lock `hu` →
revalidar Git, tracker y SQLite → reservar (`hu_op:<id>` estable por evento + `hu_authority`) →
ejecutar la macro → verificar Git → confirmar → liberar. La confirmación humana del cierre (`input`)
corre fuera del lock y la estrategia `--no-ff` no cambia.

Rechazo (corrección D5): la macro rechazada no ejecuta Git ni checkout, su evento termina `done` con
`outcome: rejected`, las tareas aún en cola de líneas anteriores del bloque se retiran y ninguna
línea posterior del mismo bloque se despacha (`outcome: suppressed`). Se emite un bloque `WATCHER`
con `@HUMANO:` (op_id `hu-notice-<id>`, idempotente), que además pausa el flujo. Las dependencias de
un bloque solo se despachan si su operación está `confirmed`: reconocer el evento (`state
--acknowledge`), reiniciar o una caída no las autorizan. Tras reiniciar, `recover()` resuelve una
reserva `opening`/`closing` interrumpida con evidencia Git (o la deja en `reconcile_required`), se
reemiten los avisos pendientes y la hidratación solo reactiva la HU abierta demostrada.

Repositorios compartidos (worktree enlazado o principal con worktrees enlazados, mismo
`git-common-dir`): sus ramas no se pueden atribuir a un proyecto y se rechaza con
`HU_SHARED_REPOSITORY`. Reconciliación humana: `python -m bmad_runtime.hu_enforcement --inspect` y
`--reconcile <HU> --as active|closed|abandoned --reason ... --confirm` (watcher detenido); se registra
en `hu_resolution:<HU>` ligada a la evidencia que resolvió, con autor, fecha e historial.

### Outbox de respuestas de agentes (Fase 4F-E5, `ai.outbox.mode`)

`direct` (por defecto) conserva el comportamiento anterior: el agente anexa su bloque al tracker.
`both` y `outbox` son opt-in (motor o `config.ai.outbox` del `project.json` de un proyecto aislado):
el despacho fija y persiste su canal; en canal outbox el agente publica un único archivo en
`<BMAD_HANDOFFS>/outbox/<event24>-<attempt>.md` entre marcas con la identidad del despacho y un
nonce, y el watcher es el único que lo escribe en el tracker con TrackerWriter (op_id
`outbox:<event_id>:<attempt>`). El canal pertenece al despacho: cambiar de modo y reiniciar no
reinterpreta despachos existentes, y un mismo despacho nunca acepta dos entregas.

```mermaid
stateDiagram-v2
    [*] --> expected: despacho persistido antes de enviar la tarea
    expected --> writing: archivo sin marca final
    writing --> ready: marca final con el nonce
    expected --> ready: publicación completa o rename atómico
    ready --> validating: contenido idéntico tras settle_seconds
    validating --> ingesting: identidad, rol, formato y macros válidos (intención persistida)
    ingesting --> confirmed: TrackerWriter done y bytes presentes; queued confirmado en la misma transacción
    validating --> rejected: inválido, rol o proyecto ajeno, macro no autorizada
    validating --> reconcile_required: despacho incierto, handoff reconocido o escalado, bloque directo
    ingesting --> reconcile_required: append incierto o perdido (nunca se repara solo)
    rejected --> [*]: reconocido por un humano (no entregado)
    reconcile_required --> rejected: --reject con el bloque ausente del tracker
```

Cada ciclo del watcher ingiere antes de leer el tracker: el bloque incorporado sigue el camino de
siempre (macros, enforce E4, extracción de handoffs, auditoría de protocolo). `audit_blocks` solo
acepta para un despacho outbox el bloque ingerido (`confirmed_block`); un bloque directo del agente
es una violación de protocolo. Rechazos e incertidumbres marcan el handoff `requiere_intervencion`,
emiten un bloque `WATCHER` con `@HUMANO:` y retienen los despachos hasta `python -m
bmad_runtime.outbox --acknowledge|--reject KEY --confirm`. El vigilante no confirma un despacho
outbox por un bloque del tracker: recuerda la ruta asignada y escala sin inventar respuesta.

Handoff humano (E5.1, ambos canales): bloque producido → incorporado y verificado → handoff confirmado
(técnico) → intervención humana pendiente → decisión humana recibida. La confirmación corre aunque el flujo
esté en pausa, pero la pausa solo la levanta un bloque humano posterior (`paused_for_human`); nada que
requiera aprobación se despacha antes. `python -m bmad_runtime.outbox --inspect` muestra los hitos, la
evidencia de cada entrega, los motivos de bloqueo y el procedimiento de recuperación.

Consistencia de configuración: el watcher persiste sus políticas efectivas (`watcher_policy`) y avisa
si su `--config` difiere de la configuración por defecto; `python -m bmad_runtime.outbox --status`
muestra las diferencias y el Control Center aplica `enforce` de HU si el watcher en ejecución lo usa.

### Mantenimiento supervisado (CLEAR, ROTATE y VERIFY)

```mermaid
stateDiagram-v2
    [*] --> REQUESTED: --clear, --rotate o --verify con --confirm, ELIGIBLE bajo Coordination
    REQUESTED --> QUIESCED: resumen y contrato fijados, agent en maintenance
    QUIESCED --> CLEARING: CLEAR (solo Claude Code), envía /clear
    QUIESCED --> STOPPING: ROTATE, envía /exit
    STOPPING --> STARTING: panel de vuelta en su shell
    CLEARING --> VERIFYING: mismo proceso listo e identidad determinista
    STARTING --> VERIFYING: relanzado en el mismo panel e identidad determinista
    REQUESTED --> VERIFYING: VERIFY
    VERIFYING --> COMPLETED: sonda verificada
    REQUESTED --> FAILED: interrumpido antes de enviar nada
    QUIESCED --> FAILED: interrumpido antes de enviar nada
    CLEARING --> FAILED: /clear rechazado antes de enviar
    STOPPING --> FAILED: /exit rechazado antes de enviar
    CLEARING --> REQUIRES_INTERVENTION: entrega incierta, diálogo o timeout
    STOPPING --> REQUIRES_INTERVENTION: /exit no confirmado
    STARTING --> REQUIRES_INTERVENTION: relanzamiento fallido o diálogo
    VERIFYING --> REQUIRES_INTERVENTION: sonda ausente o distinta
    REQUIRES_INTERVENTION --> Resuelta: --reconcile verifica el agente vivo
    COMPLETED --> [*]
    FAILED --> [*]
    Resuelta --> [*]
```

`Coordination` toma los locks `maintenance`, `watcher` (o exige un watcher con latido reciente),
`fleet` y `sessions`, y vuelve a evaluar la elegibilidad bajo exclusión. Una operación no final
bloquea al agente (`maintenance_blocks`) hasta `--reconcile`, que verifica el agente vivo, deja
`resolution` en la operación (que conserva su estado como evidencia) y nunca relanza ni reintenta.
`FAILED` significa verificado que nada llegó al agente: vuelve a `ready`. `--plan-clear` es de
solo lectura.

### Generaciones de sesión

```mermaid
stateDiagram-v2
    state "Lanzamiento (run_id nuevo)" as L
    [*] --> L: start_agents
    L --> G1: generación 1
    G1 --> Gn: CLEAR o ROTATE COMPLETED (+1)
    Gn --> Gn: CLEAR o ROTATE COMPLETED (+1)
    G1 --> G1: VERIFY o --reconcile con contexto previo
    Gn --> Gn: VERIFY o --reconcile con contexto previo
    Gn --> L: nueva flota tras stop_agents
```

Una sesión es la pareja `run_id` + `generation` del registro `agent:<rol>`. Cada despacho guarda
la sesión que lo recibió; el plan considera una sesión ya renovada si un CLEAR o ROTATE terminó
después de su último handoff confirmado (`session_already_fresh`). `--reconcile` de un CLEAR o
ROTATE interrumpido solo suma una generación cuando la sonda demuestra contexto vacío.

### Context Budget y Loop Guard

```mermaid
flowchart LR
    EV["Eventos del watcher<br/>dispatched, handoff_confirmed,<br/>artifacts_changed, no_progress,<br/>errores, permission_blocked,<br/>delivery_uncertain, headless_run"] --> L[("progress: en SQLite<br/>retención retention_days")]
    L --> E["Guard.evaluate con eventos nuevos o cada 30 s<br/>ventana window_seconds"]
    E --> R1["Bucles: instrucción repetida,<br/>ciclo de handoffs, error repetido,<br/>sin avance, aclaración repetida"]
    E --> R2["Presupuesto: intentos, duración,<br/>operaciones seguidas y por sesión,<br/>uso medido por el proveedor"]
    R1 & R2 --> A["guard_alert:regla:agente<br/>WARNING, PAUSE, REQUIRES_INTERVENTION"]
    A --> LOG["Consola y logs/guard.log<br/>solo cuando sube de nivel"]
    A --> M{"modo"}
    M -->|"observe (por defecto)"| NADA["Solo informa"]
    M -->|"enforce y PAUSE o superior"| HOLD["Retiene nuevos despachos<br/>a los agentes implicados"]
    A --> ACK["guard --acknowledge regla:agente --confirm<br/>guard_ack: la evidencia previa deja de contar"]
    R2 --> REC{"operations_per_session alcanzado<br/>y agente ELIGIBLE en el plan"}
    REC -->|"Sí"| ANN["guard_recommendation: anuncia una vez<br/>el comando CLEAR o ROTATE exacto"]
    ANN --> OPR(["Operador decide y ejecuta<br/>maintenance --confirm"])
```

Cada métrica lleva su calidad: `measured`, `estimated` o `unavailable`. Las sesiones
interactivas no reportan tokens: el uso nunca dispara recomendaciones, y un límite de uso solo se
acepta si el proveedor mide esa métrica. El guard nunca limpia, rota, reintenta, responde diálogos
ni interrumpe una operación activa; `guard --status` y `--calibrate` son de solo lectura.

## 8. Secuencias

### Inicio de proyecto, agentes y persistencia

```mermaid
sequenceDiagram
    actor OP as Operador
    participant I as init_bmad.py
    participant L as start_agents.py
    participant RT as Runtime
    participant H as Herdr
    participant W as watcher_bmad.py
    participant T as Tracker
    participant S as SQLite
    participant SK as CLI headless
    OP->>I: --workspace RUTA --project ID
    I->>I: resolve_context y lock bootstrap
    I-->>OP: scaffolding y state/config_bmad.json
    OP->>L: misma selección
    L->>RT: Runtime persistente
    RT->>RT: validar selecciones de 15 roles y 7 operaciones
    L->>S: tab: y agent: starting
    L->>H: create_tab, split, rename, sonda pwsh, agent start
    L->>H: VERIFY: identidad y sonda BMAD-VERIFICACION
    L->>S: agent: ready (o awaiting_trust / unverified)
    OP->>W: misma selección en otra terminal
    W->>SK: verificar ayuda headless por proveedor
    W->>S: restaurar cursor y cola
    OP->>H: idea en el panel business-storyteller
    H->>T: bloque con Handoff @PA:
    loop cada ~2 s
        W->>T: leer líneas nuevas
        W->>S: claim event: y enqueue queued:
        W->>H: agent prompt al panel propio idle sin seguimiento activo
        W->>S: dispatch: done, queued: done y followup
    end
    W->>SK: operación Spec Kit según la fase
    SK->>S: run: done o estado de fallo
    W->>T: registro WATCHER y siguiente handoff
```

### Handoff entre agentes con aprobación humana

```mermaid
sequenceDiagram
    participant A as Agente origen
    participant T as Tracker
    participant W as Watcher
    participant S as SQLite
    participant B as Agente destino
    actor OP as Operador
    A->>T: bloque con Handoff @HUMANO
    W->>T: is_tracker_paused_for_human
    Note over W: la cola no se despacha durante la pausa
    OP->>T: approve_step.py, response_sa.py o POST /gates/ID/decision
    Note over T: bloque HUMANO con Handoff al destino
    W->>T: nueva línea con token @DESTINO
    W->>S: claim event: y enqueue queued:
    W->>B: contrato de rutas, contexto del rol y mensaje
    W->>S: dispatch: done
    B->>T: nuevo bloque y Handoff
```

Un único token de destinatario por derivación. En un handoff al humano, los demás agentes se
nombran sin `@TOKEN:` para no disparar despachos. Las macros `@WATCHER: GITOPS-BRANCH-CREATE`,
`@WATCHER: SDD-FREEZE` y `@WATCHER: GITOPS-MERGE-CLOSE` van en líneas independientes antes del
handoff. El cierre de rama pide además escribir el nombre de la rama en la consola del watcher.

### Mantenimiento supervisado de una sesión

```mermaid
sequenceDiagram
    actor OP as Operador
    participant G as Guard (watcher)
    participant M as maintenance
    participant W as Watcher
    participant S as SQLite
    participant H as Herdr
    participant A as Agente
    G-->>OP: recomendación CLEAR o ROTATE con el comando exacto
    OP->>M: --plan-clear (solo lectura)
    M->>S: plan: ELIGIBLE o motivos
    OP->>M: --clear ROL o --rotate ROL con --confirm
    M->>M: locks maintenance, watcher o latido, fleet
    M->>S: espera el lock sessions
    Note over W: el ciclo queda en pausa sin leer ni despachar
    M->>S: replanifica bajo exclusión, maintenance: REQUESTED y QUIESCED
    alt CLEAR (solo Claude Code)
        M->>A: /clear
    else ROTATE
        M->>A: /exit y espera la shell del panel
        M->>H: agent start en el mismo panel
    end
    M->>H: identidad determinista
    M->>A: [BMAD-MANT id] sonda de verificación
    A-->>M: BMAD-VERIFICACION rol, proyecto, workspace, fuentes, memoria
    M->>S: COMPLETED, agent: ready y generación + 1 en una transacción
    M->>S: libera locks
    Note over W: el siguiente ciclo continúa
```

Cualquier fallo antes de enviar deja `FAILED` y el agente `ready`; tras un envío deja
`REQUIRES_INTERVENTION`, retiene al agente y exige `--reconcile ROL --confirm`.

### Recuperación tras fallos

```mermaid
flowchart TD
    F{"Síntoma"} --> T["Tracker reescrito o truncado<br/>tracker_integrity"]
    F --> D["Entrega incierta o evento in_flight<br/>dispatch: o event:"]
    F --> P["Bloque sin despacho<br/>protocol_violation:"]
    F --> Q["Tarea sin bloque tras escalar<br/>queued: requiere_intervencion"]
    F --> MT["Mantenimiento no final<br/>o agente retenido"]
    F --> GA["Alerta del guard"]
    F --> CR["Caída del proceso watcher"]
    T --> T1["Restaurar el tracker o<br/>state --rebaseline-tracker --confirm"]
    D --> D1["Inspeccionar panel y artefactos,<br/>state --acknowledge ID --confirm"]
    P --> P1["state --acknowledge protocol_violation:N --confirm"]
    Q --> Q1["state --acknowledge queued:ID --confirm<br/>y --release-followup ROL --confirm"]
    MT --> M1["maintenance --reconcile ROL --confirm"]
    GA --> G1["guard --acknowledge regla:agente --confirm"]
    CR --> C1["Los locks de SO se liberan solos,<br/>al reiniciar se restauran cursor, cola y seguimientos"]
    T1 & D1 & P1 & Q1 & M1 & G1 & C1 --> R["Reiniciar el watcher<br/>(con la misma --config)"]
```

Ningún comando de recuperación repite una operación: marcan la evidencia como atendida o
verifican el estado vivo. Los comandos `state` exigen el watcher detenido (toman su lock). Un
conflicto en `GITOPS-MERGE-CLOSE` aborta el merge, escribe en el tracker el comando exacto para
reconciliar su evento y detiene el watcher; reiniciar sin reconciliar vuelve a detenerlo.

### Consulta del dashboard

```mermaid
sequenceDiagram
    actor OP as Operador
    participant UI as Frontend Nuxt
    participant API as Backend FastAPI
    participant FW as FileWatcher watchdog
    participant FS as Workspace
    participant G as Git del workspace
    OP->>UI: abrir consola
    UI->>API: GET /api/v1/project y /api/v1/projects
    alt backend sin BMAD_WORKSPACE ni BMAD_PROJECT
        API-->>UI: proyecto nulo y registro
        Note over API: otras rutas 409 y WebSocket cerrado con 1008
    else backend con proyecto
        UI->>API: GET workflow/status, artifacts/tree, git/status
        API->>FS: leer tracker y archivos del perímetro
        API->>G: comandos Git de lectura
        UI->>API: WebSocket /ws/v1/events
        FS-->>FW: evento de sistema de archivos
        FW->>API: debounce de 200 ms
        API-->>UI: WORKFLOW_UPDATED, ARTIFACT_CHANGED, GIT_STATUS_CHANGED
        OP->>UI: decisión en una compuerta
        UI->>API: POST /api/v1/gates/ID/decision
        API->>FS: anexar bloque HUMANO al tracker
        API-->>UI: WORKFLOW_UPDATED
    end
```

El backend observa `docs`, `specs`, `.specify`, `handoffs` y `.git` con watchdog. El
frontend usa REST para la carga inicial y el WebSocket para actualizaciones; el latido
PING/PONG mantiene la conexión. Las decisiones del dashboard llegan al watcher solo a través
del tracker.

### Resolución de contexto

```mermaid
sequenceDiagram
    participant C as Consumidor
    participant CTX as ProjectContext
    participant TC as technical_context.assemble
    participant P as ENGINE_ROOT/constitution.md
    participant WS as Workspace
    C->>CTX: instructions
    CTX-->>C: contrato de rutas y variables BMAD_*
    C->>TC: assemble con rol u operación
    TC->>P: ruta y texto si ocupa 7000 caracteres o menos
    TC->>WS: document_index
    Note over TC,WS: constitución local siempre, y para roles técnicos tech-stack.md, architecture.md, tech_guidelines.md, guías, roles y ADRs existentes
    TC->>WS: constitución local completa si ocupa 6000 caracteres o menos
    opt rol técnico u operación plan, tasks, analyze, converge o implement
        TC->>WS: discover manifests acotado
        TC-->>TC: observaciones y diferencias con tech-stack.md
    end
    TC-->>C: índice y TAREA ACTUAL con límite de 24000 caracteres
```

| Consumidor | Composición del prompt |
|---|---|
| Arranque del panel (`interactive_command`) | contrato de rutas + `assemble(role, compact=True)`: solo rutas de política y documentos, hasta 8 observaciones |
| Despacho (`AgentDispatcher.dispatch`) | contrato + `assemble(role)` completo + mensaje del tracker |
| Spec Kit (`SpecKitExecutor.prepare`) | `assemble(operation)` + contrato + ruta absoluta de la skill `speckit-<operación>` + argumentos |

El encabezado fija la precedencia: política operativa del motor para aislamiento y seguridad;
constitución local para restricciones técnicas; ADR aprobado para decisiones particulares. Una
propuesta, un plan o una dependencia observada no equivalen a aprobación. Las guías largas se
enlazan para lectura bajo demanda. `discover()` no ejecuta scripts, omite secretos, enlaces y
workspaces anidados, y limita a 512 000 bytes por archivo, 2 000 directorios y 300 observaciones.

## 9. Orquestación

Un proceso watcher fija sus rutas globales al workspace con `configure_project()`; no cambia de
proyecto en caliente. Cada proyecto necesita su propio launcher, watcher y backend de dashboard.

### Ejemplo 1: un proyecto activo

Nombres ficticios: proyecto `agenda-citas`, workspace `D:\Proyectos\Agenda`.

```mermaid
flowchart LR
    OP(["Operador"]) -->|"--project agenda-citas"| REG["config_bmad.json<br/>projects.agenda-citas"]
    REG --> CTX["ProjectContext<br/>agenda-citas"]
    CTX --> L["start_agents.py"]
    CTX --> W["watcher_bmad.py"]
    L -->|"3 tabs agenda-citas-hash-*"| H["Herdr"]
    H --> P1["Paneles BS, PA, PM, BA, QA, UX"]
    H --> P2["Paneles SA, DA, API, QT"]
    H --> P3["Paneles QA-AUTO, CODE-REVIEW, DEVOPS"]
    W -->|"despacho"| H
    W -->|"recomendaciones"| OP
    OP -->|"maintenance --confirm"| MNT["maintenance<br/>--project agenda-citas"]
    MNT -->|"lock sessions: pausa el ciclo"| W
    MNT -->|"/clear, /exit, agent start"| H
    W -->|"Spec Kit headless"| SK["CLI headless"]
    P1 & P2 & P3 --> T[("Agenda/handoffs/tracker_bmad.md")]
    T --> W
    SK --> A[("Agenda/specs, app")]
    W --> S[("Agenda/state/state.sqlite3")]
    D["Backend :8000<br/>BMAD_PROJECT=agenda-citas"] --> T
    UI["Frontend :3000"] --> D
```

### Ejemplo 2: dos proyectos simultáneos

Nombres ficticios: `agenda-citas` y `inventario`, registrados en el mismo motor.

```mermaid
flowchart TB
    subgraph Motor["ENGINE_ROOT compartido: código, perfiles, skills, config global"]
        RA["Proceso launcher A<br/>Proceso watcher A<br/>maintenance A bajo demanda"]
        RB["Proceso launcher B<br/>Proceso watcher B<br/>maintenance B bajo demanda"]
        DA["Backend :8001<br/>BMAD_PROJECT=agenda-citas"]
        DB["Backend :8002<br/>BMAD_PROJECT=inventario"]
    end
    subgraph HerdrSrv["Herdr: un servidor"]
        HA["Tabs y paneles<br/>agenda-citas-hashA-rol"]
        HB["Tabs y paneles<br/>inventario-hashB-rol"]
    end
    subgraph WA["Workspace A"]
        TA[("tracker A")]
        SA[("state A: SQLite, locks,<br/>agent:, maintenance:, guard_*")]
        AA[("docs, specs, app, logs A<br/>logs/guard.log")]
        GA[("Git A")]
    end
    subgraph WB["Workspace B"]
        TB[("tracker B")]
        SB[("state B: SQLite, locks,<br/>agent:, maintenance:, guard_*")]
        AB[("docs, specs, app, logs B<br/>logs/guard.log")]
        GB[("Git B")]
    end
    RA --> HA
    RB --> HB
    RA --> TA & SA & AA & GA
    RB --> TB & SB & AB & GB
    HA --> TA
    HB --> TB
    DA --> TA & AA
    DB --> TB & AB
    UA["Frontend :3001<br/>VITE_BMAD_API_BASE=:8001"] --> DA
    UB["Frontend :3002<br/>VITE_BMAD_API_BASE=:8002"] --> DB
```

Mecanismos contra la contaminación cruzada:

- **Rutas:** `ProjectContext.output()` resuelve cada escritura dentro del workspace y rechaza
  escapes; los procesos hijos reciben `cwd` y variables `BMAD_*` del proyecto, y `CommandRunner`
  elimina variables heredadas de feature/Git.
- **Sesiones:** los nombres incluyen ID y hash de la ruta normalizada; el launcher rechaza nombres
  existentes y el despacho exige propiedad registrada en el SQLite del proyecto.
- **Estado:** SQLite, cursor, cola y locks viven en `state/` de cada workspace. Un segundo
  watcher sobre el mismo workspace falla al tomar el lock; sobre otro workspace no compite.
- **Git:** `GitService` exige `.git` local en el workspace y rechaza un repositorio padre.
- **Sesiones y guard:** generaciones, operaciones de mantenimiento, alertas y recomendaciones viven
  en el SQLite del workspace; los locks `maintenance` y `sessions` coordinan solo procesos del
  mismo proyecto. Los comandos recomendados incluyen `--workspace`, `--project` y la `--config`
  del watcher; `stop_agents.py --config` resuelve el proyecto con ese mismo archivo y rechaza un
  `project.json` que no coincida.
- **Dashboard:** cada backend fija un proyecto al importarse; HTTP, WebSocket, observadores y
  cachés pertenecen a ese proceso.

Limitaciones actuales:

- No existe orquestador central ni selector global: la simultaneidad consiste en procesos
  independientes por proyecto, que el operador arranca y supervisa por separado.
- El dashboard no agrega proyectos: la portada lista el registro (`/projects`), pero cada
  supervisión requiere un backend y un frontend propios; `VITE_BMAD_API_BASE` se fija al
  arrancar o compilar el frontend.
- `ai.limits.max_processes` limita cada `CommandRunner`, no el total de la máquina.
- El aislamiento de dos workspaces está verificado con dobles (`tests/test_multiworkspace.py`,
  `tests/validate_offline.py`); no hay prueba automatizada de dos flotas reales en un mismo
  Herdr ni de cuota compartida entre proveedores.

## 10. Límites de seguridad y operación

- El perímetro de rutas es una regla del runtime y del contrato inyectado, no un sandbox del
  sistema operativo: un CLI externo puede ejecutar acciones arbitrarias según sus permisos.
- En Windows, `CommandRunner` exige ejecutables nativos y rechaza `.cmd`, `.bat` y `.ps1`.
- Gemini, una skill instalada distinta de `.github/skills`, una configuración inválida o un CLI
  ausente producen errores explícitos; no hay fallback de proveedor.
- `idle`/`done` en Herdr o la aceptación de un prompt no prueban que el agente terminó: cuentan
  el artefacto y el handoff.
- No hay limpieza ni rotación automática de contexto: `/clear` (solo Claude Code) y la rotación
  son operaciones confirmadas por el operador ([SETUP.md](SETUP.md#ciclo-de-vida-de-sesiones)).
- Un agente solo recibe tareas en estado `ready`, tras una verificación (arranque, recuperación,
  CLEAR, ROTATE). El watcher es el único despachador: un bloque de agente sin despacho detiene los
  despachos hasta reconciliar. Los diálogos de confianza nunca se responden automáticamente
  ([SETUP.md](SETUP.md#arranque-y-entrega-en-herdr)).
- `ai.git.auto_commit=false` desactiva el autosave; el freeze y las macros GitOps siguen creando
  commits, ramas y merges. El freeze exige staging vacío y añade solo `specs/` y `.specify/`.
- `Runtime` cachea la configuración: un cambio requiere reiniciar los procesos afectados.
- Un despacho abre un seguimiento por agente: hasta su bloque en el tracker (o la escalada del
  vigilante) ese agente no recibe otra tarea, aunque Herdr lo muestre `idle`.

### Deuda técnica conocida

- **Outbox (E5/E5.1) sin piloto real:** el protocolo está verificado con dobles de Claude, Codex y Herdr;
  falta comprobar en vivo que cada CLI publica el archivo con sus herramientas de edición y respeta las
  marcas. Las sesiones headless de Spec Kit siguen sin canal outbox: un bloque suyo (`DEV-BACK`/`DEV-FRONT`)
  se audita (`blocked_write:`) y no ejecuta ni despacha nada; con una macro, además, pausa con `@HUMANO:`.
  Un bloque con autor del motor (`WATCHER`, `Senior … Developer`) cuya cabecera no está en el journal de
  TrackerWriter se trata igual. Las líneas sin cabecera anexadas a un bloque ajeno siguen sin atribución.
  En modo `direct`, un agente interactivo aún puede emitir una macro que su contrato no le asigna: los
  contratos ya no la ordenan (prueba de contratos), pero solo el canal outbox lo rechaza.

- **Ventana entre consulta y despacho:** el watcher lee el estado del agente en Herdr
  (`obtener_info_agente`) y `AgentDispatcher.dispatch` lo vuelve a consultar antes de enviar. Si
  el agente cambia de estado entre ambas lecturas, el despacho lanza `ReconciliationRequired` y el
  watcher se detiene sin enviar nada (fallo seguro, sin duplicados); la tarea sigue en cola al
  reiniciar. No hay bloqueo atómico con Herdr.
- **Harness de pruebas:** `tests/run_isolated.py` conserva a propósito cada directorio temporal
  bajo `.test-tmp/` (ignorado por Git) para sortear las ACL heredadas de Windows; crece con cada
  ejecución y se limpia a mano. Las pruebas que usan el modo legacy emiten `FutureWarning` por no
  seleccionar workspace, y el backend arrastra un aviso de deprecación de `httpx` en
  `starlette.testclient`.
- **Fin de línea:** el repositorio no tiene `.gitattributes`; con `core.autocrlf=true`, Git avisa
  de conversiones LF a CRLF en archivos editados con LF.
