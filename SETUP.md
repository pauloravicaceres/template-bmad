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
| Claude | Interactivo y headless | `low`, `medium`, `high`, `xhigh`, `max` → `--effort NIVEL` | `permission_mode`: `manual`, `plan`, `acceptEdits`, `bypass` (→ `--dangerously-skip-permissions`; default en interactivo/herdr, `manual` en headless); `max_budget_usd` positivo hasta 1000, solo headless |
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
| `projects` | Raíz global | `{"proyecto-a":"../Proyecto A"}` | Selección por ID; rutas relativas al archivo |

El proyecto no puede cambiar ejecutables, límites, Git, tracker ni registro. Con `projects`
presente, aunque esté vacío, todo comando exige seleccionar un workspace. Sin ese registro el
runtime entra en modo legacy (motor como proyecto) con advertencia de obsolescencia; el template
no lo usa. Hay ejemplos en [examples/](examples/config_bmad.mixed.json) y un registro de dos
proyectos en [examples/multiworkspace.config.json](examples/multiworkspace.config.json).

`init_bmad.py`, `utils/manage_workspace.py`, `utils/start_agents.py` y `watcher_bmad.py` admiten
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

Comprobaciones sin borrar archivos:

```powershell
Get-Content -Raw -LiteralPath (Join-Path $Workspace 'project.json') | ConvertFrom-Json
herdr tab list
herdr pane list
git -C $Workspace status
```

Recuperación de un proyecto en ejecución: [GUIDE.md](GUIDE.md#13-recuperación).
