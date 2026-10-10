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
| [services.py](services.py) | SpecKit, despacho y gestión de contexto | Runtime, flota y workflow |
| [state.py](state.py) | SQLite, deduplicación y locks | Runtime, servicios, watcher, bootstrap y parada |
| [watcher_service.py](watcher_service.py) | Cursor y cola persistida del tracker | workflow |
| [workflow.py](workflow.py) | Reglas BMAD/SDD y bucle del watcher | watcher_bmad |
| [gitops.py](gitops.py) | Ejecución Git y freeze de especificaciones | workflow |
| [technical_context.py](technical_context.py) | Constitución local, índice técnico, descubrimiento y ensamblado de contexto | services, workspace y dashboard |
| [workspace.py](workspace.py) | Bootstrap y migración aditiva | init_bmad y manage_workspace |
| [maintenance.py](maintenance.py) | Cierre de sesiones con comprobación de propiedad | stop_agents |
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

### `services.py`: SpecKit, despacho y sesiones

Reúne cuatro responsabilidades utilizadas por Runtime:

- **`interactive_command()`:** invocada por flota; adapta el comando del proveedor al cwd del workspace, perfil absoluto compartido, entorno y contrato de rutas. Prepara el comando sin ejecutarlo.
- **`SpecKitExecutor`:** `workflow.ejecutar_speckit()` llama a `execute()`; `cli.spec_plan()` usa `prepare()`. Valida skills, directiva y feature dentro del perímetro; construye el prompt headless. Ejecutar toma lock `speckit`, verifica ayuda, registra `run:` en SQLite, lanza el CLI y clasifica su resultado; interrupciones quedan uncertain. No reintenta automáticamente ni anexa handoffs: workflow decide cómo registrar/continuar.
- **`AgentDispatcher`:** workflow lo usa para consultar agentes y despachar tareas/recordatorios. Comprueba registro ready, identidad/pane, proveedor/modelo y estado idle/done; deduplica por `dispatch:` y antepone el contrato de rutas al prompt. La aceptación del prompt se registra done; no equivale a terminar el trabajo del agente.
- **`SessionManager`:** `workflow.limpiar_sesiones_agentes()` intenta `clear()`. Exige propiedad, inactividad y capacidad de rotación. Los adaptadores actuales la rechazan: no envía `/clear` ni rota contexto automáticamente.

No ofrece una CLI propia. Sus efectos reales dependen del método: preparar solo lee, ejecutar/despachar usa procesos y estado.

### `state.py`: SQLite, deduplicación y locks

`StateStore` guarda objetos JSON en la tabla `records(id, data)` de `state/state.sqlite3` del workspace, o `.bmad-runtime/state.sqlite3` en legacy. `get()`/`put()` leen/escriben; `claim()` registra una operación in_flight una sola vez; `finish()` actualiza el estado; `fingerprint()` calcula identificadores deterministas.

- **Quién lo invoca:** Runtime abre el almacén; flota, servicios, WatcherService y workflow registran propiedad, operaciones, cursor, cola y seguimiento. `workspace` y maintenance usan `project_lock()` incluso sin abrir SQLite.
- **Cómo funciona:** una operación ya done no vuelve a reclamarse; otra incompleta requiere reconciliación. `project_lock()` usa bloqueo del sistema operativo (`msvcrt` en Windows, `fcntl` en POSIX). El archivo `.lock` puede permanecer tras liberar el bloqueo; su existencia no prueba una operación activa. Estado y tracker son fuentes distintas: SQLite guarda metadatos, no los prompts completos.
- **CLI y efectos:** `python -m bmad_runtime.state` toma locks watcher/fleet/speckit, abre/crea SQLite y muestra registros no done. `--acknowledge ID --confirm` admite IDs event/dispatch/queued existentes y los marca done; no reintenta ni acredita entrega. No debe ejecutarse mientras esos locks estén ocupados.

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
| `registrar_seguimiento()`, `vigilar_agentes_inactivos()` | Detectar falta de registro, leer cuota y enviar recordatorios o escalar | Despacho y bucle cuando no hay pausa humana |
| `macro_gitops()`, `gitops_branch_create()`, `gitops_merge_close()` | Reconocer macros independientes y gestionar rama/cierre | Procesamiento de nuevas líneas |
| `hydration_gitops()` | Buscar apertura de rama aún no cerrada en el tracker | Arranque del watcher |
| `compilar_agentes_modulares()` | Reconstruir perfiles compartidos desde fuentes, instrucciones y skills | Solo `main()` con `--compile-profiles` |

**Efectos de operación:** anexa registros al tracker, persiste estado, despacha prompts y ejecuta SpecKit/Git. Retrabajo conserva datos en `.specify/memory/rework_state.json` y `rework_last_classification.md`; implementación puede crear directivas temporales dentro del workspace. Las escrituras de código/documentos las realiza el CLI headless y el workflow comprueba sus entregas. Los fallos requieren inspección del trabajo parcial, no un borrado de historial.

**Efectos de GitOps:** creación/reanudación de ramas y freeze; cierre solicita al operador escribir el nombre de rama, luego merge y borrado de la rama fusionada. Árbol sucio con auto_commit deshabilitado detiene el cambio; con autosave habilitado puede hacer add/commit. Cerrar una rama intenta limpiar contexto, pero la capacidad está deshabilitada actualmente.

**Funciones conservadas que no son un paso automático de arranque:** `guardar_historial()` y `validar_constitucion_gitops()` están definidas, pero no tienen llamadas internas actuales. La primera es una API legacy para autosave optativo; la segunda verifica la existencia de la constitución local sin añadir política global. Su existencia no significa que iniciar el watcher las ejecute.

**Mantenimiento explícito:** `--compile-profiles` escribe los `AGENTS.md` compartidos del motor y debe ejecutarse sin selección de proyecto; no es preparación habitual de cada workspace. `workflow.py` expone funciones y `main()`, pero no tiene bloque `__main__`: utiliza `watcher_bmad.py` como entrada pública.

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

Es código operativo necesario para `utils/stop_agents.py`, independiente de una eventual carpeta raíz `maintenance/`. `stop_main()` procesa selección y `--confirm`; sin confirmación termina sin cerrar tabs.

- **Quién lo invoca:** `utils/stop_agents.py` llama a `stop_main()`; este construye Runtime y llama a `close_owned_tabs()`. Las pruebas comprueban propiedad y separación de proyectos.
- **Cómo funciona:** toma locks watcher/fleet, consulta agentes/panes/tabs de Herdr y contrasta cada miembro con registros de propiedad del proyecto. Solo permite idle/done. Valida todos los destinos antes de cerrar; tabs ocupados, vacíos o con miembros no verificables requieren reconciliación/manual.
- **Efectos:** con confirmación abre estado/refresca configuración, cierra tabs verificados y marca sus agentes closed. No detiene el watcher por sí solo, mata agentes ocupados, borra artefactos ni ofrece dry-run/config. Un fallo al cerrar puede requerir inspección de los tabs restantes.

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

Las pruebas en [tests](../tests) cubren estos límites: `test_multiworkspace.py` verifica selección, aislamiento, bootstrap, migración y parada; `test_runtime_infrastructure.py` configuración y procesos; `test_runtime_services.py` flota/despacho/estado; `test_codex_effort.py` traducción; `test_bmad_regressions.py` y pruebas de caracterización verifican gates y compatibilidad; `test_maintenance_contracts.py` comprueba configuración explícita durante init/migrate, opciones nativas y límites de rutas. `validate_offline.py` importa todos los módulos del paquete y comprueba ayudas, ejemplos, enlaces y dry-runs sin agentes reales. Los comandos de validación están en [SETUP.md](../SETUP.md#validación-local).

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
