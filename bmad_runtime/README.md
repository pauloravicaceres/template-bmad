# Contrato operativo del runtime BMAD

Contrato por módulo del paquete `bmad_runtime`: funciones, consumidores, efectos y CLI. La instalación, configuración, proveedores y effort están en [SETUP.md](../SETUP.md); la operación en [GUIDE.md](../GUIDE.md); los diagramas de componentes, estados y secuencias en [ARCHITECTURE.md](../ARCHITECTURE.md).

## Inventario de programas y módulos Python

La mayoría de los módulos del paquete son bibliotecas internas: se importan desde scripts públicos o desde otros módulos, sin ejecutar un programa independiente. Para operar el motor utiliza las entradas públicas de la siguiente tabla; las secciones por archivo explican sus funciones, consumidores y efectos.

| Entrada pública | Módulo y función que invoca | Finalidad |
|---|---|---|
| [init_bmad.py](../init_bmad.py) | `workspace.main(['init', ...])` | Inicializar un workspace explícito |
| [utils/manage_workspace.py](../utils/manage_workspace.py) | `workspace.main()` | Inicializar o inventariar/migrar datos legacy |
| [utils/start_agents.py](../utils/start_agents.py) | `cli.launcher_main()` → `FleetOrchestrator` | Revisar o lanzar la flota interactiva |
| [watcher_bmad.py](../watcher_bmad.py) | `workflow.main()` | Revisar operaciones SpecKit, escuchar tracker o compilar perfiles explícitamente |
| [utils/stop_agents.py](../utils/stop_agents.py) | `maintenance.stop_main()` | Cerrar tabs propios verificados e inactivos |
| `python -m bmad_runtime.state` | `state.main()` | Inspeccionar y reconocer eventos del estado persistido |
| `python -m bmad_runtime.maintenance --plan-clear` | `maintenance.main()` → `SessionManager.plan()` | Informe de solo lectura sobre qué sesiones podrían limpiarse o rotarse; no modifica sesiones |
| `python -m bmad_runtime.maintenance --clear/--rotate/--reconcile ROL --confirm` | `maintenance.main()` → `SessionMaintenance` | CLEAR (solo Claude Code), ROTATE o reconciliación confirmados por el operador de un agente propio |
| [utils/approve_step.py](../utils/approve_step.py) y [utils/response_sa.py](../utils/response_sa.py) | `context.resolve_context()` | Resolver el proyecto al registrar aprobaciones o respuestas humanas |
| [backend/core/config.py](../bmad-control-center/backend/core/config.py) | `context.resolve_context()` y `config.effective_config()` | Fijar proyecto y configuración del dashboard al importar su aplicación |

`watcher_bmad.py` también conserva compatibilidad de imports: cuando se importa, expone el módulo `workflow` mediante `sys.modules`. Por eso pruebas y consumidores que importan funciones desde `watcher_bmad` siguen utilizando la implementación de `workflow.py`.

### Índice por archivo

| Archivo | Responsabilidad | Consumidor principal |
|---|---|---|
| [__init__.py](__init__.py) | Identificar el paquete | Sistema de imports de Python |
| [context.py](context.py) | Identidad, selección y perímetro de rutas | Runtime, bootstrap, CLI auxiliares y dashboard |
| [config.py](config.py) | Configuración efectiva, validación y selección IA | Runtime, ProviderFactory, bootstrap y dashboard |
| [registry.py](registry.py) | Registro e instanciación de adaptadores | Runtime y providers |
| [providers.py](providers.py) | Contratos nativos de Claude/Codex/Gemini | Factory, flota y servicios |
| [commands.py](commands.py) | Ejecución acotada de procesos externos | Runtime, proveedores, Herdr y GitOps |
| [runtime.py](runtime.py) | Construcción de dependencias de una ejecución | CLI, workflow y maintenance |
| [cli.py](cli.py) | Launcher y preparación de dry-runs SpecKit | start_agents y workflow |
| [fleet.py](fleet.py) | Distribución y arranque de paneles | cli.launcher_main |
| [herdr.py](herdr.py) | Traducción al CLI de Herdr | Flota, despacho, watcher y parada |
| [pane_state.py](pane_state.py) | Clasificación fail-closed de la pantalla de un panel y exclusión por panel antes de escribir | services (despacho), maintenance y providers |
| [services.py](services.py) | SpecKit, despacho y gestión de contexto | Runtime, flota y workflow |
| [state.py](state.py) | SQLite, deduplicación y locks | Runtime, servicios, watcher, bootstrap y parada |
| [watcher_service.py](watcher_service.py) | Cursor y cola persistida del tracker; protocolo de coordinación con el mantenimiento | workflow, services y maintenance |
| [tracker_io.py](tracker_io.py) | Única vía de escritura Python al tracker: lock de proyecto, journal SQLite y verificación | workflow, Control Center, approve_step y response_sa |
| [workflow.py](workflow.py) | Reglas BMAD/SDD y bucle del watcher | watcher_bmad |
| [hu_naming.py](hu_naming.py) | Contrato único del identificador de HU (`NNN-nombre-en-kebab-case`) | workflow, approve_step y dashboard |
| [artifacts.py](artifacts.py) | Clasificación de solo lectura del artefacto citado por una compuerta (PRESENT…AMBIGUOUS) | Control Center, approve_step y config |
| [hu_lifecycle.py](hu_lifecycle.py) | Ciclo de vida observado (no autoritativo) de las HU por proyecto: Git + tracker + SQLite | workflow (watcher), hu_enforcement, config y CLI de consulta |
| [hu_enforcement.py](hu_enforcement.py) | Una HU abierta por proyecto en modo `enforce`: reserva, autorización, rechazo y reconciliación | workflow (watcher), Control Center y CLI de reconciliación |
| [outbox.py](outbox.py) | Outbox durable de respuestas de agentes (opt-in): entrega esperada por despacho, validación, ingesta con TrackerWriter y reconciliación | services (despacho), workflow (watcher), config y CLI |
| [policy_audit.py](policy_audit.py) | Políticas efectivas del watcher en ejecución y diferencias con la configuración por defecto | workflow (watcher), Control Center y CLI del outbox |
| [gitops.py](gitops.py) | Ejecución Git y freeze de especificaciones | workflow |
| [technical_context.py](technical_context.py) | Constitución local, índice técnico, descubrimiento y ensamblado de contexto | services, workspace y dashboard |
| [workspace.py](workspace.py) | Bootstrap y migración aditiva | init_bmad y manage_workspace |
| [maintenance.py](maintenance.py) | Cierre de tabs propios y CLEAR/ROTATE supervisados con coordinación del watcher | stop_agents y operador |
| [guard.py](guard.py) | Presupuesto de contexto, loop guard y registro de progreso; recomienda, no actúa | Runtime, workflow, SpecKitExecutor y operador |
| [errors.py](errors.py) | Excepciones comunes del runtime | Módulos del paquete y sus entradas públicas |

### `__init__.py`: identidad del paquete

Contiene únicamente la descripción del paquete. Python lo carga al importar `bmad_runtime` o sus submódulos. No registra proveedores, construye un Runtime, inicia procesos ni escribe archivos. No tiene CLI ni función de arranque.

### `context.py`: selección de proyecto y rutas

`ProjectContext` reúne `engine_root`, `workspace_root`, `project_id` y la marca `legacy`. `resolve_context()` elige el proyecto por argumentos CLI, entorno o registro global; lee la identidad y comprueba coincidencias, existencia y acceso. `add_project_arguments()` incorpora `--workspace` y `--project` a los parsers.

- **Quién lo invoca:** `Runtime`, `workspace.main`, `workflow.main`, `maintenance.stop_main`, `state.main`, auxiliares humanos y configuración del dashboard. `config.py` reutiliza `read_json()` y `absolute_path()`.
- **Cómo funciona:** `output()` resuelve destinos dentro del workspace y rechaza escapes; `validate()` comprueba superposición con el motor, enlaces y acceso; `session_name()` incorpora ID/hash/rol. `environment()` genera rutas y variables para procesos hijos; `instructions()` genera el contrato multiworkspace usado en `AGENTS.md` y prompts.
- **Efectos:** lectura y validación; no crea el workspace, modifica identidad ni cambia variables globales del entorno por sí solo. No ofrece una CLI propia.

### `config.py`: configuración efectiva y selección IA

Define `Selection`, el mapa `AGENT_PHASES` de los 15 roles y `OPERATIONS` de las siete operaciones SpecKit. `RuntimeConfig.load()` carga y valida el esquema, proveedores, límites y Git; `resolve()` calcula una selección para exactamente un agente u operación.

- **Quién lo invoca:** `Runtime`, `ProviderFactory`, `workspace.bootstrap` y configuración del dashboard. Flota y servicios consumen sus mapas y selecciones.
- **Cómo funciona:** `effective_config()` combina el origen global con overrides permitidos de `project.json`; `merge_config()` aplica herencia y descarte de modelo/opciones al cambiar proveedor. La traducción de flags nativos pertenece a `providers.py`.
- **Efectos:** la carga/selección lee archivos sin ejecutar CLIs. `materialize_config()` sí escribe la vista `state/config_bmad.json`, mediante temporal y reemplazo, con rutas de tracker, memoria y documentos del contexto. Bootstrap y Runtime persistente la invocan; dashboard solo lee configuración efectiva. No tiene CLI propia.

### `registry.py`: registro y fábrica de proveedores

`ProviderRegistry.register()` asocia un identificador a una clase adaptadora, rechazando duplicados. `create()` instancia el adaptador con su ejecutable. `ProviderFactory.resolve()` obtiene la selección de `RuntimeConfig`, busca el ejecutable configurado, crea el adaptador y valida las opciones.

- **Quién lo invoca:** `providers.default_registry()` registra adaptadores; `Runtime` crea la fábrica; flota y servicios resuelven agentes/operaciones mediante ella.
- **Entradas y resultado:** configuración, registro y destino → pareja `(Selection, provider)`. Un proveedor desconocido o no configurado produce `ConfigurationError`; no elige otro automáticamente.
- **Efectos:** objetos en memoria, sin procesos ni escrituras. Runtime acepta un registro inyectado, utilizado también por pruebas; no hay descubrimiento automático de plugins ni CLI del registro.

### `providers.py`: adaptadores nativos de IA

Define `AIProvider`, `Capabilities`, `ClaudeProvider`, `CodexProvider`, `GeminiProvider` y `default_registry()`. Este último registra los tres identificadores; estar registrado no significa tener ejecución disponible.

- **Quién lo invoca:** `ProviderFactory` valida selecciones; `FleetOrchestrator` y `services` construyen/verifican comandos y clasifican resultados; el vigilante del workflow consulta `limit_state()`.
- **Cómo funciona:** `interactive()` y `headless()` construyen objetos `Command` con los flags nativos; `validate()` comprueba opciones y effort; `verify()` ejecuta ayuda mediante el runner y exige flags. `skill()` coteja identidad y todos los recursos instalados contra `.github/skills`; `classify()` interpreta código de salida, errores y cuota.
- **Efectos:** construir comandos no lanza agentes. Verificar ejecuta ayuda; la ejecución del comando preparado ocurre desde flota/servicios. Se leen perfiles y skills; no se instalan ni sincronizan. Claude y Codex tienen ejecución; Gemini devuelve capacidad pendiente. `clear_context` está deshabilitado en los adaptadores actuales.

### `commands.py`: ejecución y límites de procesos

`Command` describe argv, cwd, stdin, entorno y posiciones sensibles; `sanitized()` oculta estas posiciones para mostrar comandos. `Result` contiene salida, retorno y error; `require_success()` convierte fallos en `CommandError`. `CommandRunner` ejecuta sin shell y aplica límites de tiempo, salida y concurrencia.

- **Quién lo invoca:** `Runtime` crea el runner; proveedores, `HerdrGateway`, `SpecKitExecutor` y `GitService` lo usan para ejecutar comandos.
- **Cómo funciona:** valida argumentos y variables admitidas, resuelve ejecutable, rechaza wrappers en Windows y alimenta stdin/lee stdout y stderr con threads. En contexto multiworkspace elimina variables heredadas de feature/Git que podrían redirigir la operación y aplica el entorno explícito del proyecto.
- **Efectos:** crea procesos externos; en Windows usa `CREATE_NO_WINDOW`. Si exceden límites, termina el proceso y sus descendientes por PID, no por nombre. Los límites pertenecen a ese runner, no a todas las instancias del motor. No tiene CLI independiente ni escribe un archivo de log automáticamente.

### `runtime.py`: construcción de una ejecución

`Runtime` es el punto donde se conectan contexto, configuración, registro/fábrica, runner, gateway Herdr, estado, SpecKit, dispatcher y administrador de sesiones. Valida todas las selecciones de agentes y operaciones antes de crear paneles o ejecutar trabajo.

- **Quién lo invoca:** launcher y `spec_plan()` de `cli.py`, watcher de `workflow.py` y parada de `maintenance.py`; las pruebas también lo construyen con dobles.
- **Cómo funciona:** acepta contexto o selección de proyecto y dependencias inyectadas (`registry`, `runner`, `gateway`). Expone `context`, `config`, `factory`, `runner`, `gateway`, `state`, `spec`, `dispatcher` y `sessions` para sus consumidores.
- **Efectos:** con `persist=True` refresca la vista efectiva y abre/crea SQLite. Con `persist=False` omite ambas escrituras y deja `state=None`, adecuado para preparación de dry-runs, no para ejecutar servicios que necesitan estado. Construirlo no lanza flota ni inicia watcher. `close()` cierra SQLite; no detiene agentes ni procesos de Herdr.

### `cli.py`: launcher y dry-run de SpecKit

`launcher_main(root, argv)` implementa el parser usado por `utils/start_agents.py`. Acepta `--workspace`, `--project`, `--config` y `--dry-run`; construye Runtime y llama a `FleetOrchestrator.plan()` o `launch()`.

- **Quién lo invoca:** `utils/start_agents.py`; `workflow.main()` importa `spec_plan()` para `watcher_bmad.py --dry-run`.
- **Cómo funciona:** `spec_plan()` recorre las siete operaciones y prepara comandos sanitizados con proveedor, modelo, cwd y tracker. Una capacidad no disponible queda `pending` con motivo. No ejecuta operaciones.
- **Efectos:** los dry-runs imprimen JSON sin procesos ni persistencia. El launcher real delega creación de paneles a flota y devuelve el número iniciado. Cierra Runtime al finalizar; los errores BMAD del launcher producen retorno 1. `cli.py` no tiene bloque de ejecución propio: usa los scripts públicos.

### `fleet.py`: distribución y arranque de paneles

`TABS_CONFIG` define tres tabs: Negocio y Producto, Arquitectura e Ingeniería, Desarrollo y Despliegue. `FleetOrchestrator.plan()` calcula los 13 paneles, o 12 si `ux_routing` omite UX. Los perfiles de backend/frontend se utilizan headless, no como paneles de esta flota.

- **Quién lo invoca:** `cli.launcher_main()`; `utils/start_agents.py` también importa `TABS_CONFIG`.
- **Cómo funciona:** `plan()` resuelve selección por rol y comandos sin ejecutarlos. `launch()` toma lock `fleet`, comprueba capacidades/ayuda, verifica ejecutables Herdr y rechaza nombres existentes. Crea tabs/splits, renombra paneles y arranca agentes con contexto del proyecto.
- **Efectos:** llamadas reales a Herdr y registros `tab:`/`agent:` en SQLite, con run_id, panel, proveedor, modelo y estado starting/ready/uncertain. Un fallo parcial conserva evidencia y puede dejar tabs creados; no hay rollback automático ni cierre de sesiones anteriores.

### `herdr.py`: gateway del CLI de Herdr

`HerdrGateway` concentra los verbos de Herdr y sus respuestas. Proporciona listas de agentes/tabs/panes, creación y cierre de tabs, splits, rename/focus, arranque, envío de prompts y lectura de paneles.

- **Quién lo invoca:** Runtime lo construye; flota gestiona paneles; `AgentDispatcher` envía trabajo; watcher lee paneles; maintenance lista/cierra tabs.
- **Cómo funciona:** `_json()` exige un envelope sin error y con `result`; `verify_provider()` comprueba el kind y que el ejecutable canónico coincida con el configurado. `start_command()` adapta un comando del proveedor a `herdr agent start`; `prompt()` usa `agent prompt` para evitar escribir trabajo en una shell si el agente murió.
- **Efectos:** construcción de comandos sin ejecución o, al usar sus métodos operativos, llamadas externas que leen/modifican la sesión Herdr. No instala Herdr, abre su aplicación ni decide por sí solo si un panel pertenece al proyecto: esa validación vive en servicios y maintenance.

### `pane_state.py`: pantalla del panel antes de escribir

Fase 4F-E5.2.1. Herdr 0.8.2 informa `idle` mientras el CLI muestra un diálogo, y las teclas escritas lo responden: en el piloto E5.2 un dígito de la sonda de VERIFY eligió una opción del menú de confianza de Codex 0.162 (un `1` o un Enter habrían aceptado la confianza). `classify(perfil, pantalla, herdr_status=)` devuelve `READY_VERIFIED`, `AWAITING_TRUST`, `AWAITING_PERMISSION`, `AWAITING_SELECTION`, `BUSY`, `UNKNOWN` o `EXITED`.

- **Quién lo invoca:** `AgentDispatcher` (tareas y recordatorios), `SessionMaintenance` (VERIFY, CLEAR, ROTATE, `--reconcile`, arranque de la flota) y `interaction_blocker()` de los proveedores.
- **Cómo funciona:** normaliza la lectura `--source visible` (sin secuencias ANSI/OSC, controles ni marcos; NFKC y minúsculas). Los diálogos se reconocen por varias formulaciones y por su forma (cabeceras de confianza en las últimas 24 líneas; permisos, pistas de menú, cursor sobre opción, menú numerado sin compositor debajo o `y/n` en las últimas 10). `READY_VERIFIED` exige evidencia positiva del compositor vacío del perfil (`screen_profile` `claude`: `❯`/`>` con pie de modo o atajos; `codex`: `›`/`▌` con pie `context left`/atajos), sin nada salvo el pie debajo. La ausencia de un diálogo conocido nunca es `READY_VERIFIED`: una pantalla vacía, parcial o desconocida es `UNKNOWN`. `PaneGate.observe()` añade el proceso en primer plano (`process_info`: CLI esperado `alive`, solo la shell `EXITED`, otro o sin datos `UNKNOWN`) y dos lecturas que deben coincidir. `PaneGate.exclusive()` serializa a los escritores del runtime con el lock de SO `state/pane-<id>.lock`. `require_shell()` admite teclear comandos de shell (sonda de `pwsh`, `agent start`) solo con la shell en primer plano.
- **Efectos:** solo lee el panel y crea locks. Nunca escribe en un panel ni responde diálogos; quien escribe (despacho, mantenimiento) lo hace solo tras `READY_VERIFIED` bajo el lock del panel. Riesgo residual: Herdr no ofrece «enviar solo si la pantalla sigue igual»; entre la última lectura y `agent prompt` puede aparecer un diálogo. La ventana se reduce a una lectura y una llamada bajo lock, la sonda de VERIFY no lleva dígitos y el despacho vuelve a leer tras escribir (`AWAITING_TRUST`/`EXITED` después de la entrega la marca incierta y retiene al agente).

### `services.py`: SpecKit, despacho y sesiones

Reúne cuatro responsabilidades utilizadas por Runtime:

- **`interactive_command()`:** invocada por flota; adapta el comando del proveedor al cwd del workspace, perfil absoluto compartido, entorno y contrato de rutas. Prepara el comando sin ejecutarlo.
- **`SpecKitExecutor`:** `workflow.ejecutar_speckit()` llama a `execute()`; `cli.spec_plan()` usa `prepare()`. Valida skills, directiva y feature dentro del perímetro; construye el prompt headless. Ejecutar toma lock `speckit`, verifica ayuda, registra `run:` en SQLite, lanza el CLI y clasifica su resultado; interrupciones quedan uncertain. No reintenta automáticamente ni anexa handoffs: workflow decide cómo registrar/continuar.
- **`AgentDispatcher`:** workflow lo usa para consultar agentes y despachar tareas/recordatorios. Comprueba registro ready, identidad/pane, proveedor/modelo y estado idle/done; deduplica por `dispatch:` y antepone el contrato de rutas al prompt. El archivo de tarea referencia la política global incluida en el contrato del agente en lugar de copiarla; contrato de rutas, constitución local, observaciones y regla del tracker siguen en cada tarea. La aceptación del prompt se registra done; no equivale a terminar el trabajo del agente. `pane_ready()` (Fase 4F-E5.2.1) comprueba el panel antes de reservar `dispatch:` y otra vez bajo el lock del panel justo antes de escribir: un diálogo retiene al agente en `awaiting_trust` y un CLI terminado en `unverified` (`AgentBlocked`, nada enviado); una pantalla ocupada o ambigua lanza `PaneNotReady` (la tarea sigue en cola) y, tras `unready_limit` comprobaciones seguidas, también retiene. El motivo queda en `agent:<rol>.screen_check`.
- **`SessionManager`:** `record_summary()` guarda `session:<agente>` al confirmar un handoff; `plan()` evalúa elegibilidad en solo lectura (incluye mantenimientos pendientes, generación y sesión ya renovada). No limpia ni rota: `workflow.limpiar_sesiones_agentes()` solo sugiere el plan al cerrar una HU. `probe_text()`/`probe_verdict()` construyen y evalúan la verificación de mantenimiento; `clear_supported()` limita CLEAR a Claude Code.

No ofrece una CLI propia. Sus efectos reales dependen del método: preparar solo lee, ejecutar/despachar usa procesos y estado.

### `state.py`: SQLite, deduplicación y locks

`StateStore` guarda objetos JSON en la tabla `records(id, data)` de `state/state.sqlite3` del workspace, o `.bmad-runtime/state.sqlite3` en legacy. `get()`/`put()` leen/escriben; `claim()` registra una operación in_flight una sola vez; `finish()` actualiza el estado; `fingerprint()` calcula identificadores deterministas.

- **Quién lo invoca:** Runtime abre el almacén; flota, servicios, WatcherService y workflow registran propiedad, operaciones, cursor, cola y seguimiento. `workspace` y maintenance usan `project_lock()` incluso sin abrir SQLite.
- **Cómo funciona:** una operación ya done no vuelve a reclamarse; otra incompleta requiere reconciliación. `project_lock()` y `ProjectLock` (adquisición no bloqueante reutilizable por ciclo) usan bloqueo del sistema operativo (`msvcrt` en Windows, `fcntl` en POSIX); `put_many()` escribe varios registros en una transacción. El archivo `.lock` puede permanecer tras liberar el bloqueo; su existencia no prueba una operación activa. Estado y tracker son fuentes distintas: SQLite guarda metadatos, no los prompts completos.
- **CLI y efectos:** `python -m bmad_runtime.state` toma locks watcher/fleet/speckit/tracker, abre/crea SQLite y muestra registros no done. `--acknowledge ID --confirm` admite IDs event/dispatch/queued/protocol_violation existentes y los marca done (cerrados, nunca repetidos; conserva `acknowledged_state`); no reintenta ni acredita entrega. Con IDs `tracker_append:` solo registra la revisión humana: no cambia el estado de entrega ni desbloquea. `--reconcile`, `--authorize-reissue` y `--accept-loss` (`tracker_append:ID --confirm`) son la reconciliación explícita de `tracker_io`. No debe ejecutarse mientras esos locks estén ocupados.

### `tracker_io.py`: escritura segura del tracker

`TrackerWriter` es la única vía por la que el watcher, el Control Center, `utils/approve_step.py` y `utils/response_sa.py` anexan al tracker. Los agentes CLI todavía lo editan directamente.

- **Cómo funciona:** `locked()` toma `state/tracker.lock` (o `.bmad-runtime/tracker.lock` en legacy) con espera acotada por `ai.tracker.lock_timeout_seconds` (5 s por defecto); vencida, `TrackerBusy` sin escribir. `append()` registra `tracker_append:<op_id>` in_flight con offset, longitud y SHA-256 del contenido exacto, escribe el bloque completo terminado en salto con `fsync`, lo relee y lo marca done. El mismo `op_id` es idempotente. `precondition` aborta con `TrackerConflict` si el estado leído ya no vale (otra decisión humana).
- **Recuperación:** tras una caída, un in_flight se busca desde su offset: completo → done; truncado al final → uncertain; ausente → not_written (el mismo op_id puede reintentarse). Cada escritura y cada ciclo del watcher comprueban las 200 escrituras recientes; un bloque ausente más allá de la gracia (`rewrite_grace_seconds` en el watcher) queda lost. Uncertain/lost producen `TrackerIntegrityError` y detienen escrituras y despachos hasta una resolución explícita. Nada se reescribe ni re-anexa automáticamente.
- **Reconciliación (E1.1):** `state` (entrega) y la gestión humana son campos distintos. `done` solo se fija con evidencia: el replay de un op_id done exige que sus bytes sigan en el tracker (si no, pasa a lost). `--acknowledge` añade `acknowledged`/`acknowledged_state` sin tocar `state`. `--reconcile` relee el tracker bajo lock: copia completa → done (`resolution: verified_present`); fragmento final → uncertain; nada → lost. Solo una pérdida reconocida y verificada ausente admite `--authorize-reissue` (el productor reescribe ese op_id una vez → `reissued`; si la copia original reaparece antes, es la entrega y no se escribe otra) o `--accept-loss` (cierra la incidencia; el op_id no se reemite). `history` conserva cada transición y la evidencia sustituida. Un uncertain con fragmento no se resuelve hasta que el fragmento desaparece. `delivered(op_id)` = done y presente; lo usan el Control Center (replay) y la alerta MERGE-CLOSE.
- **Efectos:** escribe el tracker y metadatos (digests, nunca texto) en SQLite. El lock solo cubre lectura/decisión/anexo local; nunca llamadas a proveedores, Herdr, red ni la revisión humana (approve_step usa precondición optimista).

### `watcher_service.py`: cursor y cola del tracker

`WatcherService` conecta la lectura del tracker con `StateStore`. Lo instancia `workflow.iniciar_watcher()`; no es un segundo watcher ni ejecuta su propio bucle.

- **Cómo funciona:** `read_lines()` devuelve líneas no vacías, o una lista vacía si falta tracker. `begin_line()`/`complete_line()` deduplican eventos; `save_cursor()`/`restore_cursor()` guardan cantidad y hash del prefijo. `enqueue()` persiste destinatario y segmento de la línea original; `pending_tasks()` reconstruye pendientes comprobando su hash; `dispatched()` las marca terminadas.
- **Efectos:** lee tracker y escribe metadatos en SQLite; no anexa documentos/handoffs, ejecuta SpecKit ni habla con Herdr. Ante historial alterado o una línea pendiente modificada exige reconciliación. Al recuperar cola reconstruye instrucciones de despacho, sin volver a extraerlas para evitar repetir macros Git/SDD.

### `workflow.py`: coordinador BMAD/SDD y watcher

Es la implementación del flujo de negocio. `watcher_bmad.py` invoca `main()`, que resuelve contexto, prepara el dry-run o toma lock `watcher` y configura un Runtime persistente. `configure_project()` fija las rutas globales de ese proceso al workspace; no existe selección en caliente entre proyectos dentro del mismo watcher.

| Función o grupo | Para qué sirve | Quién lo llama dentro del flujo |
|---|---|---|
| `iniciar_watcher()` | Verificar operaciones headless, recuperar rama/cursor/cola/seguimiento y revisar tracker aproximadamente cada 2 segundos | `main()` |
| `actualizar_contexto_bloque()`, `buscar_bloque_tracker()` | Asociar línea, autor y bloque del tracker | Bucle y extracción de instrucciones |
| `is_tracker_paused_for_human()` | Detectar la compuerta humana vigente | Extracción, cola y vigilante |
| `extraer_instrucciones()` | Interpretar tokens, respuestas clarify, aprobaciones QA, SDD-FREEZE y gatillos de implementación/retrabajo | Procesamiento de eventos del bucle |
| `ejecutar_sdd_fase_negocio()` | specify/clarify, comprobar carpeta de HU y derivar a UX o SA | Intercepción de aprobación documental |
| `decidir_ruta_ux()`, `registrar_traspaso_fase_a()` | Consultar `ux_routing.py` y registrar la transición | Negocio y respuesta humana a clarify |
| `ejecutar_sdd_fase_arquitectura()` | plan/tasks/analyze, freeze y handoff a DA | Macro SDD-FREEZE |
| `ejecutar_sdd_fase_implementacion()` | Implementación por capas y comprobación de arquitecturas/README antes de revisión | Gatillo de arquitectura o SpecKit, y retrabajo |
| `ejecutar_sdd_retrabajo()` | analyze/converge/implement tras rechazo, con máximo dos iteraciones | Handoff de revisores hacia desarrollo |
| `ejecutar_speckit()` | Delegar operación a `runtime().spec` y registrar errores | Funciones SDD |
| `registrar_seguimiento()`, `vigilar_agentes_inactivos()` | Detectar falta de registro, leer cuota y enviar recordatorios o escalar; mientras el seguimiento de un agente está activo, el bucle retiene sus siguientes tareas | Despacho y bucle cuando no hay pausa humana |
| `comando_reconciliar_evento()` | Orden exacta `bmad_runtime.state --acknowledge event:... --confirm` del proyecto, usada en la alerta de conflicto de `gitops_merge_close()` | Recuperación de macros GitOps |
| `macro_gitops()`, `gitops_branch_create()`, `gitops_merge_close()` | Reconocer macros independientes y gestionar rama/cierre | Procesamiento de nuevas líneas |
| `hydration_gitops()` | Buscar apertura de rama aún no cerrada en el tracker | Arranque del watcher |
| `compilar_agentes_modulares()` | Reconstruir perfiles compartidos desde fuentes, instrucciones y skills | Solo `main()` con `--compile-profiles` |

**Efectos de operación:** anexa registros al tracker, persiste estado, despacha prompts y ejecuta SpecKit/Git. Retrabajo conserva datos en `.specify/memory/rework_state.json` y `rework_last_classification.md`; implementación puede crear directivas temporales dentro del workspace. Las escrituras de código/documentos las realiza el CLI headless y el workflow comprueba sus entregas. Los fallos requieren inspección del trabajo parcial, no un borrado de historial.

**Efectos de GitOps:** creación/reanudación de ramas `feat/NNN-nombre-en-kebab-case` (otro nombre se rechaza sin crear rama) y freeze; cierre solicita al operador escribir el nombre de rama, luego merge y borrado de la rama fusionada. Árbol sucio con auto_commit deshabilitado detiene el cambio; con autosave habilitado puede hacer add/commit. Cerrar una rama intenta limpiar contexto, pero la capacidad está deshabilitada actualmente.

**Funciones conservadas que no son un paso automático de arranque:** `guardar_historial()` y `validar_constitucion_gitops()` están definidas, pero no tienen llamadas internas actuales. La primera es una API legacy para autosave optativo; la segunda verifica la existencia de la constitución local sin añadir política global. Su existencia no significa que iniciar el watcher las ejecute.

**Mantenimiento explícito:** `--compile-profiles` escribe los `AGENTS.md` compartidos del motor y debe ejecutarse sin selección de proyecto; no es preparación habitual de cada workspace. `workflow.py` expone funciones y `main()`, pero no tiene bloque `__main__`: utiliza `watcher_bmad.py` como entrada pública.

### `hu_naming.py`: identificador universal de historias de usuario

Fuente única del nombre de HU: `NNN-nombre-en-kebab-case.md` (tres dígitos, guion, descripción en minúsculas ASCII con palabras separadas por un único guion). El identificador sin `.md` nombra la carpeta `specs/NNN-nombre/` y la rama `feat/NNN-nombre`. No hay compatibilidad con snake_case ni con `NNN-HU_nombre`.

- **Quién lo invoca:** `workflow.carpeta_spec_para_hu()`, la intercepción de aprobación QA y SDD-FREEZE de `extraer_instrucciones()`, `gitops_branch_create()`, `utils/approve_step.py` (opciones 3 y 4) y `POST /gates/{id}/decision` del dashboard.
- **Cómo funciona:** `is_hu_id()`, `is_hu_filename()` e `is_feature_branch()` validan; `find_hu_file()` y `hu_id_from_delegation()` reconocen nombres válidos en el tracker; `hu_name_error()` explica por qué un nombre se rechaza (numeración, separador, descripción vacía, espacios, guiones bajos, tildes, mayúsculas o caracteres especiales); `invalid_hu_reference()` y `last_hu_candidate()` localizan nombres con aspecto de HU para informar el rechazo en lugar de ignorarlo.
- **Efectos:** ninguno; funciones puras. Los consumidores detienen solo el paso de esa HU (sin specify, sin rama, sin aprobación) y nunca renombran archivos ni inventan identificadores. No tiene CLI propia.

### `artifacts.py`: clasificación de artefactos de compuerta

Clasificador determinista y de solo lectura (Fase 4F-E2) del artefacto que cita una aprobación, resuelto contra el workspace del proyecto, nunca contra el cwd.

- **Quién lo invoca:** `POST /gates/{id}/decision` del dashboard (dentro de la transacción del tracker, tras la verificación de replay), `utils/approve_step.py` y `RuntimeConfig` (`ai.artifacts`).
- **Estados:** `PRESENT` (archivo regular; vacío → advertencia), `MISSING` (ausente o no es archivo regular), `FUTURE` (ausente y una regla explícita dice que esa ruta exacta la crea la siguiente etapa; hoy solo la HU `docs/business-analyst/<id>.md` que delega el PM), `EXTERNAL_ALLOWED` (https con hostname exacto en la allowlist de la compuerta; por defecto solo `figma.com`/`www.figma.com` en designer-ux), `OUTSIDE` (escapes `..`, absolutas ajenas, UNC/dispositivo, unidad relativa, `:` de flujo alterno, enlaces que salen, otros esquemas, credenciales, puertos), `OTHER_PROJECT` (registro `projects` del motor o `project.json` más cercano, también anidado) y `AMBIGUOUS` (nombre suelto con varias coincidencias, o con una sin poder probar unicidad por la búsqueda acotada).
- **Cómo funciona:** `GATES` fija por compuerta autores, directorios y hosts; un nombre suelto se busca solo en esos directorios (orden alfabético, profundidad 6, 10 000 entradas, sin entrar en enlaces). La ruta registrada es relativa POSIX y canónica (`realpath`); un cambio entre `realpath` y `stat` clasifica `OUTSIDE`.
- **Política:** `ai.artifacts` opcional: `mode` `warn` (por defecto) u `off`, y `external_hosts` por compuerta; `enforce` se rechaza hasta autorizarlo. En `warn`, OUTSIDE/OTHER_PROJECT/AMBIGUOUS se rechazan y MISSING pasa con advertencias estructuradas (`ARTIFACT_MISSING`, `ARTIFACT_NOT_A_FILE`, `ARTIFACT_EMPTY`, `ARTIFACT_OUTSIDE_GATE_DIRS`, `ARTIFACT_SEARCH_TRUNCATED`).
- **Efectos:** ninguno: `stat`/`scandir`/`realpath` y lectura de `project.json`/registro; sin red ni escrituras. No tiene CLI propia.

### `hu_lifecycle.py`: ciclo de vida observado de las HU

Fase 4F-E3, modo OBSERVE. Estima por proyecto qué HU están abiertas sin cambiar el comportamiento del watcher, de GitOps ni del Control Center: no bloquea aperturas, no responde 409, no altera el despacho ni cierra HUs.

- **Fuentes:** Git (solo lectura: ramas `feat/NNN-nombre`, HEAD, merge/rebase en curso, merges en la base `dev`>`main`>`master` con sus padres); tracker (macros `@WATCHER: GITOPS-BRANCH-CREATE/MERGE-CLOSE`, mismo contrato que `workflow.macro_gitops` vía `gitops_macro()`); SQLite (registro `event:` de cada macro, `tracker_cursor`, alerta `tracker_append:gitops-conflict:*` y la observación anterior). Los documentos HU (`docs/business-analyst/<id>.md`, `specs/<id>/`) solo se informan: nunca prueban apertura ni cierre.
- **Estados por HU:** `unknown`, `opening` (macro pendiente o evento in_flight), `active` (evento done y rama presente), `closing` (cierre pendiente o en curso sin merge), `closed` (cierre ejecutado por el watcher y merge en la base; la rama puede seguir existiendo), `reconcile_required` (conflicto, merge externo, rama desaparecida, cierre interrumpido tras el merge o evidencia contradictoria). Cada observación lleva `observed_state`, `authoritative: false`, certeza (`high`/`medium`/`low`), causas y evidencia `git`/`tracker`/`sqlite`/`documents`. Un cambio de HEAD solo añade `head_elsewhere`; la evidencia parcial de merge nunca produce `closed`.
- **Estado del proyecto:** `no_open_hu` (Git y tracker legibles, ninguna HU abierta ni dudosa), `one_open_hu`, `reconcile_required` (alguna HU lo requiere o hay varias potencialmente abiertas, incluidas ramas sin rastro en el tracker y sin integrar) o `unknown` (sin repositorio propio, tracker inestable, HU desconocidas, operación Git no atribuible u observación fallida).
- **Persistencia:** `hu_lifecycle` (resumen) y `hu_lifecycle:<id>` en el SQLite del proyecto, con `fingerprint`, `observed_at`, `changed_at`, `previous_state` y `reason`. Solo se escribe lo que cambió: repetir la observación o reiniciar no añade ni reescribe registros. No toca `event:`, `queued:`, `dispatch:` ni `tracker_append:`. Sin migraciones.
- **Quién lo invoca:** `workflow.observar_ciclo_hu()` al iniciar el watcher (antes de la hidratación GitOps), tras completar una línea con macro GitOps y cuando esa macro falla o entra en conflicto (antes de propagar el error). Un fallo de observación se registra como `unknown` (`observation_failed:<tipo>`) y no altera el watcher. `RuntimeConfig` valida `ai.hu_lifecycle` (`mode`: `observe` por defecto, `off` o `enforce`; ver `hu_enforcement.py`). En E4 la observación excluye las macros que nunca se ejecutaron (rechazadas, suprimidas o con operación `failed`/`not_executed`) y aplica las reconciliaciones humanas `hu_resolution:<id>` mientras su evidencia no cambie.
- **Aislamiento:** cada proyecto observa su propio workspace y su SQLite. Git solo se consulta si `WORKSPACE_ROOT/.git` existe (con `GIT_CEILING_DIRECTORIES`, nunca un repositorio padre), con comandos de lectura (`rev-parse`, `symbolic-ref`, `for-each-ref`, `rev-list`, `log`) y `GIT_OPTIONAL_LOCKS=0`. Los worktrees comparten ramas: el id `repository` (digest del directorio común) los delata, una rama sin macros en este tracker se marca `shared_repository` y `--all` lista `shared_repository_with`.
- **CLI:** `python -m bmad_runtime.hu_lifecycle --status [--workspace W] [--project P] [--evidence]` o `--status --all` (proyectos del registro `projects`). Solo lectura: abre SQLite en modo `ro` (no lo crea si falta), no toma locks ni escribe; muestra el estado en vivo, el último registrado y `drift`. Sale con 1 si algún proyecto no pudo observarse.

### `hu_enforcement.py`: una HU abierta por proyecto

Fase 4F-E4. Solo actúa con `ai.hu_lifecycle.mode = enforce` (motor o `config.ai.hu_lifecycle` del `project.json` de un proyecto aislado); en `observe`/`off` el watcher y el Control Center se comportan como antes.

- **Regla:** como máximo una HU abierta por proyecto hasta completar y verificar su MERGE-CLOSE. `project_view()` combina la reserva `hu_authority` (`free`/`opening`/`active`/`closing`/`reconcile_required`) con la observación E3; `decide_open()`/`decide_close()` devuelven `Decision` con código estable (`HU_OPEN_ALLOWED`, `HU_OPEN_RESUME`, `HU_ANOTHER_OPEN`, `HU_OPENING_IN_PROGRESS`, `HU_CLOSING_IN_PROGRESS`, `HU_RECONCILE_REQUIRED`, `HU_STATE_UNKNOWN`, `HU_SHARED_REPOSITORY`, `HU_INVALID_BRANCH`, `HU_CLOSE_ALLOWED`, `HU_CLOSE_MISMATCH`, `HU_NOTHING_TO_CLOSE`).
- **Watcher (autoritativo):** `Enforcer.open()`/`close()` toman el lock `hu` del proyecto (espera acotada; nunca durante la confirmación humana), revalidan con el historial anterior a la línea, persisten la reserva (`hu_op:<id>` derivado del evento + `hu_authority`) antes de Git, ejecutan la macro existente, verifican Git (rama y HEAD; cierre = punta reservada ancestro de la base) y confirman. Un fallo sin cambios en Git restaura la reserva; con cambios o sin poder leer Git pasa a `reconcile_required`.
- **Rechazo:** operación `rejected`, evento `done` con `outcome: rejected`, tareas en cola de líneas anteriores del bloque retiradas, líneas posteriores del bloque `suppressed` (también tras reconocer el evento o reiniciar) y bloque `WATCHER` con `@HUMANO:` emitido con TrackerWriter (op_id `hu-notice-<id>`; si la escritura falla se reemite al arrancar).
- **Arranque:** `recover()` resuelve una reserva interrumpida con evidencia Git (rama presente → `active`; sin rama y sin punta previa → libre; cierre con la punta integrada → `reconcile_required`; nada cambió → `active`); `hydration_branch()` solo reactiva la HU abierta demostrada. Los eventos `in_flight` siguen exigiendo `state --acknowledge`.
- **Control Center:** `preflight()` aplica las mismas reglas en solo lectura (SQLite `ro`, Git de lectura); el endpoint de decisión responde 409 `HU_OPEN_CONFLICT` u 423 `HU_STATE_BLOCKED` (evidencia en `metadata.hu_lifecycle`) sin registrar nada; el watcher revalida siempre.
- **Fail-closed (E4.1):** excepción, timeout de Git, Git ausente, SQLite no consultable, tracker inestable o ilegible, `unknown`, `reconcile_required` o reserva que contradice a Git bloquean siempre la apertura (`HU_STATE_UNKNOWN`/`HU_RECONCILE_REQUIRED`), en el watcher y en el preflight. Además: una rama `feat/` con nombre fuera de contrato y trabajo sin integrar (`git.invalid_unmerged`) impide demostrar que el proyecto está libre (`unattributed_feature_branch:<rama>`); un evento E4 terminado o reconocido sin operación `confirmed` se observa `reconcile_required` (`open_unconfirmed`/`close_unconfirmed`), nunca `active`/`closed`; y un `project.json` presente pero ilegible hace fallar `load_policy()` (el Control Center responde 423) en vez de caer a la política del motor. En `observe` nada de esto bloquea.
- **Repositorios compartidos:** un worktree enlazado, o el principal con worktrees enlazados, se rechaza con `HU_SHARED_REPOSITORY`: no se puede demostrar el aislamiento entre proyectos.
- **CLI:** `python -m bmad_runtime.hu_enforcement [--workspace W] [--project P] --inspect` (solo lectura: vista, reserva, observación, operaciones, resoluciones y propuesta por HU) y `--reconcile <HU> --as active|closed|abandoned [--reason R] [--actor A] [--confirm]`. Sin `--confirm` es un dry-run; con él exige `--reason`, el watcher detenido y el lock `hu`. `closed` exige evidencia Git de integración (punta de la rama, o la punta reservada por el cierre, ancestro de la base; nunca mensajes, HEAD ni borrado de rama), `abandoned` que la rama ya no exista y `active` que exista sin integrar y no haya otra HU abierta. Registra `hu_resolution:<HU>` (evidencia, huella, motivo, autor, fecha, historial) y nunca crea ni elimina ramas ni toca el tracker.

### `outbox.py`: canal de salida durable de los agentes

Fase 4F-E5. `ai.outbox.mode` = `direct` (por defecto: los agentes escriben el tracker como antes), `both` (transición: solo los agentes de `ai.outbox.agents` usan el outbox) u `outbox` (todo agente interactivo). Se activa en la configuración del motor o, para un proyecto aislado, en `config.ai.outbox` de su `project.json`. Opciones: `max_bytes` (1024–1048576, por defecto 65536) y `settle_seconds` (0–60, por defecto 2).

- **Despacho:** `AgentDispatcher.dispatch()` fija y persiste el canal en `dispatch:<id>` (`channel`, `outbox`) cuando el modo no es `direct`. En canal outbox crea `outbox:<event_id>:<attempt>` (`expect()`: ruta `<BMAD_HANDOFFS>/outbox/<event24>-<attempt>.md`, agente, autores admitidos, proyecto, nonce, op_id `outbox:<event_id>:<attempt>`) antes de enviar nada, y el archivo de tarea lleva `task_rule()` en lugar de la regla del tracker. Si la entrega se rechaza (`not_delivered`) la expectativa se cierra en silencio; los recordatorios del vigilante conservan el canal y nunca abren otra.
- **Protocolo del archivo:** marca inicial `<!-- BMAD-OUTBOX v1 event_id=… attempt=… agent=… project=… nonce=… -->`, un único bloque tracker-logger y marca final `<!-- BMAD-OUTBOX-END nonce=… -->`. Sin la marca final el archivo está `writing`; con ella debe repetirse idéntico tras `settle_seconds`. Se admite publicar con `<archivo>.tmp` + rename; temporales y ocultos no se leen.
- **Estados:** `expected → writing → ready → validating → ingesting → confirmed`, o `rejected` / `reconcile_required`. Recibido, validado (intención con el bloque exacto persistida), incorporado (journal TrackerWriter `done` con bytes presentes) y confirmado (queued `confirmado` con `confirmed_block` + outbox `confirmed` en una transacción) son hitos distintos.
- **Validación:** lectura acotada sin seguir enlaces (lstat/O_NOFOLLOW, comprobación de inodo; junctions y symlinks rechazados, también en el directorio), UTF-8 estricto, sin caracteres de control, identidad del despacho persistido (proyecto, evento, intento, agente, nonce), cabecera `### [DD-MM-YYYY] <autor del rol>` sin `HUMANO`/`WATCHER`, un solo bloque, campo Hora y Handoff. Macros solo desde su rol de contrato (`MACRO_AUTHORITY`): `GITOPS-BRANCH-CREATE` product-manager, `GITOPS-MERGE-CLOSE` code-review, `SDD-FREEZE` solutions-architect, `/speckit.clarify` ningún agente; también en prosa. El enforce de HU (E4) sigue decidiendo después sobre el bloque ya incorporado.
- **Autorización:** solo un `dispatch` `done` del mismo agente, canal e intento; `uncertain`/`in_flight` → `reconcile_required`; handoff reconocido, ya confirmado, escalado o bloque directo del agente tras el despacho (ambos canales) → `reconcile_required`. Un archivo sin entrega esperada es `outbox_orphan:<id>` (`unknown_identity`, `wrong_channel` o `stale_attempt`).
- **Ingesta:** `OutboxIngestor.tick()` (lock `outbox` del proyecto; el watcher lo llama antes de leer el tracker) usa solo TrackerWriter con el op_id estable: idempotente, recupera una caída entre el tracker y SQLite sin duplicar y nunca repara un append incierto o perdido (`reconcile_required`; un incidente abierto de TrackerWriter detiene el watcher).
- **Incidencias:** rechazo o incertidumbre → handoff `requiere_intervencion`, bloque `WATCHER` con `@HUMANO:` (op_id `outbox-notice-<id>`, una vez) y retención de todos los despachos hasta resolver. Reconocer no entrega.
- **E5.1:** `@SPEC-KIT:` no lo emite ningún agente (QA Tech gatilla la Fase D con `@DEV-BACK:`/`@DEV-FRONT:`). `--inspect` (solo lectura) muestra por entrega la evidencia (archivo y si coincide con lo recibido, journal, bytes en el tracker, canal persistido), los hitos del handoff (`confirmed`, `human`: `not_requested`/`pending`/`decision_received`), hallazgos (`evidence_missing`, `evidence_changed_after_receipt`, `delivered_then_lost`, `acknowledged_not_delivered`, `current_policy_is_direct_channel_kept`) y el procedimiento de recuperación; `blockers()` explica por qué el watcher retiene despachos (outbox, violaciones, appends E1.1, integridad, mantenimiento, HU, escrituras bloqueadas, pausa humana). `publication_compatibility()` avisa de agentes outbox que no pueden publicar (Codex `read-only`, Claude `plan`/`manual`, proveedor no verificado) sin relajar permisos. No existe ingesta autorizada tras reconciliar.
- **CLI:** `python -m bmad_runtime.outbox [--workspace W] [--project P] [--config C] --status|--inspect` (solo lectura: entregas, categoría —pending_response, incomplete_file, received, ingesting, confirmed, invalid_file, wrong_role, foreign_or_unknown, duplicate_delivery, uncertain_delivery, no_response—, huérfanos, incidencias y diferencias de configuración); `--acknowledge KEY --confirm` (rechazo revisado; libera la retención, nunca entrega) y `--reject KEY --confirm` (cierra sin ingerir una entrega `reconcile_required` cuyo bloque no está en el tracker). Ambas exigen el watcher detenido. Nada se borra del outbox.

### `policy_audit.py`: configuración efectiva del watcher

Al arrancar, el watcher persiste `watcher_policy` (origen de `--config` y modos de `outbox`, `hu_lifecycle`, `artifacts` y `guard`) y avisa si difiere de la configuración por defecto. `divergence()` lo compara con la configuración local (CLI del outbox). El Control Center aplica `enforce` en su preflight de HU cuando un watcher con latido reciente declara `enforce` aunque su propia configuración diga otra cosa (nunca relaja un `enforce` propio).

### `gitops.py`: ejecución Git y freeze

`GitService` centraliza comandos Git sobre el cwd del Runtime. `workflow.run_git()` delega en `run()` y la fase de arquitectura utiliza `freeze()`.

- **Cómo funciona:** `run()` exige argv comenzando por git, rechaza flags force y comprueba que el workspace explícito tenga `.git` local; ejecuta mediante CommandRunner y el entorno del contexto. `freeze()` exige staging vacío, añade solo `specs/` y `.specify/` y crea el commit de freeze si hay cambios.
- **Efectos:** lecturas/mutaciones Git según comando y commit de especificaciones. No inicializa repositorios, decide la siguiente fase ni interpreta macros: esas decisiones están en workflow. Un staging ajeno no se mezcla con el freeze. No tiene CLI propia.

### `workspace.py`: inicialización y migración aditivas

`main()` es la CLI que usan `init_bmad.py` y `utils/manage_workspace.py`. También permite `python -m bmad_runtime.workspace` desde el motor. Acepta acción init/migrate, selección, config, confirm y dry-run; confirm y dry-run son excluyentes.

- **Bootstrap:** `bootstrap()` toma lock bootstrap, crea identidad, carpetas, tracker vacío si falta, contrato AGENTS.md, memoria y snapshots de scripts/plantillas SpecKit. `write_new()` abre archivos en modo exclusivo y conserva los existentes. La vista efectiva se materializa si falta.
- **Migración:** `migration_plan()` inventaría documentos, app, specs, memoria, feature y handoffs legacy; detecta conflictos y excluye Git/dependencias/estado activo. `migrate()` sin confirmación devuelve inventario; con confirmación toma locks bootstrap/watcher/fleet/speckit, copia sin sobrescribir, registra `logs/migration.json` e inicializa scaffolding.
- **Efectos:** init real y migración confirmada escriben exclusivamente en el destino seleccionado; no lanzan agentes ni inicializan Git. Init dry-run muestra entorno sin crear workspace; una migración interrumpida puede dejar archivos parciales y no tiene rollback automático.

### `maintenance.py`: cierre controlado de sesiones

Es código operativo necesario para `utils/stop_agents.py`, independiente de una eventual carpeta raíz `maintenance/`. `stop_main()` procesa selección, `--config` y `--confirm`; sin confirmación termina sin cerrar tabs. La misma `--config` resuelve el proyecto (registro `projects` y `project.json`) y construye el Runtime.

- **Quién lo invoca:** `utils/stop_agents.py` llama a `stop_main()`; este construye Runtime y llama a `close_owned_tabs()`. Las pruebas comprueban propiedad y separación de proyectos.
- **Cómo funciona:** toma locks maintenance/watcher/fleet y rechaza el cierre si hay un mantenimiento sin reconciliar; consulta agentes/panes/tabs de Herdr y contrasta cada miembro con registros de propiedad del proyecto. Solo permite idle/done. Valida todos los destinos antes de cerrar; tabs ocupados, vacíos o con miembros no verificables requieren reconciliación/manual.
- **Efectos:** con confirmación abre estado/refresca configuración, cierra tabs verificados y marca sus agentes closed. No detiene el watcher por sí solo, mata agentes ocupados, borra artefactos ni ofrece dry-run/config. Un fallo al cerrar puede requerir inspección de los tabs restantes.

`main()` (`python -m bmad_runtime.maintenance`) atiende el ciclo de vida de sesiones; `plan_main` es su alias anterior.

- **`--plan-clear` y operaciones sin `--confirm`:** solo lectura con `StateStore.open_readonly()`; sin locks, escrituras ni mensajes.
- **`Coordination`:** locks de SO `maintenance`, `watcher` (solo si no corre ninguno; si corre, exige su latido `sessions-lock/1` reciente), `fleet` y `sessions` (espera acotada a que termine el ciclo del watcher). Se liberan al salir o al morir el proceso.
- **`SessionMaintenance.run()`:** reevalúa elegibilidad e identidad bajo exclusión y ejecuta ROTATE (`REQUESTED → QUIESCED → STOPPING → STARTING → VERIFYING → COMPLETED`) o CLEAR (`… → CLEARING → VERIFYING → COMPLETED`), con `FAILED` (nada enviado) y `REQUIRES_INTERVENTION` (incierto). Persiste `maintenance:<op_id>` en cada transición; la generación sube solo tras la verificación, en la misma transacción que `COMPLETED`. No reintenta ni cambia de CLEAR a ROTATE.
- **`reconcile()`:** marca como interrumpida una operación no final (o crea un VERIFY para un agente retenido en `starting`/`awaiting_trust`/`unverified`), verifica el agente vivo y registra `resolution`; nunca relanza, reenvía comandos ni responde diálogos. Detalle operativo en [SETUP.md](../SETUP.md#ciclo-de-vida-de-sesiones).
- **`verify()` (`--verify`, arranque de la flota):** operación VERIFY sin cambio de contexto ni de generación. `identity()` reúne comprobaciones deterministas (Herdr, cwd, proceso y argv con el contrato, proveedor/modelo, generación del mismo `run_id`) antes de la respuesta del agente; `_require_ready()` (`pane_state`) exige `READY_VERIFIED` antes de la sonda, de `/clear`, de `/exit` y de `--reconcile`, y se repite bajo el lock del panel justo antes de escribir. Un diálogo deja `REQUIRES_INTERVENTION` y `awaiting_trust`; un CLI terminado, ocupado o una pantalla ambigua, `unverified`. La sonda `[BMAD-MANT <id>]` usa un id sin dígitos (`probe_nonce()`). Una decisión humana (p. ej. confianza concedida a mano) solo habilita una nueva verificación con `--reconcile`; `state --acknowledge` no acepta operaciones `maintenance:`.
- **`prepare_pane()` / `start_agent()`:** antes de arrancar Codex en un panel (flota o ROTATE), sondea qué `pwsh` resuelve su shell y aplica `PANE_PATH_REPAIR` solo a esa shell; rechaza si sigue en `WindowsApps`. `start_agent()` diagnostica como `AgentBlocked` un arranque fallido detrás de un diálogo.

### `guard.py`: presupuesto de contexto y loop guard

Observa el bucle del watcher; no es un segundo orquestador. `Runtime` crea `Guard` antes de escribir nada y rechaza límites de tokens o coste para proveedores que no reportan esa métrica (`measured_usage` vacío en Claude, Codex y Gemini).

- **Registro de progreso:** eventos `progress:<ns>:<id>` en SQLite (`dispatched`, `work_started`, `artifacts_changed`, `handoff_confirmed`, `task_completed`, `no_progress`, `recoverable_error`, `repeated_error`, `permission_blocked`, `delivery_uncertain`, `clarification_requested`, `headless_run`). Cada métrica lleva su calidad: `measured` (reloj del runtime, intentos), `estimated` (tamaño del archivo de tarea / 4, nunca consumo) o `unavailable` (tokens y coste). Solo un artefacto declarado y modificado durante la tarea (mtime y contenido distinto del último confirmado) cuenta como avance; una entrega `accepted` o un bloque confirmado no lo son.
- **Evaluación:** `evaluate()` recalcula las reglas solo desde SQLite (un reinicio llega al mismo veredicto): instrucción repetida, ciclo de handoffs, error repetido, turnos sin avance y aclaración repetida (señales combinadas que se reinician con avance verificado), bloqueo por permisos, entrega incierta, intentos, duración de la operación activa, operaciones consecutivas, tareas por sesión (generación) y consumo medido. Niveles `NORMAL`, `WARNING`, `PAUSE`, `REQUIRES_INTERVENTION`.
- **Actuación:** `tick()` persiste el veredicto en `guard_alert:<regla>:<agente>` y anuncia solo subidas de nivel (consola y `logs/guard.log`, nunca el tracker). En `enforce`, `hold()` retiene nuevos despachos a los agentes implicados ante `PAUSE`/`REQUIRES_INTERVENTION`; en `observe` (predeterminado) solo alerta. Nunca interrumpe una operación activa, reintenta, limpia ni rota.
- **CLI:** `python -m bmad_runtime.guard --workspace W` es un informe de solo lectura; `--acknowledge REGLA:AGENTE --confirm` registra `guard_ack:`: los eventos anteriores a la revisión del operador dejan de contar. Un CLEAR/ROTATE solo reinicia el presupuesto de la sesión (nueva generación); los bucles requieren reconocimiento.
- **Diagnóstico (solo lectura):** `status()` (`--status [--agent ROL]`) agrega por agente sesión, trabajo desde el último mantenimiento (despachos de la sesión `run_id`+generación vigente), duración medida, métricas con calidad, alertas, retenciones y la elegibilidad de `SessionManager.plan()`. Con un watcher activo, el efecto de cada alerta usa el modo que ese watcher guardó en ella. `calibrate()` (`--calibrate`) reproduce las reglas de bucle evento a evento con `evaluate(history=..., budgets=False)` (los reconocimientos posteriores a cada instante no cuentan) y resume episodios, repeticiones legítimas y recuperación tras CLEAR/ROTATE; propone umbrales solo con `MIN_DISPATCHES`/`MIN_EPISODES`. `describe()` y `hold()` expresan el modo vigente, también en la primera retención tras un reinicio.
- **Recomendaciones (4D.2):** `recommendations()` evalúa por agente las tareas de la sesión vigente (`session_work()`) frente a `max_operations_per_session` y la elegibilidad de `SessionManager.plan()`; devuelve `below_threshold`, `blocked` (con `checks` por condición) o `recommended` con evidencia y comandos de `maintenance_command()` (conservan el `--config` explícito del proceso, `RuntimeConfig.source`, como ruta absoluta; `maintenance` y `guard` aceptan `--config`). `Guard.announce_recommendations()` (watcher) persiste `guard_recommendation:<rol>` y anuncia solo una vez por clave `run_id:generación:causa` y cuota; nunca ejecuta. `state --release-followup ROL --confirm` libera el seguimiento de una tarea ya reconocida (`--acknowledge queued:...`), sin confirmarla.
- **Uso headless:** con `guard.headless_usage`, `SpecKitExecutor` pide al proveedor su resultado estructurado documentado (`structured_headless()`) y `read_headless_usage()` devuelve el texto y las métricas (`HEADLESS_METRICS`); `on_headless()` las registra con su calidad.
- **Hooks no bloqueantes:** un fallo al registrar se informa y no detiene el watcher.

### `errors.py`: contrato común de errores

Define `BMADRuntimeError` y sus subclases `ConfigurationError` (datos/selección inválidos), `UnsupportedCapability` (capacidad no implementada/verificada), `CommandError` (fallo de comando o respuesta) y `ReconciliationRequired` (duplicación, estado parcial o propiedad dudosa).

Lo importan los módulos del runtime; las entradas públicas capturan errores BMAD para informar fallos y evitar declarar éxito. No ejecuta procesos, escribe archivos ni ofrece CLI. Los consumidores también pueden dejar propagar errores ajenos a esta jerarquía; definir estas excepciones no implica recuperación automática.

### Recorridos entre módulos y comprobaciones

| Operación | Cadena principal | Resultado/efecto |
|---|---|---|
| Inicializar | init_bmad → workspace → context/config/state.project_lock | Scaffolding y vista efectiva del proyecto |
| Revisar flota | start_agents → cli → Runtime persist=False → fleet.plan → services/providers/herdr.start_command | JSON sanitizado; sin procesos ni SQLite |
| Lanzar flota | start_agents → cli → Runtime → fleet.launch → HerdrGateway → CommandRunner | Paneles reales y propiedad en SQLite |
| Supervisar | watcher_bmad → workflow → WatcherService/StateStore → AgentDispatcher o SpecKitExecutor | Cursor/cola, handoffs, prompts y artefactos según fase |
| Freeze | workflow → GitService.freeze → CommandRunner | Staging acotado y commit si hay cambios |
| Detener | stop_agents → maintenance → Runtime → HerdrGateway/StateStore | Cierre solo de tabs propios idle/done |
| Limpiar o rotar | maintenance --clear/--rotate → Coordination (locks maintenance/watcher/fleet/sessions) → SessionMaintenance → HerdrGateway/StateStore | Operación `maintenance:<op_id>` persistida; generación incrementada solo tras verificar |

Las pruebas en [tests](../tests) cubren estos límites: `test_multiworkspace.py` verifica selección, aislamiento, bootstrap, migración y parada; `test_runtime_infrastructure.py` configuración y procesos; `test_runtime_services.py` flota/despacho/estado; `test_codex_effort.py` traducción; `test_bmad_regressions.py` y pruebas de caracterización verifican gates y compatibilidad; `test_maintenance_contracts.py` comprueba configuración explícita durante init/migrate, opciones nativas y límites de rutas; `test_session_lifecycle.py` el plan de solo lectura, `test_session_maintenance.py` CLEAR/ROTATE, coordinación, fallos y recuperación, `test_agent_startup.py` PATH de paneles, diálogo de confianza, protocolo de ejecución e identidad determinista, `test_context_guard.py` presupuesto, loop guard, recuperación y contratos optimizados, y `test_guard_observability.py` uso headless, diagnóstico, calibración, texto del modo tras reinicio y contratos con los perfiles reales, `test_maintenance_recommendations.py` recomendaciones supervisadas, condiciones de bloqueo, duplicados y liberación de seguimientos, `test_tracker_integrity.py` cursor, cola, seguimiento activo, reinicios y reconciliación de merge-close, `test_stop_config.py` la `--config` de `stop_agents.py` y `test_delete_agents.py` la confirmación explícita de `utils/delete_agents.py`. `validate_offline.py` importa todos los módulos del paquete y comprueba ayudas, ejemplos, enlaces y dry-runs sin agentes reales. Los comandos de validación están en [SETUP.md](../SETUP.md#validación-local).

## Migración opcional

`utils/manage_workspace.py migrate` copia un proyecto legacy (datos dentro del motor) a un workspace nuevo:

```powershell
& $Python (Join-Path $Engine 'utils\manage_workspace.py') migrate --workspace 'D:\BMAD Workspaces\Migrado' --project migrado --dry-run
# Solo tras revisar el inventario y elegir un destino vacío:
& $Python (Join-Path $Engine 'utils\manage_workspace.py') migrate --workspace 'D:\BMAD Workspaces\Migrado' --project migrado --confirm
```

Copia documentos/app/specs/memoria y handoffs legacy, conserva el origen y registra `logs/migration.json`. No copia Git, dependencias, sesiones ni SQLite activo. Falla ante conflictos; una copia interrumpida puede dejar archivos parciales y requiere inspección. No reescribe referencias absolutas de documentos.

## Contexto constitucional y técnico

[constitution.md](../constitution.md) es la política compartida de operación e aislamiento.
[technical_context.py](technical_context.py) resuelve exclusivamente la memoria del workspace,
observa manifests y construye un índice por rol/operación. Launcher usa referencias compactas;
Spec Kit y cada handoff refrescan constitución y observaciones sin modificar estado aprobado.
El presupuesto del contexto ensamblado es 24 000 caracteres; constitución local y política se
incluyen una vez cuando caben completas. Guías largas y ADRs se enlazan para lectura pertinente.
No se leen archivos de secretos ni se siguen enlaces fuera del perímetro. Los scripts de
manifests nunca se ejecutan. La exploración limita archivos a 512 000 bytes, 2 000 directorios
y 300 observaciones; los límites se notifican. TOML detallado requiere Python 3.11+.

No se importan reglas técnicas desde el motor como fallback de otro workspace.

`python utils/manage_workspace.py context --workspace RUTA --project ID --role solutions-architect`
inspecciona contexto y diferencias sin procesos externos. `--record` guarda solo observaciones
en `docs/architecture/stack-observations.json`; las aprobaciones siguen siendo explícitas.
`GET /api/v1/project/context` ofrece el índice y descubrimiento del workspace del proceso dashboard.

La constitución técnica canónica es `<WORKSPACE_ROOT>/.specify/memory/constitution.md`; bootstrap la crea neutral con `initialize_constitution()`. Spec Kit, QT,
configuración efectiva y dashboard usan esa única ruta. El watcher ya no añade cláusulas globales
ni sobrescribe memoria aprobada. Las skills instaladas se cotejan íntegramente contra sus fuentes;
el contrato de precedencia se añade desde el servicio, conservando esa verificación.
