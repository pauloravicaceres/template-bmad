# Dashboard BMAD: backend

API FastAPI con Watchdog y WebSockets. La entrada ASGI es `main:app`. `core/config.py` selecciona un workspace al importar la aplicación mediante `BMAD_WORKSPACE` y `BMAD_PROJECT`; sin selección inicia una consola de registro vacía, sin observadores ni operaciones de proyecto. Lee configuración global y overrides con el mismo mecanismo del runtime.

## Ejecución

Desde la raíz del motor, tras [instalar las dependencias](../../SETUP.md):

```powershell
$Engine = (Get-Location).Path
$Python = Join-Path $Engine 'bmad-control-center/backend/.venv/Scripts/python.exe'
$env:BMAD_WORKSPACE = Join-Path (Split-Path $Engine -Parent) 'Proyecto A'
$env:BMAD_PROJECT = 'proyecto-a'
& $Python -m uvicorn main:app --app-dir (Join-Path $Engine 'bmad-control-center/backend') --host 127.0.0.1 --port 8001
```

Usa un proceso y puerto por proyecto. Reinicia para cambiar workspace. Este backend no ofrece `--config` del launcher. `Settings.CORS_ORIGINS` declara localhost:3000 y 127.0.0.1:3000; `main.py` agrega `*` al middleware CORS. No existe configuración de CORS por variable de entorno.

## Componentes

| Ruta | Responsabilidad |
|---|---|
| `main.py` | App, lifespan, CORS y errores estructurados |
| `core/config.py`, `core/security.py` | Contexto de proyecto, límites y validación de rutas |
| `api/` | Workflow, artefactos, gates, observabilidad, Git y WebSocket |
| `models/` | Contratos Pydantic |
| `services/tracker_service.py`, `workflow_service.py` | Lectura del tracker y proyección de etapas, alertas y retrabajo |
| `services/artifact_service.py` | Árbol y lectura de entregables dentro del perímetro |
| `services/file_watcher.py`, `event_debouncer.py`, `connection_manager.py` | Observación, coalescencia y eventos por instancia |
| `services/git_service.py` | Telemetría Git de solo lectura y snapshots |

## API

Los endpoints REST usan `/api/v1`: `/project`, `/projects`, `/project/context`, `/workflow/status` (alias `/workflow/state`), `/artifacts/tree`, `/artifacts/content`, `/gates/status`, `/gates/{gate_id}/decision`, `/observability/perimeter/status` y `/git/status`, `/git/commits`, `/git/branches`. Las rutas `/workspace/tree` y `/workspace/file` delegan al mismo servicio de artefactos.

El canal canónico es `/ws/v1/events`; los alias `/api/v1/ws/monitor`, `/ws/hitl` y `/ws` comparten el mismo manejador. Envía frames JSON; PING recibe PONG y los frames inválidos cierran con WS 1008.

Las raíces documentales son `documents`, `specs`, `.specify` y, en multiworkspace, `handoffs`. El observador compara la ruta completa del tracker. Las compuertas escriben decisiones en ese tracker; sockets, cachés y observadores pertenecen al proceso seleccionado. Los eventos de archivos mayores de 5 MiB llevan metadatos; la ventana de debounce es 200 ms.

## Pruebas

Desde la raíz del motor:

```powershell
& $Python -B tests/run_isolated.py bmad-control-center/backend/tests -q
```

Instala las dependencias de [requirements.txt](requirements.txt), incluido AnyIO. Las pruebas Git deben usar repositorios temporales: no crees `index.lock` en el repositorio del usuario. Los contratos del motor y su matriz offline están documentados en [README](../../README.md#validación-local).

Sin selección, `/project` devuelve identidad y ruta nulas y `/projects` lista el registro global.
Las demás rutas de proyecto responden 409 y los WebSockets se cierran sin observar el motor.
Registrar un workspace consiste en añadir su ID y ruta a `config_bmad.json.projects`;
la lista se refresca sin reinicio. Seleccionar otro workspace requiere otro proceso.
Las pruebas usan directorios temporales y dobles de Git; no crean commits ni locks en el motor.
