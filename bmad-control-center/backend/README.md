# BMAD Control Center — Backend API (FastAPI)

Servicio backend asíncrono reactivo para el **BMAD Control Center**, implementado sobre **FastAPI**, **Uvicorn**, **Watchdog** y **WebSockets**. Provee monitoreo en tiempo real del pipeline agéntico, exploración segura de entregables (árbol de archivos), inspección de especificaciones Markdown, telemetría de observabilidad y auditoría de control de versiones Git.

---

## Arquitectura del Sistema

El backend está concebido bajo el paradigma **File-System as a Database (FSaaDB)**, actuando como un envoltorio reactivo y seguro sobre el espacio de trabajo local de los agentes del ecosistema BMAD. No requiere bases de datos relacionales ni servicios externos en la nube; opera estrictamente sobre localhost (`127.0.0.1`).

### Principios y Patrones Arquitectónicos
1. **Asincronía Total No Bloqueante (`async/await`):** Todos los endpoints y listeners de WebSocket son asíncronos. La lectura de archivos documentales se delega a `aiofiles` y las consultas Git se ejecutan mediante subprocesos asíncronos nativos para no bloquear el loop de eventos de Uvicorn.
2. **File-System as a Database (FSaaDB):** El archivo central `documents/tracker_bmad.md` y los directorios autorizados (`documents/`, `specs/`, `.specify/`) son la única fuente de verdad (SSOT).
3. **Observabilidad Reactiva con Watchdog Multi-Raíz y Git:** Un observador en background (`Observer`) monitorea en tiempo real todas las raíces autorizadas (`documents/`, `specs/`, `.specify/`) e intercepta mutaciones en `.git/HEAD` y `.git/refs/heads/`, emitiendo notificaciones en caliente (`WORKFLOW_UPDATED`, `ARTIFACT_CHANGED`, `GIT_STATUS_CHANGED`).
4. **Sandboxing Canónico Estricto y Descarte Silencioso (ADR-007 / ADR-012):** Validación perimetral en dos niveles (`is_path_in_perimeter` y `validate_sandbox_path`) mediante resolución canónica (`os.path.realpath` y `os.path.commonpath`). Confinamiento estricto a las raíces autorizadas. Cualquier evento externo (e.g. temporales del host, `.idea/`, `node_modules/`) es descartado silenciosamente en el backend (0% de fugas hacia el WebSocket, Criterio SC-004) e incrementa el contador de telemetría `ignored_external_events_count`.
5. **Amortiguación de Ráfagas I/O (Debounce 200ms - ADR-010):** Módulo de coalescencia en backend (`EventDebouncer`) indexado por ruta de archivo. Agrupa ráfagas continuas de escritura física en una ventana temporizada de 200ms, emitiendo 1 único evento consolidado (`coalesced_count: N`) y evento complementario `SYSTEM_NOTICE`, erradicando la saturación del WebSocket y congelamientos en la UI.
6. **Política Metadata-Only para Archivos Extensos (>5MB - ADR-012 / CB-05):** Para cualquier archivo que supere los 5 MB (`5.242.880 bytes`), el evento `ARTIFACT_CHANGED` propaga exclusivamente `FileMetadataRecord` con `metadata_only = true` e `is_large_file = true`, omitiendo la lectura y transmisión de contenido crudo para proteger la memoria del cliente.
7. **Operación Git Estrictamente de Solo Lectura (Strict Read-Only / ADR-013):** La API de telemetría Git expone exclusivamente consultas pasivas (`GET /api/v1/git/status`, `/commits`, `/branches`). Cero mutaciones en la consola web para preservar la soberanía transaccional del Watcher y del operador humano.
8. **Invocación Asíncrona Git Porcelain v2 con SLA < 300ms (ADR-014):** Invocación segura mediante subproceso nativo sin shell (`asyncio.create_subprocess_exec("git", ..., shell=False)`), parser determinista de Porcelain v2 y elisión de diffs binarios o masivos (>1MB) garantizando tiempos de respuesta ultrarrápidos.
9. **Resiliencia ante Contención `.git/index.lock` y Aislamiento 404 (ADR-015):** Detección defensiva de colisiones por bloqueo de Git con reintentos escalonados (50ms, 100ms, 200ms) y fallback elegante hacia snapshot en memoria con bandera `is_syncing: true` (0% errores 5xx). Repositorios no inicializados son capturados como `GIT_REPO_NOT_FOUND` (HTTP 404 estructurado RFC 7807) para despliegue de Empty State sin afectar los otros módulos.
10. **Frame Protocol Guard y Blindaje WebSocket (WS 1008 - ADR-011 / ADR-012):** El canal `/ws/v1/events` valida la integridad de cada trama entrante. Si un cliente envía tramas corruptas no conformes a JSON o payloads no-diccionario, el servidor cierra inmediatamente el socket con código WS 1008 Policy Violation.

### Estructura de Directorios
```text
bmad-control-center/backend/
├── main.py                   # Entrypoint ASGI, ciclo de vida (lifespan), CORS y manejadores de error
├── pytest.ini                # Configuración de pruebas Pytest
├── requirements.txt          # Dependencias de producción y pruebas
├── README.md                 # Documentación viva de arquitectura y ejecución
├── api/
│   ├── routes.py             # Enrutador REST principal y compuertas HITL (HU-001)
│   ├── workflow.py           # GET /api/v1/workflow/status y /workflow/state (US1)
│   ├── artifacts.py          # GET /api/v1/artifacts/tree y /artifacts/content (US1/US2)
│   ├── observability.py      # GET /api/v1/observability/perimeter/status (Telemetría HU-003)
│   ├── git.py                # GET /api/v1/git/status, /commits, /branches (Telemetría HU-004)
│   └── websockets.py         # WS /ws/v1/events, /api/v1/ws/monitor, /ws/hitl (Guard WS 1008)
├── core/
│   ├── config.py             # Configuración central (umbrales 5MB, debounce 200ms)
│   └── security.py           # is_path_in_perimeter, validate_sandbox_path y contador de descartes
├── models/
│   ├── workflow.py           # Modelos Pydantic v2: WorkflowStageStep y WorkflowStatusResponse
│   ├── directory.py          # Modelos Pydantic v2: DirectoryNode y ArtifactTreeResponse
│   ├── artifact.py           # Modelo Pydantic v2: ArtifactContent con validación de 5MB
│   ├── observability.py      # Modelos Pydantic v2: WebSocketEventMessage, FileMetadataRecord, Payloads
│   ├── git.py                # Modelos Pydantic v2: GitStatusResponse, GitCommitListResponse, GitBranchListResponse
│   ├── errors.py             # Modelo RFC 7807: ErrorResponse
│   └── schemas.py            # Re-exportador unificado de esquemas
├── services/
│   ├── workflow_service.py   # Parser inverso de tracker_bmad.md y proyección de 8 fases canónicas
│   ├── artifact_service.py   # Escaneo recursivo de directorios y lectura segura de entregables
│   ├── workspace_service.py  # Wrapper interoperable del servicio de espacio de trabajo
│   ├── git_service.py        # Invocador asíncrono Git CLI, parser Porcelain v2, fallback de lock y caché
│   ├── file_watcher.py       # Observador de Watchdog multi-carpeta con sandboxing perimetral y .git/HEAD
│   ├── event_debouncer.py    # Búfer de amortiguación de 200ms y coalescencia de ráfagas I/O
│   ├── connection_manager.py # Gestor de WebSockets multiplexados, latidos y broadcast enriquecido
│   └── tracker_service.py    # Servicio FSaaDB atómico con filelock sobre tracker_bmad.md
└── tests/
    ├── test_gates.py                     # Pruebas de compuertas HITL (HU-001)
    ├── test_security_and_schemas.py      # Pruebas de validación Pydantic y sanitización
    ├── test_tracker_service.py           # Pruebas de persistencia atómica FSaaDB
    ├── test_workflow_api.py              # Pruebas del pipeline de 8 etapas y parsing de tracker
    ├── test_artifacts_api.py             # Pruebas de árbol, lectura y detección de directorios vacíos
    ├── test_path_traversal_security.py   # Auditoría de seguridad contra Directory Traversal
    ├── test_payload_limit.py             # Pruebas de límite de 5MB y formatos binarios no soportados
    ├── test_websockets_api.py            # Pruebas de canal WebSocket y latido PING/PONG base
    ├── test_websocket_events.py          # Pruebas de sobres de eventos WS estructurados (HU-003)
    ├── test_event_debouncer.py           # Pruebas de coalescencia y debounce de 200ms (HU-003)
    ├── test_perimeter_sandboxing.py      # Pruebas de descarte silencioso y telemetría de perímetro
    ├── test_websocket_malformed_frame.py # Pruebas de cierre WS 1008 ante tramas corruptas
    ├── test_large_file_metadata.py       # Pruebas de política Metadata-Only (>5MB)
    ├── test_git_api.py                   # Pruebas de endpoints /status, /commits y /branches (HU-004)
    ├── test_git_lock_contention.py       # Pruebas de resiliencia ante index.lock y fallback (HU-004)
    ├── test_git_repo_not_found.py        # Pruebas de error 404 ante repositorios no inicializados (HU-004)
    ├── test_git_binary_and_sanitization.py # Pruebas de elisión de diffs binarios y sanitización (HU-004)
    ├── test_git_pagination_performance.py # Pruebas de rendimiento paginado SLA < 300ms (HU-004)
    └── unit/
        └── test_fs_utils.py              # Pruebas unitarias de validación canónica de rutas
```

---

## Cómo Compilar y Ejecutar

### 1. Requisitos Previos
- Python 3.10+ (Recomendado: Python 3.11 o superior).
- Git CLI nativo instalado y disponible en el `PATH` del sistema.
- Gestor de paquetes `uv` (recomendado) o `pip` con `venv`.

### 2. Configuración del Entorno Virtual e Instalación

#### Con `uv` (Recomendado por alto rendimiento):
```bash
cd bmad-control-center/backend
uv venv .venv --python 3.14
uv pip install -r requirements.txt
```

#### Con `pip` estándar:
```bash
cd bmad-control-center/backend
python -m venv .venv

# En Windows (PowerShell):
.venv\Scripts\Activate.ps1   # pip
.venv\Scripts\activate  # uv

# En Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt -q
```

### 3. Ejecución de la Suite Completa de Pruebas (Pytest)
Desde la raíz del repositorio o dentro de `bmad-control-center/backend/`:
```bash
cd bmad-control-center/backend
uv run pytest
```
O con el ejecutable local del entorno virtual:
```powershell
.\.venv\Scripts\pytest.exe tests/ -v
```

### 4. Ejecución del Servidor Backend en Modo Desarrollo
Para iniciar el servidor ASGI en `127.0.0.1:8000` con hot-reloading:
```bash
cd D:\Paulo\Cursos\DMC\template-bmad
uv run --directory bmad-control-center/backend uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
Una vez levantado, la documentación Swagger interactiva y telemetría estarán disponibles en:
- Swagger UI: `http://127.0.0.1:8000/docs`
- Redoc: `http://127.0.0.1:8000/redoc`
- Telemetría de Git (Status): `http://127.0.0.1:8000/api/v1/git/status`
- Telemetría de Git (Commits): `http://127.0.0.1:8000/api/v1/git/commits`
- Telemetría de Git (Branches): `http://127.0.0.1:8000/api/v1/git/branches`
- Telemetría de Perímetro: `http://127.0.0.1:8000/api/v1/observability/perimeter/status`
- WebSocket de Eventos: `ws://127.0.0.1:8000/ws/v1/events`

### 5. Verificación Rápida de Sintaxis (Headless Compile)
```bash
uv run python -m py_compile bmad-control-center/backend/main.py bmad-control-center/backend/api/git.py bmad-control-center/backend/services/git_service.py
```
