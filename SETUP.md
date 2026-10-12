# Instalación y configuración

Instalación del motor BMAD en Windows con PowerShell, dependencias, proveedores de IA, Herdr,
variables de entorno, configuración y diagnóstico. La operación de proyectos está en
[GUIDE.md](GUIDE.md) y la arquitectura en [ARCHITECTURE.md](ARCHITECTURE.md).

Instala el motor una sola vez. No lo clones por proyecto ni copies perfiles o skills a los
workspaces.

## Prerrequisitos

| Dependencia | Requisito | Comprobación |
|---|---|---|
| Python | 3.10 o posterior; 3.11+ para leer `pyproject.toml` en el descubrimiento Brownfield | `& $Python --version` |
| Git | Repositorio propio por workspace para ramas, freeze y cierre GitOps | `git --version` |
| PowerShell | Ejemplos y scripts Spec Kit en `.specify/scripts/powershell` | `$PSVersionTable.PSVersion` |
| Herdr | Aplicación abierta y CLI accesible; el motor no la instala ni la abre | `herdr agent start --help`, `herdr agent list` |
| Claude y/o Codex | Todos los proveedores de la selección efectiva, instalados y autenticados | `Get-Command claude,codex -ErrorAction SilentlyContinue` |
| Node.js y npm | Solo para el dashboard; Node 22.18+ para sus pruebas | `node --version`, `npm --version` |

El motor no fija versiones mínimas de Herdr ni de los CLIs de IA: antes de ejecutar comprueba
que su ayuda contenga los flags requeridos. En Windows, `CommandRunner` rechaza wrappers `.cmd`,
`.bat` y `.ps1`: configura ejecutables nativos. Herdr debe resolver el mismo ejecutable del
proveedor que la configuración.

## Dependencias

Desde la raíz del motor:

```powershell
$Engine = (Get-Location).Path
$Python = Join-Path $Engine 'bmad-control-center/backend/.venv/Scripts/python.exe'
python -m venv bmad-control-center/backend/.venv   # solo si falta el entorno
& $Python -m pip install -r (Join-Path $Engine 'bmad-control-center/backend/requirements.txt')
npm --prefix (Join-Path $Engine 'bmad-control-center/frontend') ci
```

El runtime solo usa la biblioteca estándar. [requirements.txt](bmad-control-center/backend/requirements.txt)
cubre el backend del dashboard y las pruebas (incluye AnyIO) y no fija versiones. El frontend
solo es necesario para el dashboard; `postinstall` prepara Nuxt.

## Proveedores y Herdr

Verifica los proveedores que aparezcan en los dry-runs:

```powershell
claude --help
claude auth status
codex --help
codex exec --help
codex login status
herdr agent start --help
herdr agent list
```

Si los subcomandos de autenticación difieren en tu versión, consulta `claude auth --help` y
`codex login --help`. No guardes credenciales en la configuración. La ayuda y el estado de
autenticación no prueban cuota, acceso al modelo ni éxito remoto.

| Proveedor | Implementación | Effort y traducción | Otras opciones |
|---|---|---|---|
| Claude | Interactivo y headless | `low`, `medium`, `high`, `xhigh`, `max` → `--effort NIVEL` | `permission_mode`: `manual`, `plan`, `acceptEdits`, `bypass` (→ `--dangerously-skip-permissions`, solo si se configura explícitamente). Default: `acceptEdits` en interactivo/herdr (ediciones dentro del workspace sin preguntar; shell y rutas externas piden aprobación), `manual` en headless; `max_budget_usd` positivo hasta 1000, solo headless |
| Codex | Interactivo y headless | Mismos niveles → `-c model_reasoning_effort=NIVEL`; `max` exige modelo explícito de la allowlist (`gpt-6-astra`) | `sandbox`: `read-only`, `workspace-write`; `approval`: `never` (default → `--ask-for-approval never`) o `on-request`; solo interactivo/herdr, `codex exec` no pide aprobación; no acepta `permission_mode` |
| Gemini | Solo registro | Sin traducción; `options` no vacías se rechazan | Dry-run `pending`; arranque no disponible |

Omitir effort conserva el default del CLI. Mayúsculas, `ultra` o tipos inválidos fallan sin
conversión. `model: null` delega al CLI; un nombre explícito válido no acredita acceso remoto.
Las listas son contratos del adaptador actual, no del catálogo del proveedor.

Las skills instaladas en `.agents/skills` (Codex) y `.claude/skills` (Claude) deben coincidir
con `.github/skills`, incluidos sus recursos. No se sincronizan al arrancar ni son duplicados
prescindibles. Recompilar los perfiles `<rol>/AGENTS.md` es mantenimiento explícito del motor:
`watcher_bmad.py --compile-profiles`, sin selección de proyecto.

## Variables de entorno

| Variable | Uso |
|---|---|
| `BMAD_WORKSPACE`, `BMAD_PROJECT` | Selección de proyecto cuando el comando no recibe `--workspace`/`--project`; obligatoria para que el backend del dashboard fije un proyecto |
| `VITE_BMAD_API_BASE` | Base HTTP del frontend (por defecto `http://localhost:8000/api/v1`); la URL WebSocket se deriva de ella |
| `BMAD_TEST_REAL_CLI` | `1` habilita pruebas opcionales contra CLIs reales; el harness aislado la desactiva |

El runtime inyecta a los procesos hijos `ENGINE_ROOT`, `WORKSPACE_ROOT`, `PROJECT_ID`,
`BMAD_TRACKER`, `BMAD_CONFIG`, `BMAD_DOCUMENTS`, `BMAD_APP`, `BMAD_HANDOFFS`, `BMAD_STATE`,
`BMAD_LOGS`, `BMAD_TEMP`, `SPECIFY_INIT_DIR` y `TEMP`/`TMP`/`TMPDIR` apuntando al workspace. No
hace falta definirlas a mano.

## Configuración

| Origen | Contenido |
|---|---|
| `config_bmad.json` del motor | Selección IA global, ejecutables, límites, Git y registro `projects` |
| `project.json.config` del workspace | `project_name`, `project_type`, `ux_phase`, `code_dirs` y overrides `ai.defaults`/`phases`/`agents`/`speckit` |
| `state/config_bmad.json` | Vista efectiva generada para consumidores legacy; no editar |

Primero se combinan global y proyecto; después se resuelve `defaults → fase → agente` o
`defaults → fase → operación Spec Kit`. Fases: B, M, A, D. Cambiar de proveedor descarta el
modelo y las opciones heredados en esa selección; `options` reemplaza el objeto completo. No
hay fallback a otro proveedor. Los overrides globales de agentes u operaciones siguen vigentes
aunque cambies `ai.defaults`: revisa todas las filas de los dry-runs.

Ejemplo de overrides para el objeto `config` de `project.json`:

```json
{
  "ai": {
    "defaults": {"provider": "claude", "model": null, "options": {"effort": "medium"}},
    "phases": {
      "B": {"provider": "claude", "model": null, "options": {"effort": "medium"}},
      "M": {"provider": "claude", "model": null, "options": {"effort": "medium"}},
      "A": {"provider": "codex", "model": null, "options": {"effort": "high"}},
      "D": {"provider": "codex", "model": null, "options": {"effort": "high"}}
    },
    "agents": {"business-analyst": {"provider": "claude", "model": null, "options": {"effort": "high"}}},
    "speckit": {"implement": {"provider": "codex", "model": null, "options": {"effort": "xhigh"}}}
  }
}
```

| Clave | Ubicación | Ejemplo | Efecto |
|---|---|---|---|
| `schema_version`, `project_id` | Raíz de `project.json` | `1`, `proyecto-a` | Identidad; no cambiarla para alternar proyectos |
| `project_name` | `project.json.config` | `Proyecto A` | Nombre efectivo |
| `project_type`, `ux_phase` | `project.json.config` | `headless`, `off` | Omitir UX; `auto`/`on` en proyectos con interfaz |
| `code_dirs` | `project.json.config` | `{"backend":"server"}` | Solo `backend`/`frontend`; carpetas locales fuera de directorios operativos |
| `ai.defaults`, `ai.phases`, `ai.agents`, `ai.speckit` | Global o `project.json.config` | `{"D":{"provider":"codex"}}` | Selección por nivel |
| `ai.providers` | Solo global | `{"claude":{"executable":"claude"}}` | Ejecutable sin argumentos; ruta relativa al motor |
| `ai.git.auto_commit` | Solo global | `false` | Desactiva el autosave; freeze y macros GitOps siguen escribiendo |
| `ai.limits` | Solo global | `{"command_timeout":120,"headless_timeout":1800,"max_output_bytes":1048576,"max_processes":1}` | Límites por `CommandRunner` |
| `ai.limits.operation_timeouts` | Solo global | `{"implement":3600}` | Timeout en segundos (1–86400) por operación Spec Kit (`specify`, `clarify`, `plan`, `tasks`, `analyze`, `converge`, `implement`); las omitidas usan `headless_timeout`. Al vencer se termina el árbol de procesos y la operación queda `timeout` |
| `ai.tracker` | Solo global | `{"settle_seconds":4,"rewrite_grace_seconds":10}` | Lectura segura del tracker (enteros 0–3600). `settle_seconds`: espera antes de aceptar una última línea sin salto final que ya no cambia. `rewrite_grace_seconds`: tolerancia ante reescrituras o truncamientos transitorios antes de suspender. Con `0` se procesa la línea y se suspende de inmediato, como antes. Opcional `lock_timeout_seconds` (por defecto 5): espera máxima del lock de escritura del tracker (`tracker_io`) antes de fallar sin escribir |
| `ai.guard` | Solo global | `{"mode":"observe"}` | Presupuesto de contexto y loop guard (ver [Presupuesto de contexto y bucles](#presupuesto-de-contexto-y-bucles)). Omitido = `observe` con valores conservadores |
| `projects` | Raíz global | `{"proyecto-a":"../Proyecto A"}` | Selección por ID; rutas relativas al archivo |

El proyecto no puede cambiar ejecutables, límites, Git, tracker ni registro. Con `projects`
presente, aunque esté vacío, todo comando exige seleccionar un workspace. Sin ese registro el
runtime entra en modo legacy (motor como proyecto) con advertencia de obsolescencia; el template
no lo usa. Hay ejemplos en [examples/](examples/config_bmad.mixed.json) y un registro de dos
proyectos en [examples/multiworkspace.config.json](examples/multiworkspace.config.json).

`init_bmad.py`, `utils/manage_workspace.py`, `utils/start_agents.py`, `watcher_bmad.py`,
`python -m bmad_runtime.maintenance` (ciclo de sesiones) y `python -m bmad_runtime.guard` admiten
`--config RUTA` (anclada al motor; una ruta inexistente falla antes del bootstrap). Repítelo en
cada comando: `project.json` no guarda el origen. Dashboard, aprobaciones, parada e inspección de
estado usan siempre `config_bmad.json` del motor. `Runtime` cachea la configuración: reinicia los
procesos afectados tras editarla.

## Validación local

Sin agentes reales ni red:

```powershell
& $Python -B tests/run_isolated.py tests -q
& $Python -B tests/validate_offline.py
& $Python -B tests/run_isolated.py bmad-control-center/backend/tests -q
npm --prefix bmad-control-center/frontend test
npm --prefix bmad-control-center/frontend run build
```

`validate_offline.py` comprueba imports, ayuda de CLIs, ejemplos JSON, bloques JSON de la
documentación, enlaces Markdown y dry-runs de dos proyectos con los tres proveedores, sin ejecutar
procesos externos.

## Diagnóstico

| Síntoma | Comprobación y acción |
|---|---|
| Ruta inexistente o sin identidad | Comprueba el workspace; inicialízalo con ruta e ID explícitos |
| ID diferente | Lee `project.json` y corrige el comando; no cambies la identidad para tomar otras sesiones |
| Configuración inválida | Valida JSON y claves, repite ambos dry-runs; no edites `state/config_bmad.json` |
| CLI ausente, wrapper o flags faltantes | `Get-Command` y ayuda del proveedor o Herdr; instala un ejecutable nativo compatible |
| Autenticación, cuota o modelo inaccesible | Estado de autenticación y consola del proveedor; el dry-run no prueba acceso remoto |
| Fila `pending` en dry-run | Proveedor Gemini o capacidad no implementada; cambia la selección |
| Skill pendiente o diferente | Coteja `.agents`/`.claude` con `.github/skills` mediante mantenimiento revisado del motor |
| Herdr inaccesible o respuesta inválida | Aplicación abierta y `herdr agent list`; el gateway exige JSON con `result` |
| Escritura denegada o salida fuera del perímetro | Revisa permisos y junctions; usa un destino propio sin enlaces que escapen |
| Git padre detectado | `git -C $Workspace rev-parse --show-toplevel` debe devolver el workspace |
| Watcher detenido por `Tracker history changed before the saved cursor` | El tracker quedó más corto, reescrito o ausente durante más de `rewrite_grace_seconds`; sigue [Integridad del tracker](#integridad-del-tracker) |

Comprobaciones sin borrar archivos:

```powershell
Get-Content -Raw -LiteralPath (Join-Path $Workspace 'project.json') | ConvertFrom-Json
herdr tab list
herdr pane list
git -C $Workspace status
```

Recuperación de un proyecto en ejecución: [GUIDE.md](GUIDE.md#13-recuperación).

### Integridad del tracker

El watcher procesa solo líneas terminadas en salto de línea; una línea a medio escribir espera
hasta completarse o hasta llevar `settle_seconds` sin cambios. En cada lectura verifica que las
líneas ya procesadas (registro `tracker_cursor` de SQLite) siguen intactas. Si el archivo cambia
mientras se lee, reintenta en el siguiente ciclo. Si queda más corto, reescrito o ausente, espera
`rewrite_grace_seconds`; si no se recupera, se detiene sin despachar, registra `tracker_integrity`
(`reason`: `shorter`, `rewritten`, `missing` o `invalid_utf8`) y no escribe en el tracker.

Cada handoff encolado (`queued:`) conserva su `state` canónico y añade `stage` y `stages` con las
etapas `detectado`, `reservado`, `despachado`, `confirmado` (el agente registró su bloque),
`fallido` (no se entregó) y `requiere_intervencion` (entrega incierta o agente sin registro tras
los recordatorios). Un despacho incierto nunca se reintenta automáticamente.

Recuperación, con el watcher detenido:

1. Inspecciona el estado: `& $Python -B -m bmad_runtime.state --workspace $Workspace --project $Project`.
2. Si el cambio fue accidental, restaura el tracker (historial de Git o copia) y reinicia el
   watcher; al encontrar el historial intacto marca `tracker_integrity` como `done`.
3. Si el cambio fue intencional, revisa que ningún handoff nuevo quede sin atender y acepta el
   contenido actual como historial procesado:
   `& $Python -B -m bmad_runtime.state --workspace $Workspace --project $Project --rebaseline-tracker --confirm`.
   Las líneas completas existentes no se vuelven a despachar; vuelve a emitir a mano cualquier
   handoff pendiente. Un `queued:` cuya línea cambió se reconoce con `--acknowledge`.

### Arranque y entrega en Herdr

- Nombre de agente: `<proyecto>-<hash8 del workspace>-<alias del rol>` (por ejemplo
  `alpha-1a2b3c4d-ba`), siempre de 32 caracteres o menos, como exige Herdr. El nombre usado se
  guarda en `agent:<rol>`; las sesiones lanzadas con el formato anterior deben relanzarse.
- Contrato del agente: se escribe completo en `state/contracts/<rol>.md` al lanzar la flota. Claude
  lo recibe con `--append-system-prompt-file` y Codex con un mensaje inicial de una línea que lo
  referencia: Herdr en Windows rechaza argumentos con saltos de línea. Incluye copias íntegras del
  perfil del rol y de `ENGINE_ROOT/constitution.md` (con su sha256 en la cabecera), de modo que el
  arranque no lee archivos fuera del workspace ni pide aprobaciones. Se regenera al lanzar y antes
  de cada despacho si cambian sus fuentes; cada archivo de tarea indica las fuentes vigentes.
  Plantillas o skills del motor que el agente abra después siguen sujetas a su aprobación normal.
- Registro en el tracker: contrato y tareas exigen anexar solo con la herramienta de edición del
  agente (Edit/apply_patch), nunca con shell. Esas herramientas reescriben el archivo completo, así
  que una escritura concurrente aún podría perderse: la verificación de integridad del watcher lo
  detecta y suspende ([Integridad del tracker](#integridad-del-tracker)).
- Windows: Herdr crea las pestañas y paneles con `--env PATH=…`, donde los alias de la Microsoft
  Store (`…\Microsoft\WindowsApps`) quedan al final. El sandbox `unelevated` de Codex no puede
  lanzar apps empaquetadas (`CreateProcessAsUserW failed: 5`), así que usa el `pwsh.exe` instalado
  (por ejemplo `C:\Program Files\PowerShell\7`). Si solo existe la versión de la Store, instala
  PowerShell 7 MSI; no se cambia ninguna configuración global ni el modo del sandbox. Un panel
  restaurado o reutilizado por Herdr conserva el `PATH` del servidor, sin ese orden: antes de
  arrancar Codex en cualquier panel (flota, ROTATE) el runtime escribe en su shell una sonda de una
  línea (`Get-Command pwsh`); si resuelve a `WindowsApps`, reordena `$env:Path` solo en esa shell
  (el mismo orden de `--env PATH`) y vuelve a comprobar. Si sigue sin un `pwsh` instalado, rechaza
  el arranque con diagnóstico. Si la máquina solo tiene el `pwsh` de la Store, ROTATE se rechaza
  antes de enviar `/exit`.
- Codex con `sandbox: read-only` se lanza sin `--add-dir` (Codex no admite raíces escribibles
  adicionales en ese modo).
- Cada handoff se escribe en `handoffs/tasks/<evento>-<intento>.md` (creación exclusiva, nunca se
  sobrescribe) y la terminal recibe una línea breve que lo referencia. `dispatch:<evento>` guarda
  `task_file`, `task_sha256` y `delivery`.
- Entrega: `herdr agent prompt --wait --until working|idle|done|blocked --timeout 30000`.
  `done` + `delivery: accepted` = el agente reaccionó; `not_delivered` = Herdr lo rechazó antes de
  enviar (por ejemplo `agent_blocked`); un reinicio manual del watcher crea un nuevo intento con
  otro archivo. `uncertain` (por ejemplo `agent_prompt_stalled`) nunca se reintenta: revisa el
  panel y usa `--acknowledge` solo tras comprobarlo.
- Arranque verificado: `start_agents.py` deja cada agente en `starting` y solo lo pasa a `ready`
  tras una operación `VERIFY` (identidad determinista y respuesta del agente, ver
  [Ciclo de vida de sesiones](#ciclo-de-vida-de-sesiones)). El watcher retiene, sin despachar, las
  tareas de agentes en `starting`, `awaiting_trust`, `unverified` o `maintenance`.
- Diálogo de confianza: la primera vez en un workspace, Claude Code pregunta si confiar en la
  carpeta, y Codex 0.162 lo hace por repositorio Git («Folder access … Trust this folder? › 1. Trust
  and continue / 2. Quit»). Herdr puede darlo por listo (`idle`) o `blocked`; un Enter o un dígito
  elegiría una opción. Antes de cada escritura (tarea, recordatorio, sonda de VERIFY, `/clear`,
  `/exit`, `--reconcile`) el runtime clasifica la pantalla visible y el proceso del panel
  (`bmad_runtime/pane_state.py`) y escribe solo si ve el compositor vacío del CLI esperado
  (`READY_VERIFIED`), bajo un lock por panel. Un diálogo deja el agente en `awaiting_trust`; un CLI
  terminado o una pantalla ambigua persistente, en `unverified`; una pantalla ocupada solo aplaza
  la tarea. El runtime nunca responde diálogos ni modifica la configuración de Claude o Codex:
  respóndelo tú en el panel y ejecuta `--reconcile ROL --confirm`, que vuelve a comprobar pantalla,
  proceso, identidad, rol y workspace antes de liberar el despacho.
- Protocolo de ejecución: el watcher es el único despachador y el tracker no es una cola. El
  contrato y la orden de arranque lo indican, y el watcher lo comprueba de forma determinista:
  cada bloque cuyo autor corresponde a un agente debe responder a un despacho (`followup` activo o
  `confirmed_block` del handoff confirmado). Un bloque sin despacho registra
  `protocol_violation:<n>`, anota un bloque WATCHER, retiene todos los despachos y aparece en
  `--plan-clear`. Con el watcher detenido, revisa el trabajo y reconcilia con
  `& $Python -B -m bmad_runtime.state --workspace $Workspace --acknowledge protocol_violation:<n> --confirm`.
  El historial previo a la primera auditoría (estados SQLite anteriores) no se juzga.
- Seguimiento por agente: mientras un agente tiene un `followup` activo (tarea despachada sin su
  bloque en el tracker), no recibe otra tarea aunque Herdr lo muestre `idle`; la siguiente queda en
  cola (`detectado`) y sobrevive a un reinicio. Se libera con su bloque, con la escalada del
  vigilante tras `MAX_RECORDATORIOS` o, tras reconocer su tarea (`--acknowledge queued:...`), con
  `state --release-followup ROL --confirm`.

### Ciclo de vida de sesiones

Al confirmar un handoff, el watcher guarda `session:<agente>` en SQLite: agente, proyecto,
workspace, tarea, fase, handoff, `Estado`, artefactos (ruta y existencia), decisiones y puntos
abiertos tal como los registró el agente, fecha y generación de sesión. Textos acotados a 500
caracteres; no guarda conversaciones ni salidas de herramientas.

Liberar contexto es siempre una decisión del operador: el watcher nunca limpia ni rota sesiones
(al cerrar una HU solo sugiere revisar el plan). Comandos (`ROL` admite el nombre o el alias, por
ejemplo `business-analyst` o `ba`):

```powershell
& $Python -B -m bmad_runtime.maintenance --workspace $Workspace --plan-clear
& $Python -B -m bmad_runtime.maintenance --workspace $Workspace --clear ROL --confirm
& $Python -B -m bmad_runtime.maintenance --workspace $Workspace --rotate ROL --confirm
& $Python -B -m bmad_runtime.maintenance --workspace $Workspace --reconcile ROL --confirm
& $Python -B -m bmad_runtime.maintenance --workspace $Workspace --verify ROL --confirm
```

- `--plan-clear`: solo lectura (sin locks, escrituras ni mensajes). Cada agente propio recibe
  `ELIGIBLE` o `NOT_ELIGIBLE`, sus motivos, su generación y una acción: `CLEAR` (Claude Code),
  `ROTATE` (Codex u otro proveedor), `SKIP` (condición transitoria: agente ocupado, tareas
  pendientes o sin confirmar, ejecución headless, líneas sin procesar, sesión ya renovada tras su
  último handoff) o `MANUAL_REVIEW` (dato ausente, incierto o inconsistente, o mantenimiento
  pendiente). `--clear`/`--rotate` sin `--confirm` muestran la fila del agente y no cambian nada.
- `--clear` solo existe para Claude Code: su contrato viaja como system prompt y sobrevive a
  `/clear`. Codex lo recibe como primer mensaje y lo pierde, así que solo admite `--rotate`. Un
  fallo de CLEAR nunca se convierte en ROTATE sin una nueva orden del operador.
- Coordinación: el comando toma los locks de SO `maintenance` (un mantenimiento por workspace),
  `fleet` y `sessions`. El watcher toma `sessions` en cada ciclo y publica un latido `watcher`
  (`sessions-lock/1`) en SQLite; mientras el mantenimiento retiene el lock, el watcher no lee ni
  despacha. Si no hay watcher, el comando retiene también el lock `watcher` para que ninguno
  arranque a mitad de la operación. Un watcher sin latido reciente o sin el protocolo bloquea el
  mantenimiento. Tras adquirir los locks se vuelve a evaluar la elegibilidad e identidad (nombre,
  panel, tipo de CLI y cwd del panel en Herdr; proveedor y modelo). Un cierre inesperado libera
  los locks, pero no la operación registrada.

Máquinas de estado (registro `maintenance:<op_id>`):

| Operación | Estados | Pasos |
|---|---|---|
| ROTATE | `REQUESTED → QUIESCED → STOPPING → STARTING → VERIFYING → COMPLETED` | resumen y contrato regenerado; `/exit`; agente fuera de `herdr agent list` y panel con la shell en primer plano (`pane process-info`); relanzamiento del mismo rol en el mismo panel; verificación |
| CLEAR | `REQUESTED → QUIESCED → CLEARING → VERIFYING → COMPLETED` | resumen y contrato regenerado; `/clear`; mismo agente idle en su panel; verificación |
| VERIFY | `REQUESTED → VERIFYING → COMPLETED` | arranque de la flota, `--verify` o agente retenido; diálogo, identidad determinista y respuesta; no cambia el contexto ni la generación |

Antes de pedir la respuesta del agente se comprueban, sin depender del modelo: nombre y panel en
Herdr, tipo de CLI, cwd del panel = workspace, proceso en primer plano del proveedor (para Claude,
su argv referencia `state/contracts/<rol>.md`), proveedor y modelo configurados y generación
coherente con las operaciones del mismo lanzamiento (`run_id`). Una contradicción deja la
operación en `REQUIRES_INTERVENTION`; un dato que Herdr no expone no cuenta como fallo.

Verificación: el comando escribe `state/maintenance/<nonce>.md` y envía al agente una línea breve
que lo referencia. El agente relee su contrato vigente y responde una línea
`BMAD-VERIFICACION op=<nonce> rol=… proyecto=… workspace=… fuentes=… memoria=…`; se exige rol,
proyecto, workspace, digests de perfil y política actuales y `memoria=NINGUNA` (contexto
reiniciado). Solo entonces se incrementa la generación (`agent:<rol>.generation`) en la misma
transacción que `COMPLETED`. `FAILED` significa que nada llegó al agente (rechazo previo al envío);
cualquier resultado incierto o parcial queda en `REQUIRES_INTERVENTION`, sin reintentos. Cada
registro guarda proyecto, workspace, agente, proveedor, generación anterior y nueva, estados con
fecha, resumen y su sha256, fuentes del contrato, evidencias, errores e incertidumbre.

Recuperación: una operación no final (`REQUIRES_INTERVENTION` o un estado intermedio tras un
cierre inesperado) sigue visible en `--plan-clear` (`maintenance_pending:<rol>`), bloquea nuevos
mantenimientos y el cierre de tabs, y el watcher retiene las tareas de ese agente.

1. Inspecciona el panel (`herdr agent read`, `herdr pane process-info --pane <id>`). No apruebes
   permisos que el agente pida durante la operación.
2. Si el agente no corre en su panel y la shell está en primer plano, `--reconcile` muestra el
   comando exacto de relanzamiento; ejecútalo a mano.
3. Con el agente idle en su panel, `--reconcile ROL --confirm` repite la verificación. Si el
   contexto está limpio incrementa la generación (VERIFY nunca la cambia); si conserva el anterior,
   la mantiene. En ambos casos registra `resolution` y libera el bloqueo; nunca reenvía `/exit`,
   `/clear` ni relanza. Un agente en `awaiting_trust`, `starting` o `unverified` sin operación
   pendiente se reconcilia igual, con una operación VERIFY nueva. Si el diálogo sigue en pantalla,
   falla sin escribir nada.

Reversión: no hay migración de datos. Revertir el código deja registros `maintenance:*` y el campo
`generation` sin consumidores; no hace falta borrarlos. Antes de revertir, termina o reconcilia
toda operación pendiente y detén el watcher.

Paneles: la rotación hereda el entorno del panel; antes de relanzar Codex se comprueba y, si hace
falta, se corrige el `pwsh` de esa shell (ver [Arranque y entrega en Herdr](#arranque-y-entrega-en-herdr)).
La evidencia queda en el paso `pane_shell` de la operación y en `agent:<rol>.pane_shell`.

### Presupuesto de contexto y bucles

El watcher registra en SQLite eventos de progreso y evalúa presupuestos y bucles con
`bmad_runtime/guard.py`. Modo predeterminado `observe`: solo alerta (consola y
`logs/guard.log` del workspace; nunca en el tracker). `enforce` además retiene nuevos despachos al
agente implicado ante `PAUSE` o `REQUIRES_INTERVENTION`; `off` lo desactiva. Ningún modo
interrumpe una operación activa, reintenta entregas inciertas ni limpia o rota sesiones.

```powershell
& $Python -B -m bmad_runtime.guard --workspace $Workspace                       # informe, solo lectura
& $Python -B -m bmad_runtime.guard --workspace $Workspace --status              # diagnóstico por agente, solo lectura
& $Python -B -m bmad_runtime.guard --workspace $Workspace --status --agent business-analyst
& $Python -B -m bmad_runtime.guard --workspace $Workspace --calibrate           # calibración, solo lectura
& $Python -B -m bmad_runtime.guard --workspace $Workspace --acknowledge no_progress:business-analyst --confirm
```

`--status` muestra por agente: estado del registro, sesión (`run_id`, generación, renovación y
verificación), último mantenimiento, tareas desde el último CLEAR/ROTATE o arranque, duración
acumulada medida, métricas con su calidad, alertas abiertas, retenciones (guard, mantenimiento
pendiente o estado del agente) con el comando que las libera, y la elegibilidad de
`maintenance --plan-clear` (misma fuente; consulta `herdr agent list`). Con un watcher activo, el
efecto de cada alerta usa el modo que ese watcher aplica (puede ejecutarse con otro `--config`);
`watcher` indica si el latido está activo u obsoleto. `--calibrate` reproduce las reglas de bucle
sobre el registro: episodios por regla y cómo terminaron (avance, reconocimiento, abiertos),
`PAUSE` resueltos solos (los que `enforce` habría retenido), repeticiones legítimas, recuperación
tras CLEAR/ROTATE y métricas por proveedor. Solo propone un umbral por proveedor con al menos 30
despachos y 5 episodios; nunca cambia la configuración ni el modo. Ninguno de los dos escribe.

Mantenimiento recomendado: cuando las tareas despachadas a la sesión vigente de un agente (misma
ejecución y generación) alcanzan `max_operations_per_session` y el agente es `ELIGIBLE` en
`maintenance --plan-clear` (sin handoffs pendientes ni inciertos, tracker verificado, sin
mantenimiento en curso, agente propio e inactivo, resumen completo), `--status` incluye en
`recommendation` el agente, proveedor, motivo, evidencia, generación, operación (CLEAR para Claude
Code, ROTATE para el resto) y los comandos exactos de revisión y aplicación. Si falta una condición,
`status: blocked` indica cuál (`checks`). El watcher anuncia cada recomendación una sola vez por
sesión, causa y evidencia (otra cuota completa de tareas o una generación nueva cuentan como
evidencia nueva); queda en SQLite (`guard_recommendation:<rol>`) y `logs/guard.log`, sobrevive a
reinicios sin repetirse y nunca se ejecuta: un humano revisa el plan y lanza el comando. Los tokens
nunca la disparan. Si el watcher arrancó con `--config`, ambos comandos terminan en
`--config "<ruta absoluta>"` (también en `commands.config`) para que el plan use el mismo umbral y
proveedores; con la configuración predeterminada no llevan `--config`. Un `guard --status` lanzado
con otra configuración que la del anuncio añade `config_warning` a la recomendación.

Si una tarea quedó despachada a un panel que ya no existe (servidor Herdr detenido), el watcher la
sigue esperando y el agente queda `followup_active`. Tras inspeccionar el panel y el tracker,
reconócela y libera el seguimiento con el watcher detenido; la tarea no se confirma ni se reintenta:

```powershell
& $Python -B -m bmad_runtime.state --workspace $Workspace --acknowledge queued:<event_id> --confirm
& $Python -B -m bmad_runtime.state --workspace $Workspace --release-followup business-analyst --confirm
```

Métricas: duración e intentos son `measured` (reloj y registros del runtime); el tamaño del
archivo de tarea y del contrato en tokens es `estimated` con la razón caracteres/token medida para el
texto del framework (Claude 2,1; Codex 3,85; 4 para proveedores no medidos) y no representa consumo.
En sesiones interactivas (Herdr) tokens y coste son `unavailable` para Claude, Codex y Gemini: la
TUI no expone uso al runtime. Por eso `max_input_tokens`, `max_output_tokens` y `max_cost_usd`
deben quedar en `null`: configurarlos para un proveedor que no los reporta falla al cargar.

Las ejecuciones headless de Spec Kit pueden medir su uso con `"guard": {"headless_usage": true}`
(desactivado por defecto porque cambia el formato de salida del CLI; la respuesta de texto se
extrae igual para clarify, analyze y converge). Claude usa `-p --output-format json`: tokens de
entrada (incluida la caché), lectura y escritura de caché, salida, turnos y ventana de contexto son
`measured`; el coste es `estimated` porque el CLI lo calcula a precio de lista (`costBasis`), no es
facturación. Codex usa `exec --json`: tokens de entrada (incluida la caché), caché, salida y turnos
son `measured`; coste y ventana de contexto, `unavailable`. Una salida que no se puede interpretar
se conserva intacta y su uso queda `unavailable`.

| Regla | Señal | Niveles predeterminados |
|---|---|---|
| `repeated_instruction` | Misma instrucción normalizada al mismo agente sin avance verificado entre envíos | 2 WARNING · 3 PAUSE · 4 intervención |
| `handoff_cycle` | Ciclo de 2–3 agentes repetido tras el último avance verificado | 3 · 4 · 5 |
| `repeated_error` | Error equivalente (misma firma) en la ventana | 2 · 3 · 5 |
| `no_progress` | Turnos sin bloque o confirmaciones sin cambio en artefactos declarados, seguidos | 2 · 3 · 4 |
| `repeated_clarification` | Handoff a HUMANO con los mismos puntos abiertos | 2 · 3 · 4 |
| `permission_blocked` | Diálogo o permiso pendiente (Herdr `blocked` o diálogo antes del envío) | 1 WARNING · 3 intervención |
| `delivery_uncertain` | Entrega que pudo llegar al agente | intervención |
| `attempts`, `operation_duration`, `consecutive_operations`, `operations_per_session` | Presupuesto: intentos (PAUSE); duración activa, envíos seguidos y tareas en la generación actual (WARNING; recomiendan `--plan-clear` y CLEAR/ROTATE manual) | ver `budget` |

Configuración propuesta para la sección `ai` de `config_bmad.json` (los valores de `budget` y
`loop` son los predeterminados; `providers` y `agents` aceptan los mismos campos que `budget`):

```json
{"ai": {"guard": {
  "mode": "observe", "window_seconds": 21600, "retention_days": 14,
  "budget": {"max_operation_seconds": 3600, "max_attempts": 2, "max_consecutive_operations": 8,
             "max_operations_per_session": 15, "max_input_tokens": null, "max_output_tokens": null,
             "max_cost_usd": null},
  "providers": {"codex": {"max_operation_seconds": 5400}},
  "agents": {"dev-backend": {"max_operations_per_session": 10}},
  "loop": {"no_progress": {"warning": 2, "pause": 3, "intervention": 4}}
}}}
```

Recuperación tras una alerta: revisa el panel y el tracker; si el contexto está degradado,
consulta `--plan-clear` y aplica CLEAR/ROTATE manual (reinicia solo `operations_per_session`);
después reconoce la regla con `--acknowledge REGLA:AGENTE --confirm` (`*` para `handoff_cycle`).
Los eventos anteriores al reconocimiento dejan de contar y una tarea retenida se despacha en el
siguiente ciclo. Eventos y alertas sobreviven a reinicios del watcher sin repetirse y se depuran
tras `retention_days`. Revertir el código deja registros `progress:` y `guard_*` sin consumidores.
