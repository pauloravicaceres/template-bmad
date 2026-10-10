# Guía de operación BMAD

Procedimientos para crear workspaces, arrancar y detener agentes, operar el watcher y el
dashboard y localizar resultados. Requiere el motor instalado según [SETUP.md](SETUP.md). La
arquitectura y los diagramas de flujo están en [ARCHITECTURE.md](ARCHITECTURE.md).

Todos los comandos se ejecutan en PowerShell desde la raíz del motor con estas variables:

```powershell
$Engine = (Get-Location).Path
$Python = Join-Path $Engine 'bmad-control-center/backend/.venv/Scripts/python.exe'
$Workspace = Join-Path (Split-Path $Engine -Parent) 'Proyecto A'
$Project = 'proyecto-a'
```

Cada comando selecciona el proyecto con `--workspace` y/o `--project`. La selección explícita
reemplaza `BMAD_WORKSPACE`/`BMAD_PROJECT`; sin ninguna, el motor rechaza ejecutar porque el
registro `projects` existe en `config_bmad.json`.

## 1. Crear un workspace

```powershell
& $Python (Join-Path $Engine 'init_bmad.py') --workspace $Workspace --project $Project
if ($LASTEXITCODE -ne 0) { throw 'Falló el bootstrap; revisa el error.' }
Get-Content -LiteralPath (Join-Path $Workspace 'project.json')
```

`init_bmad.py` equivale a `utils/manage_workspace.py init`; `--dry-run` muestra el contexto sin
crear nada. Crea la ruta si falta. El ID admite 1–64 letras ASCII, dígitos, `_` o `-`, empieza
por letra o dígito y no puede ser un nombre reservado de Windows. Si `project.json` existe, el ID
debe coincidir.

Bootstrap es aditivo: no sobrescribe archivos, no vacía el tracker, no inicializa Git y no
actualiza los snapshots de Spec Kit al repetirse. Resultado inicial:

```text
Proyecto A/
├── project.json                    identidad y overrides
├── AGENTS.md                       contrato de rutas del workspace
├── docs/<rol>/                     15 carpetas, más business-analyst/HUs-stakeholders/
├── app/                            vacío; código en app/backend y app/frontend por defecto
├── handoffs/tracker_bmad.md        vacío
├── specs/README.md                 ledger de HUs
├── .specify/memory/constitution.md constitución técnica neutral, stack pendiente
├── .specify/scripts/, templates/   snapshot de Spec Kit
├── state/config_bmad.json          vista efectiva generada
├── state/bootstrap.lock            permanece tras liberar el lock
└── logs/, temp/                    vacíos
```

Para registrar el workspace por ID, añade su ruta a `projects` sin borrar otros proyectos:

```powershell
$ConfigPath = Join-Path $Engine 'config_bmad.json'
$Config = Get-Content -LiteralPath $ConfigPath -Raw | ConvertFrom-Json
$Config.projects | Add-Member -NotePropertyName $Project -NotePropertyValue $Workspace
$Config | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $ConfigPath -Encoding utf8
```

Las rutas del registro se anclan al directorio de `config_bmad.json`; las de `--workspace`, al
motor. Un ID o ruta incorrectos fallan sin adoptar otro proyecto.

## 2. Preparar el proyecto

### Configuración del proyecto

Edita `project.json` conservando la identidad. Ejemplo mínimo que hereda la selección IA global:

```json
{
  "schema_version": 1,
  "project_id": "proyecto-a",
  "config": {
    "project_name": "Proyecto A",
    "project_type": "fullstack",
    "ux_phase": "auto",
    "code_dirs": {"backend": "app/backend", "frontend": "app/frontend"}
  }
}
```

Claves, overrides de proveedor/modelo/effort y precedencia: [SETUP.md](SETUP.md#configuración).

### Constitución y stack

`ENGINE_ROOT/constitution.md` es la política operativa compartida; no se edita por proyecto.
La constitución técnica del proyecto es `.specify/memory/constitution.md` del workspace, la
misma que usa Spec Kit. Bootstrap la crea neutral, con stack pendiente: su existencia no implica
Brownfield ni aprobación. Registra el inventario en `docs/architecture/tech-stack.md`, la
arquitectura en `docs/architecture/architecture.md` y las decisiones en
`docs/architecture/adr/`, y enlázalos desde la constitución. Cada decisión indica
Observado, Propuesto, Aprobado (con evidencia) o Pendiente.

**Brownfield.** Conserva el árbol existente y apunta `code_dirs` a las carpetas reales, por
ejemplo `{"backend": "server", "frontend": "web"}`, sin moverlas a `app/`. Inspecciona el
contexto sin lanzar agentes:

```powershell
& $Python (Join-Path $Engine 'utils/manage_workspace.py') context --workspace $Workspace --role solutions-architect
& $Python (Join-Path $Engine 'utils/manage_workspace.py') context --workspace $Workspace --record
```

`--record` guarda fuentes, versiones observadas y diferencias con `tech-stack.md` en
`docs/architecture/stack-observations.json`. No aprueba decisiones ni modifica
dependencias. El escaneo omite secretos, enlaces y workspaces anidados e informa sus límites.
Con Python 3.10 la lectura detallada de `pyproject.toml` queda pendiente; Python 3.11+ la incluye.

**Greenfield.** Con stack aprobado, regístralo en la constitución antes de planificar. Sin
stack, Solutions Architect propone opciones y solicita aprobación con `@HUMANO:`; QA Tech
verifica coherencia después. Un plan generado no concede aprobación.

### Git del workspace

GitOps exige un repositorio propio del workspace; el runtime rechaza un Git padre y nunca
inicializa repositorios. En un workspace nuevo:

```powershell
git -C $Workspace init
# Crea primero el .gitignore del proyecto: secretos, dependencias, state/, logs/, temp/.
git -C $Workspace add .
git -C $Workspace diff --cached --stat
git -C $Workspace commit -m 'chore: initialize BMAD workspace'
git -C $Workspace rev-parse --show-toplevel
```

La última salida debe ser exactamente el workspace. Revisa repositorios existentes antes de
aplicar estos pasos.

## 3. Revisar sin ejecutar agentes

```powershell
& $Python (Join-Path $Engine 'utils/start_agents.py') --workspace $Workspace --project $Project --dry-run
& $Python (Join-Path $Engine 'watcher_bmad.py') --workspace $Workspace --project $Project --dry-run
```

Comprueba en el JSON `project_id`, `workspace`/`cwd`, `tracker`, proveedor, modelo y flags de
effort, y que no haya filas `pending` (pueden aparecer con código de salida cero).
`verified_cli_contract` significa comando construido, no CLI ejecutado ni autenticado. Ningún
dry-run lanza procesos ni crea SQLite.

La flota tiene 13 paneles en 3 tabs (12 si se omite UX). Dev Backend y Dev Frontend no tienen
panel: se ejecutan como directiva de Spec Kit `implement`. El dry-run del watcher lista las siete
operaciones Spec Kit.

## 4. Arrancar flota y watcher

Con Herdr abierto y los proveedores autenticados:

```powershell
& $Python (Join-Path $Engine 'utils/start_agents.py') --workspace $Workspace --project $Project
```

El launcher verifica proveedores y Herdr, crea tres tabs, registra la propiedad en SQLite y
termina; los agentes quedan esperando. Rechaza nombres de sesión existentes y no reemplaza
sesiones. Comprueba con `herdr agent list`.

En **otra terminal**, con las mismas variables:

```powershell
& $Python (Join-Path $Engine 'watcher_bmad.py') --workspace $Workspace --project $Project
```

Debe indicar que escucha `handoffs/tracker_bmad.md` del proyecto. Un segundo watcher sobre el
mismo workspace falla por lock. En el primer arranque con un tracker no vacío y sin cursor
guardado pregunta si reanudar **la última línea**; arrancar el watcher antes de entregar la idea
evita esa pregunta.

## 5. Entregar la idea y supervisar

Selecciona el panel cuyo nombre termina en `business-storyteller` (incluye ID y hash del
workspace) y pega la idea con actores, problema, objetivo, alcance y restricciones. No existe
importación automática de un archivo inicial. Ejemplo:

```text
Gestionamos las citas de un centro por teléfono y se producen cruces de horario.
Recepción necesita registrar y consultar reservas. Empezamos con una agenda interna,
sin pagos ni acceso de clientes. Estructura esta idea según tu perfil y el contrato del workspace.
```

Business Storyteller guarda la narrativa en `docs/business-storyteller/idea_<nombre>.md` y
anexa el handoff `@PA:`. Sigue el tracker en otra terminal:

```powershell
Get-Content -LiteralPath (Join-Path $Workspace 'handoffs/tracker_bmad.md') -Tail 40 -Wait
```

## 6. Flujo de una historia

El diagrama completo está en [ARCHITECTURE.md](ARCHITECTURE.md#6-flujo-bmad--sdd).

1. Business Storyteller estructura la idea; Product Analyst redacta el Product Brief, que se
   aprueba en una pausa `@HUMANO:`.
2. Product Manager prioriza el MVP, selecciona una HU, asigna el correlativo de `specs/README.md`
   y abre la rama con `GITOPS-BRANCH-CREATE`. Business Analyst produce la HU técnica y la
   narrativa para stakeholders; QA Documental valida.
3. Tras la aprobación de QA, el watcher ejecuta `specify` y `clarify`. La carpeta de feature debe
   coincidir con el identificador de la HU. Una ambigüedad pausa el flujo hasta la respuesta humana.
4. `ux_routing.py` decide UX según `project_type`, `ux_phase` y `Requiere interfaz: Sí|No`.
5. Solutions Architect publica guidelines y emite `@WATCHER: SDD-FREEZE`; el watcher ejecuta
   `plan`, `tasks` y `analyze`, hace el commit de freeze y deriva a Data Architect. API Architect
   interviene si hace falta; QA Tech revisa el diseño.
6. El watcher ejecuta `implement` para backend y después frontend. QA Automation verifica y Code
   Review dictamina.
7. Un rechazo activa `analyze → converge → implement` (máximo dos iteraciones; luego escala al
   humano). La aprobación cierra la rama con `GITOPS-MERGE-CLOSE` y permite la siguiente HU.

Una HU se completa antes de abrir la siguiente. El identificador `XXX-HU_nombre_en_snake_case`
se conserva sin truncar en HU, carpeta de spec, rama y handoffs.

## 7. Entradas y entregables por rol

Cada rol lee la configuración efectiva (`BMAD_CONFIG`), el tracker (`BMAD_TRACKER`), la
constitución del workspace y los artefactos de su tarea. Perfiles, skills y plantillas se leen
desde `ENGINE_ROOT`; las rutas de la tabla son relativas al workspace. El contrato de rutas del
workspace prevalece sobre rutas legacy de los perfiles.

| Rol / token | Fase | Entradas principales | Salidas y siguiente paso |
|---|---|---|---|
| Business Storyteller / `@BS:` | B | Idea del humano | `docs/business-storyteller/idea_*.md`; PA |
| Product Analyst / `@PA:` | B | Idea estructurada | `docs/product-analyst/pb_*.md`; aprobación humana |
| Product Manager / `@PM:` | M | PB aprobado, ledger y backlog | `docs/product-manager/mvp_*.md`; priorización, rama y BA |
| Business Analyst / `@BA:` | M | PB, MVP, HU y feedback de QA | HU técnica en `docs/business-analyst/` y narrativa en `HUs-stakeholders/`; QA |
| QA Documental / `@QA:` | M | HU y PB | Aprobación o feedback en `docs/qa-documental/`; specify/clarify o BA |
| Designer UX / `@UX:` | A | HU, spec y PB | `docs/designer-ux/ux_*.md`; SA |
| Solutions Architect / `@SA:` | A | PB, MVP, spec, UX y constitución | `docs/solutions-architect/tech_guidelines.md`; SDD-FREEZE |
| Data Architect / `@DA:` | A | Guidelines, HU, spec, plan y tasks | `docs/data-architect/db_*.md`; API o QT |
| API Architect / `@API:` | A | Guidelines, datos y HU | `docs/api-architect/api_*.md`; QT |
| QA Tech / `@QT:` | A | Spec, guidelines, datos y contratos | `docs/qa-tech/tech-design_*.md`; implementación |
| Dev Backend (headless) | D | Spec, plan, tasks, contratos y perfil | Código en `code_dirs.backend`, `docs/dev-backend/backend-architecture.md` y README |
| Dev Frontend (headless) | D | Spec, plan, tasks, UX y contratos | Código en `code_dirs.frontend`, `docs/dev-frontend/frontend-architecture.md` y README |
| QA Automation / `@QA-AUTO:` | D | Código, criterios y tasks | Pruebas y `docs/qa-auto/qa-report.md`; Code Review o retrabajo |
| Code Review / `@CODE-REVIEW:` o `@CR:` | D | Código, pruebas, diseño y constitución | Dictamen en tracker y `docs/code-review/`; cierre o retrabajo |
| DevOps / `@DEVOPS:` | D | Diseño y aplicación aprobados | Infraestructura y documentación en el workspace |

Las operaciones headless no emiten handoffs propios: el watcher registra su resultado y deriva a
revisión.

## 8. Handoffs y aprobaciones

El tracker es `handoffs/tracker_bmad.md`. Cada entrada es un bloque con fecha, autor, hora,
artefacto, estado, puntos abiertos y una línea `Handoff` con un único token de destinatario. En
un aviso al humano, los demás agentes se nombran sin token para no disparar despachos.

Las macros GitOps van como líneas independientes antes del handoff:

```text
@WATCHER: GITOPS-BRANCH-CREATE feat/XXX-HU_nombre
@WATCHER: SDD-FREEZE
@WATCHER: GITOPS-MERGE-CLOSE feat/XXX-HU_nombre
```

Un `@HUMANO:` real pausa el despacho. Atiende la compuerta con:

```powershell
& $Python (Join-Path $Engine 'utils/approve_step.py') --workspace $Workspace --project $Project
& $Python (Join-Path $Engine 'utils/response_sa.py') --workspace $Workspace --project $Project
```

`approve_step.py` ofrece un menú y anexa la transición elegida; no acredita por sí solo las fases
previas. Su menú conserva opciones de despacho directo a desarrollo que no corresponden a la
flota actual: sigue la ruta Spec Kit. `response_sa.py` captura respuestas para Solutions
Architect hasta la línea `FIN`. El cierre `GITOPS-MERGE-CLOSE` pide confirmar el nombre de la
rama en la consola del watcher.

## 9. Dashboard

El dashboard es opcional (dependencias en [SETUP.md](SETUP.md#dependencias)). Un backend fija
un proyecto por proceso:

```powershell
$env:BMAD_PROJECT = $Project      # o $env:BMAD_WORKSPACE = $Workspace
& $Python -m uvicorn main:app --app-dir (Join-Path $Engine 'bmad-control-center/backend') --host 127.0.0.1 --port 8001
# En otra terminal:
$env:VITE_BMAD_API_BASE = 'http://localhost:8001/api/v1'
npm --prefix (Join-Path $Engine 'bmad-control-center/frontend') run dev -- --port 3001
```

Sin `BMAD_PROJECT` ni `BMAD_WORKSPACE` el backend arranca como consola de registro: lista
`projects` y no observa archivos ni habilita compuertas. Comprueba `GET /api/v1/project` antes
de operar compuertas. El panel muestra etapas, compuertas, entregables, eventos y telemetría Git;
`GET /api/v1/project/context` expone el índice técnico del workspace. Detalles de API y
frontend: [backend](bmad-control-center/backend/README.md) y
[frontend](bmad-control-center/frontend/README.md).

## 10. Varios proyectos

Usa el mismo motor y Python; no clones el motor por proyecto.

```powershell
$WorkspaceB = Join-Path (Split-Path $Engine -Parent) 'Proyecto B'
& $Python (Join-Path $Engine 'init_bmad.py') --workspace $WorkspaceB --project proyecto-b
& $Python (Join-Path $Engine 'utils/start_agents.py') --workspace $WorkspaceB --project proyecto-b --dry-run
```

Cada proyecto necesita su launcher, su watcher en una terminal propia y, si se supervisa, su
backend y frontend con puertos distintos. No hay selector global persistente: puedes fijar la
selección en una terminal con `BMAD_WORKSPACE`/`BMAD_PROJECT` y limpiarla con
`Remove-Item Env:BMAD_WORKSPACE, Env:BMAD_PROJECT -ErrorAction SilentlyContinue`. Cambiar esas
variables no renombra ni detiene sesiones abiertas.

El aislamiento entre workspaces está probado con dobles, no con dos flotas reales en un mismo
Herdr: empieza operando un proyecto a la vez y comprueba paneles y puertos antes de operar en
paralelo. No compartas tracker ni `state/` entre proyectos. Ver
[ARCHITECTURE.md](ARCHITECTURE.md#9-orquestación).

## 11. Detener y reanudar

1. Detén el watcher con `Ctrl+C` y espera su salida. Si interrumpiste una operación headless,
   puede quedar `uncertain`.
2. Revisa `herdr agent list`, paneles y artefactos; espera a que los agentes estén idle/done.
3. Cierra los tabs propios:

```powershell
& $Python (Join-Path $Engine 'utils/stop_agents.py') --workspace $Workspace --project $Project --confirm
```

Sin `--confirm` no cierra nada; no ofrece `--dry-run` ni `--config`. Solo cierra tabs cuya
propiedad y estado idle/done verifica. No borres locks ni SQLite.

Si las sesiones siguen válidas, reinicia solo el watcher: recupera cursor, cola y rama abierta.
Si cerraste la flota, repite dry-runs, flota y watcher. Para inspeccionar registros no
terminados (sin watcher, flota ni Spec Kit activos):

```powershell
& $Python -B -m bmad_runtime.state --workspace $Workspace --project $Project
& $Python -B -m bmad_runtime.state --workspace $Workspace --project $Project --acknowledge 'event:ID' --confirm
```

El primero puede crear o abrir SQLite. El segundo marca como manejado un `event:`, `dispatch:` o
`queued:` ya inspeccionado; no lo reintenta ni completa la tarea de negocio.

## 12. Dónde están los resultados

| Resultado | Ubicación en el workspace |
|---|---|
| Entregables por rol | `docs/<rol>/` |
| Stack, arquitectura y ADRs | `docs/architecture/` |
| Especificaciones por HU | `specs/XXX-HU_nombre/` (`spec.md`, `plan.md`, `tasks.md`) |
| Ledger de HUs | `specs/README.md` |
| Código | `code_dirs.backend` y `code_dirs.frontend` (por defecto `app/backend`, `app/frontend`) |
| Arquitectura de capas | `docs/dev-backend/backend-architecture.md`, `docs/dev-frontend/frontend-architecture.md` |
| Historial de handoffs | `handoffs/tracker_bmad.md` |
| Estado de retrabajo | `.specify/memory/rework_state.json` |

Ningún comando certifica una HU terminada: revisa especificaciones, tareas, código, pruebas y el
dictamen de Code Review.

## 13. Recuperación

| Situación | Acción |
|---|---|
| Watcher sin tracker | `Test-Path (Join-Path $Workspace 'handoffs/tracker_bmad.md')`; revisa selección y bootstrap sin recrear historial |
| Idea guardada pero el flujo no avanza | Indica su ruta al panel de Business Storyteller; guardar el archivo no inicia el flujo |
| Agente ocupado | Esperar; la parada no fuerza el cierre de paneles ocupados |
| Agente terminó pero no avanza | Revisa artefacto, handoff y pausa humana; idle/done no certifican la entrega |
| Evento `uncertain` o `in_flight` | Inspecciona panel, artefactos y estado antes de `--acknowledge` |
| Tracker truncado o modificado | Detén y reconcilia historial y cursor; no borres estado para forzar reintentos |
| Sesión previa o arranque parcial | Revisa `herdr agent list` y la propiedad registrada; no relances sobre nombres existentes ni cierres tabs ajenos |
| Clarify sigue pendiente | Responde la ambigüedad registrada por el watcher; la respuesta relanza `clarify` |
| Git rechaza rama o merge | Revisa `git -C $Workspace status`; resuelve tus cambios o conflictos sin checkout forzado |
| Cambio de configuración | Reinicia los procesos afectados; Runtime cachea la configuración |

Problemas de instalación, proveedores o Herdr: [SETUP.md](SETUP.md#diagnóstico).
