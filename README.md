# BMAD Framework Template

Motor Python para el flujo BMAD/SDD, perfiles de 15 roles, integración con Herdr y dashboard de supervisión. Los entregables, aplicación, handoffs y estado pertenecen al workspace seleccionado. La flota tiene 13 paneles (12 al omitir UX); backend y frontend se implementan mediante operaciones headless de SpecKit.

## Iniciar un nuevo proyecto

Requiere Python 3.10 o posterior, Git, Herdr abierto y los CLI nativos de los proveedores seleccionados, instalados y autenticados. El dashboard es opcional. Sigue la [guía operativa para iniciar proyectos](SETUP.md):

1. Prepara una sola instalación del motor y su entorno Python.
2. Inicializa un workspace independiente con ruta e ID explícitos.
3. Configura `project.json`, prepara Git propio y revisa ambos dry-runs.
4. Arranca la flota y luego el watcher en terminales separadas; entrega la idea a Business Storyteller.
5. Verifica artefactos y handoffs, atiende aprobaciones y detén los procesos de forma controlada.

Instala las dependencias siguiendo [SETUP.md](SETUP.md). Desde la raíz del motor, con el Python del entorno instalado:

```powershell
$Engine = (Get-Location).Path
$Python = Join-Path $Engine 'bmad-control-center/backend/.venv/Scripts/python.exe'
$Workspace = Join-Path (Split-Path $Engine -Parent) 'Proyecto A'
& $Python (Join-Path $Engine 'init_bmad.py') --workspace $Workspace --project proyecto-a
& $Python (Join-Path $Engine 'utils/start_agents.py') --workspace $Workspace --dry-run
& $Python (Join-Path $Engine 'watcher_bmad.py') --workspace $Workspace --dry-run
```

Init es aditivo: conserva archivos existentes y no inicializa Git. Los dry-runs muestran comandos sin iniciar agentes ni crear SQLite. Claude y Codex tienen adaptadores interactivos y headless; Gemini está registrado y devuelve capacidades pendientes. La selección y `effort` se configuran por fase, agente y operación.

## Registrar, configurar y ejecutar

El motor incluye un registro `projects` vacío en `config_bmad.json`. No es un workspace
de aplicación: launcher y watcher requieren `--workspace` o `--project`.
Tras inicializar el workspace, añade su ruta al registro sin borrar otros proyectos:

```powershell
$ConfigPath = Join-Path $Engine 'config_bmad.json'
$Config = Get-Content -LiteralPath $ConfigPath -Raw | ConvertFrom-Json
$Config.projects | Add-Member -NotePropertyName 'proyecto-a' -NotePropertyValue $Workspace
$Config | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $ConfigPath -Encoding utf8
& $Python utils/start_agents.py --project proyecto-a --dry-run
```

En `project.json`, `config.ai` permite overrides de `defaults`, `phases` (B/M/A/D),
`agents` y `speckit`. Por ejemplo, dentro de `config.ai.defaults`:
`{"provider":"codex","model":null,"options":{"effort":"medium"}}`.
`model: null` usa el modelo del CLI; reemplázalo por un modelo disponible para tu proveedor.
Los valores globales y ejecutables están en `config_bmad.json`; conserva sus ajustes al registrar.
La precedencia es defaults → fase → agente u operación. El runtime traduce effort a flags
nativos y rechaza capacidades no soportadas; no cambia de proveedor automáticamente.
Consulta los [ejemplos de configuración](examples/config_bmad.mixed.json).

Con Herdr abierto, los CLI autenticados y Git propio preparado en el workspace:

```powershell
& $Python utils/start_agents.py --project proyecto-a
# En otra terminal, con el mismo Python y motor:
& $Python watcher_bmad.py --project proyecto-a
```

Entrega la idea a Business Storyteller y atiende los gates humanos del tracker de ese
workspace. Cada proyecto usa sus propias sesiones, locks, cola, logs y estado.

## Brownfield y Greenfield

La [constitución del motor](constitution.md) gobierna operación, aislamiento y
GitOps. Cada workspace conserva su constitución técnica en
`.specify/memory/constitution.md`, compartida con Spec Kit. El runtime ensambla
política global, constitución local, índice técnico por rol y tarea; no hereda el
stack de otros proyectos. Las guías completas se consultan bajo demanda.

En Brownfield, configura `project.json.config.code_dirs` con las carpetas reales
(por ejemplo `server` y `web`, sin moverlas a `app`). Inspecciona el contexto sin
lanzar agentes:

```powershell
& $Python utils/manage_workspace.py context --workspace $Workspace --role solutions-architect
& $Python utils/manage_workspace.py context --workspace $Workspace --record
```

`--record` guarda observaciones y diferencias en
`documents/architecture/stack-observations.json`; no altera decisiones ni
dependencias. Registra el stack aprobado en `documents/architecture/tech-stack.md`,
arquitectura y ADRs locales, enlazados desde la constitución. En Greenfield sin
stack, el estado sigue pendiente hasta aprobación humana y revisión QT.
| Documento | Finalidad |
|---|---|
| [SETUP.md](SETUP.md) | Dependencias, instalación, preparación, recorrido multiworkspace, diagramas y diagnóstico |
| [bmad_runtime/README.md](bmad_runtime/README.md) | Comandos, rutas, configuración, proveedores, effort y recuperación |
| [GUIDE.md](GUIDE.md) | Operación del flujo, gates y solución de problemas |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Componentes y límites del sistema |
| [framework_bmad.md](framework_bmad.md) | Principios BMAD/SDD y adaptación del stack |
| [INPUTS_POR_AGENTE.md](INPUTS_POR_AGENTE.md) | Entradas, entregables y responsabilidades de cada rol |
| [Backend](bmad-control-center/backend/README.md) y [frontend](bmad-control-center/frontend/README.md) | Ejecución y pruebas del dashboard |

## Supervisión desde el dashboard

Instala sus dependencias con [SETUP.md](SETUP.md). Puedes iniciar la consola sin
proyectos: muestra el registro vacío sin observar archivos ni habilitar compuertas.

```powershell
& $Python -m uvicorn main:app --app-dir bmad-control-center/backend --host 127.0.0.1 --port 8000
# En otra terminal:
npm --prefix bmad-control-center/frontend run dev -- --port 3000
```

Para supervisar un proyecto, define `$env:BMAD_PROJECT = 'proyecto-a'` antes de
iniciar su backend. También puedes seleccionar una ruta con `BMAD_WORKSPACE`.
El registro se muestra y se actualiza en la consola; cada backend mantiene un proyecto fijo.
Para varias instancias usa puertos distintos y define `VITE_BMAD_API_BASE` en cada frontend,
por ejemplo `http://localhost:8001/api/v1`. HTTP y WebSocket apuntan al mismo proyecto.
No es necesario registrar un proyecto para usar su ruta explícita.

## Validación local

```powershell
& $Python -B tests/run_isolated.py tests -q
& $Python -B tests/validate_offline.py
& $Python -B tests/run_isolated.py bmad-control-center/backend/tests -q
npm --prefix bmad-control-center/frontend test
npm --prefix bmad-control-center/frontend run build
```

La comprobación offline valida imports, ayuda CLI, ejemplos JSON, enlaces y planes de dos proyectos con los tres proveedores, sin flota ni reportes. Las pruebas de ayuda de CLIs reales son optativas con `BMAD_TEST_REAL_CLI=1`; el harness aislado las desactiva.
