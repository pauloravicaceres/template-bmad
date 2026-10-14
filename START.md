# START — Guía de inicio del orquestador BMAD/SDD v1.0

Guía práctica, paso a paso, para poner en marcha el orquestador **Herdr + BMAD + SDD (Spec Kit) +
Multiworkspace v1.0** en Windows con PowerShell y empezar un proyecto **desde una carpeta vacía**.

Está escrita a partir del código actual del repositorio, no de cómo debería funcionar. Cuando algo
no está implementado o no se pudo verificar, se indica explícitamente con 🔴 **IMPORTANTE**.

**Etiquetas usadas en toda la guía**

- 🟢 **SOLO LA PRIMERA VEZ:** configuración que normalmente no se repite.
- 🔵 **CADA VEZ QUE INICIES EL ORQUESTADOR:** pasos de cada sesión de trabajo.
- 🟡 **POR CADA PROYECTO NUEVO:** pasos para preparar otro workspace.
- 🟠 **CUANDO NECESITES INTERVENIR:** aprobaciones o decisiones que solo tú puedes tomar.
- 🔴 **IMPORTANTE:** advertencias y operaciones que requieren precaución.
- ✅ **VERIFICACIÓN:** cómo confirmar que el paso funcionó.

---

## 0. ¿Qué voy a conseguir siguiendo esta guía?

Al terminar tendrás:

1. El **motor** (este repositorio) instalado una sola vez.
2. Un **proyecto nuevo** (un "workspace") creado desde una carpeta vacía, con su propia
   configuración, documentos, tracker y estado.
3. **Herdr** abierto, con un equipo de agentes de IA (Claude y Codex) trabajando en paneles, cada uno
   con un rol: Business Storyteller, Product Analyst, Product Manager, Business Analyst, QA, UX,
   Arquitectos, QA Automation, Code Review y DevOps.
4. El **watcher**, que lee el tracker del proyecto y le pasa el trabajo al agente que corresponde.
   También ejecuta Spec Kit (SDD) automáticamente.
5. Opcionalmente, el **Control Center** (dashboard web) para ver el avance y aprobar compuertas.
6. Una primera idea entregada y una forma sencilla de comprobar que el orquestador trabaja.

### Orden real de arranque

El orden que sugiere "Backend → Frontend → Watcher → Herdr…" **no es el que exige el código**. El
dashboard es opcional y no controla a los agentes; el watcher necesita que el proyecto exista y que
los agentes ya estén lanzados. El orden correcto es:

```text
(una vez)      Instalar dependencias del motor
(por proyecto) Crear workspace → project.json → Git del proyecto → (opcional) registrarlo
(cada día)     Herdr → Agentes (start_agents) → Watcher → (opcional) Backend → (opcional) Frontend
               → Entregar la idea al Business Storyteller
```

| Componente | ¿Obligatorio? | ¿Se queda abierto? |
|---|---|---|
| Herdr | Sí | Sí, su ventana/terminal queda abierta |
| Agentes (`utils/start_agents.py`) | Sí | No: lanza los paneles en Herdr y termina |
| Watcher (`watcher_bmad.py`) | Sí | Sí, terminal propia |
| Backend del Control Center | No (opcional) | Sí, terminal propia |
| Frontend del Control Center | No (opcional; requiere el backend) | Sí, terminal propia |

---

## 1. Antes de comenzar

### Qué necesitas instalado

El motor **no instala** ninguna de estas herramientas. Debes tenerlas instaladas y, en el caso de
Claude y Codex, con sesión iniciada.

| Herramienta | Para qué | Requisito |
|---|---|---|
| Python | Motor y backend del dashboard | 3.10 o superior (3.11+ recomendado para leer `pyproject.toml` en proyectos existentes) |
| Git | Repositorio propio de cada proyecto (ramas por HU, freeze, merge) | Cualquier versión reciente |
| PowerShell 7 (`pwsh`) | Comandos de esta guía y sandbox de Codex en Windows | Versión instalada (MSI), **no** solo la de Microsoft Store |
| Herdr | Gestor de paneles donde viven los agentes | Probado con `herdr 0.8.2` |
| Claude Code CLI | Agentes con proveedor Claude | Instalado y autenticado |
| Codex CLI | Agentes con proveedor Codex | Instalado y autenticado |
| Node.js y npm | **Solo** para el frontend del dashboard | Node 22.18+ para sus pruebas |

🔴 **IMPORTANTE:** con la configuración actual del motor (`config_bmad.json`) se usan **los dos
proveedores**. Codex (modelo `gpt-6-astra`) cubre las fases B, M, A y D, y Claude el Business Analyst
y la operación `clarify` de Spec Kit. Si te falta uno de los dos CLIs, el arranque falla.

🔴 **IMPORTANTE:** en Windows el motor rechaza los "envoltorios" `.cmd`, `.bat` y `.ps1`. `claude`,
`codex` y `herdr` deben resolverse a ejecutables `.exe`.

### Comandos para comprobar cada requisito

Abre una terminal PowerShell (cualquier carpeta) y ejecuta:

```powershell
python --version
git --version
$PSVersionTable.PSVersion
Get-Command pwsh, herdr, claude, codex, node, npm -ErrorAction SilentlyContinue | Select-Object Name, Source
herdr --version
claude --version
codex --version
node --version
npm --version
```

✅ **VERIFICACIÓN:** cada comando muestra una versión. En la tabla de `Get-Command`, la columna
`Source` muestra rutas terminadas en `.exe`. `pwsh` no debe apuntar a `...\Microsoft\WindowsApps\...`.

Comprueba también la autenticación de los proveedores y la ayuda de Herdr:

```powershell
claude auth status
codex login status
herdr agent start --help
```

Si tu versión no reconoce `claude auth status` o `codex login status`, consulta
`claude auth --help` y `codex login --help`. Estos comandos no prueban que tengas cuota ni acceso
al modelo: solo que el CLI está instalado y con sesión.

---

## 2. Preparación inicial — 🟢 SOLO LA PRIMERA VEZ

Todo este bloque se ejecuta **en la carpeta del motor**:
`D:\Paulo\Cursos\DMC\template-bmad`.

### Paso 2.1 — Abrir una terminal en el motor

- **Terminal:** una PowerShell nueva.
- **Comando:**

```powershell
Set-Location 'D:\Paulo\Cursos\DMC\template-bmad'
$Engine = (Get-Location).Path
$Python = Join-Path $Engine 'bmad-control-center\backend\.venv\Scripts\python.exe'
```

`$Python` es el Python del entorno virtual del motor. **Todos** los comandos del motor de esta guía
usan ese Python.

### Paso 2.2 — Crear el entorno virtual (solo si no existe)

```powershell
if (-not (Test-Path $Python)) { python -m venv bmad-control-center/backend/.venv }
& $Python --version
```

- **Resultado esperado:** muestra `Python 3.x.y`.
- ✅ **VERIFICACIÓN:** `Test-Path $Python` devuelve `True`.

### Paso 2.3 — Instalar dependencias de Python

```powershell
& $Python -m pip install -r (Join-Path $Engine 'bmad-control-center/backend/requirements.txt')
```

El runtime del orquestador solo usa la biblioteca estándar de Python. Este archivo instala lo que
necesitan el backend del dashboard y las pruebas (FastAPI, uvicorn, watchdog, etc.).

✅ **VERIFICACIÓN:**

```powershell
& $Python -c "import fastapi, uvicorn, watchdog; print('OK')"
```

Debe imprimir `OK`.

### Paso 2.4 — Instalar dependencias del frontend (solo si usarás el dashboard)

```powershell
npm --prefix (Join-Path $Engine 'bmad-control-center/frontend') ci
```

- **Resultado esperado:** npm instala los paquetes y al final ejecuta `nuxt prepare` (`postinstall`).
- ✅ **VERIFICACIÓN:** existe la carpeta `bmad-control-center\frontend\node_modules`.

### Paso 2.5 — Revisar la configuración global del motor

Abre `D:\Paulo\Cursos\DMC\template-bmad\config_bmad.json` con un editor y **léelo**. No hace falta
cambiar nada para empezar. Contiene:

- `ai.defaults`, `ai.phases`, `ai.agents`, `ai.speckit`: qué proveedor, modelo y esfuerzo usa cada
  fase, agente u operación de Spec Kit.
- `ai.providers`: el ejecutable de cada proveedor (`claude`, `codex`, `gemini`).
- `ai.git.auto_commit`: `false` (desactiva el autoguardado; el freeze y las macros GitOps sí hacen commits).
- `projects`: el **registro de proyectos** (al principio está vacío: `{}`).

🔴 **IMPORTANTE:** como `projects` existe (aunque esté vacío), **todo comando del motor exige indicar
el proyecto** con `--workspace` y/o `--project`. Sin eso, el motor se niega a ejecutar.

🔴 **IMPORTANTE:** no edites nunca `state/config_bmad.json` de un proyecto: es una copia generada.

### Paso 2.6 — Comprobar Herdr una primera vez

Abre una PowerShell nueva y ejecuta:

```powershell
herdr
```

Se abre la interfaz de Herdr (sesión persistente). Ciérrala o déjala abierta; en la sección 3 la
usarás cada día. Desde **otra** terminal:

```powershell
herdr status server
herdr agent list
```

✅ **VERIFICACIÓN:** `herdr agent list` responde sin error (todavía sin agentes BMAD).

---

## 3. Cómo levantar el orquestador — 🔵 CADA VEZ QUE INICIES EL ORQUESTADOR

> Requisito: el proyecto ya existe (sección 4). **Si es tu primer día**, sigue la sección 4 hasta el
> paso 4.10: ahí ya abres Herdr y lanzas los agentes (PASOS 1 y 2 de esta sección), así que
> continúa directamente en el **PASO 3 (Watcher)**. **Los días siguientes**, sigue esta sección
> completa desde el PASO 1.

### Mapa de terminales

| Terminal | Contenido | ¿Queda abierta? |
|---|---|---|
| **Terminal 1** | Herdr | Sí |
| **Terminal 2** | Comandos del motor: lanzar agentes, aprobaciones, consultas | Sí (la reutilizas) |
| **Terminal 3** | Watcher | Sí |
| **Terminal 4** | Backend del dashboard (opcional) | Sí |
| **Terminal 5** | Frontend del dashboard (opcional) | Sí |

### Bloque de variables (pégalo al abrir las Terminales 2, 3 y 4)

Cada terminal nueva empieza vacía, así que **pega este bloque al abrirla**. Ajusta las dos últimas
líneas a tu proyecto (en esta guía: `D:\Proyectos\MiNuevoProyecto` y `mi-nuevo-proyecto`).

```powershell
Set-Location 'D:\Paulo\Cursos\DMC\template-bmad'
$Engine    = (Get-Location).Path
$Python    = Join-Path $Engine 'bmad-control-center\backend\.venv\Scripts\python.exe'
$Workspace = 'D:\Proyectos\MiNuevoProyecto'
$Project   = 'mi-nuevo-proyecto'
```

Todos los comandos del motor se ejecutan **desde la carpeta del motor** (por eso el `Set-Location`).
Así funciona `python -m bmad_runtime...`. El proyecto se elige siempre con `--workspace` y `--project`.

### PASO 1 — Herdr (Terminal 1)

- **¿Para qué sirve?** Es la "pantalla" donde viven los agentes: cada agente es un panel dentro de
  una pestaña de Herdr.
- **Carpeta:** cualquiera.
- **¿Terminal nueva?** Sí.
- **Comando:**

```powershell
herdr
```

- **¿Dejarla abierta?** Sí. Herdr mantiene una sesión persistente en un servidor local.
- **Señal de arranque correcto:** se ve la interfaz de Herdr.
- ✅ **VERIFICACIÓN** (desde la Terminal 2):

```powershell
herdr agent list
```

Responde sin error.

### PASO 2 — Agentes (Terminal 2)

- **¿Para qué sirve?** Crea 3 pestañas en Herdr con 13 paneles (12 si el proyecto no usa UX) y
  arranca en cada uno el CLI (Claude o Codex) de su rol.
- **Carpeta:** la del motor (bloque de variables).
- **¿Terminal nueva?** Sí (Terminal 2, con el bloque de variables pegado).

Primero revisa el plan **sin lanzar nada**:

```powershell
& $Python (Join-Path $Engine 'utils/start_agents.py') --workspace $Workspace --project $Project --dry-run
```

✅ **VERIFICACIÓN del dry-run:** imprime un JSON con una fila por agente. Comprueba en cada fila:

- `project_id` = tu proyecto, y `workspace` y `cwd` = la carpeta de tu proyecto.
- `status` = `verified_cli_contract`. Si alguna fila dice `pending`, **no sigas**: ese agente tiene
  un proveedor no ejecutable (por ejemplo Gemini).
- `provider` y `model` son los que esperas.

`verified_cli_contract` solo significa que el comando se pudo construir; no que el CLI esté
autenticado.

Después lanza la flota:

```powershell
& $Python (Join-Path $Engine 'utils/start_agents.py') --workspace $Workspace --project $Project
```

- **¿Dejarla abierta?** El comando termina solo. La terminal sí, porque la reutilizarás.
- **Señal de arranque correcto:** `Flota iniciada: 13 agentes.` (o `12` sin UX).
- **Si aparece** `ERROR: Launched, but these agents are held until verified ...`, algún agente está
  esperando que respondas un diálogo (normalmente "¿confías en esta carpeta?"). Ve al
  🟠 **PASO 2b**.

🟠 **PASO 2b — Responder diálogos de confianza (CUANDO NECESITES INTERVENIR)**

La **primera vez** que Claude o Codex se abren en una carpeta nueva preguntan si confías en ella. El
motor **nunca responde estos diálogos por ti**: deja el agente retenido en estado `awaiting_trust`.

1. En Herdr, ve al panel del agente indicado en el error.
2. Lee el diálogo y elige confiar en la carpeta si es tu proyecto:
   - Codex muestra `Trust this folder? › 1. Trust and continue / 2. Quit`.
   - Claude muestra su propia pregunta de confianza.
3. Cuando el agente quede esperando instrucciones, ejecuta en la Terminal 2 (cambia `ROL` por el
   nombre del rol, por ejemplo `business-analyst` o su alias `ba`):

```powershell
& $Python -B -m bmad_runtime.maintenance --workspace $Workspace --project $Project --reconcile ROL --confirm
```

🔴 **IMPORTANTE:** aceptar la confianza modifica la configuración global de tu usuario
(`~/.claude.json` para Claude y `~/.codex/config.toml` para Codex). Hazlo solo con carpetas de
proyectos tuyos. Normalmente basta con hacerlo una vez por carpeta.

✅ **VERIFICACIÓN del PASO 2:**

```powershell
herdr agent list
& $Python -B -m bmad_runtime.guard --workspace $Workspace --project $Project --status
```

`herdr agent list` muestra agentes cuyo nombre empieza por tu proyecto, por ejemplo
`mi-nuevo-proy-1a2b3c4d-bs`. El prefijo se recorta solo para respetar el límite de 32 caracteres de
Herdr. `guard --status` (solo lectura) muestra el estado de cada agente. Solo los agentes en estado
`ready` reciben tareas; `starting`, `awaiting_trust` y `unverified` quedan retenidos.

### PASO 3 — Watcher (Terminal 3)

- **¿Para qué sirve?** Lee `handoffs/tracker_bmad.md` del proyecto cada ~2 segundos y entrega cada
  tarea al agente que corresponde. También ejecuta automáticamente las operaciones de Spec Kit
  (`specify`, `clarify`, `plan`, `tasks`, `analyze`, `converge`, `implement`).
- **Carpeta:** la del motor.
- **¿Terminal nueva?** Sí (pega el bloque de variables).

Primero, la revisión sin ejecutar:

```powershell
& $Python (Join-Path $Engine 'watcher_bmad.py') --workspace $Workspace --project $Project --dry-run
```

✅ Debe listar las 7 operaciones de Spec Kit con su proveedor y `status: verified_cli_contract`
(ninguna `pending`).

Después, el watcher real:

```powershell
& $Python (Join-Path $Engine 'watcher_bmad.py') --workspace $Workspace --project $Project
```

- **¿Dejarla abierta?** Sí, **todo el tiempo que trabajes**. Se detiene con `Ctrl+C`.
- **Señal de arranque correcto:**

```text
👁️ Watcher BMAD (Sequential Token-Passing) iniciado.
📂 Escuchando cambios en: D:\Proyectos\MiNuevoProyecto\handoffs\tracker_bmad.md
```

- 🟠 La **primera vez** que arranca con un tracker que ya tiene contenido y sin cursor guardado,
  pregunta `¿Deseas reanudar la ejecución desde esta última instrucción? (s/n)`. Si el proyecto es
  nuevo y aún no has entregado la idea, el tracker está vacío y no pregunta nada. Por eso conviene
  arrancar el watcher **antes** de entregar la idea.
- ✅ **VERIFICACIÓN:** un segundo watcher sobre el mismo proyecto falla por lock, lo que demuestra
  que el primero está activo. La consola del watcher muestra los avisos (`⚠️`, `🛑`, `💡`) mientras
  trabaja.

### PASO 4 — Backend del Control Center (Terminal 4, opcional)

- **¿Para qué sirve?** Una API local que lee el tracker, los documentos y el Git de **un** proyecto y
  permite aprobar o rechazar compuertas desde el navegador.
- **Carpeta:** la del motor.
- **¿Terminal nueva?** Sí (pega el bloque de variables).
- **Comando:**

```powershell
$env:BMAD_WORKSPACE = $Workspace
$env:BMAD_PROJECT   = $Project
& $Python -m uvicorn main:app --app-dir (Join-Path $Engine 'bmad-control-center/backend') --host 127.0.0.1 --port 8000
```

- **¿Dejarla abierta?** Sí. Se detiene con `Ctrl+C`.
- **Señal de arranque correcto:** uvicorn muestra `Uvicorn running on http://127.0.0.1:8000`.
- ✅ **VERIFICACIÓN:** abre `http://127.0.0.1:8000/api/v1/project` en el navegador. Debe mostrar un
  JSON con tu `project_id`. Si `project_id` sale `null`, el backend arrancó sin proyecto: revisa las
  dos variables `$env:` y reinícialo.

Un backend sirve **un solo proyecto**. Para cambiar de proyecto hay que reiniciarlo con otras variables.

### PASO 5 — Frontend del Control Center (Terminal 5, opcional)

- **¿Para qué sirve?** La página web del dashboard.
- **Carpeta:** la del motor.
- **¿Terminal nueva?** Sí.
- **Comando:**

```powershell
Set-Location 'D:\Paulo\Cursos\DMC\template-bmad'
$env:VITE_BMAD_API_BASE = 'http://localhost:8000/api/v1'
npm --prefix bmad-control-center/frontend run dev -- --port 3000
```

- **¿Dejarla abierta?** Sí. Se detiene con `Ctrl+C`.
- **Señal de arranque correcto:** Nuxt muestra la URL local `http://localhost:3000/`.
- ✅ **VERIFICACIÓN:** abre `http://localhost:3000`. Arriba aparece `BMAD · Workspaces` con
  `Proyecto seleccionado: ... (mi-nuevo-proyecto)` y, debajo, el panel `BMAD Control Center`.

El frontend usa `http://localhost:8000/api/v1` aunque no definas `VITE_BMAD_API_BASE`. Definirla
es necesario cuando el backend usa otro puerto (sección 8).

---

## 4. Cómo crear un proyecto nuevo DESDE UNA CARPETA VACÍA — 🟡 POR CADA PROYECTO NUEVO

Ejemplo de esta guía:

- Carpeta del proyecto: `D:\Proyectos\MiNuevoProyecto` (vacía o inexistente).
- Identificador del proyecto (`project_id`): `mi-nuevo-proyecto`.

Todos los comandos de esta sección se ejecutan en una PowerShell **en la carpeta del motor**.

🔴 **IMPORTANTE:** antes de cualquier comando de esta sección, **pega este bloque en la terminal**.
Las variables de PowerShell no pasan de una terminal a otra. Si las dejas vacías, verás el error
`argument --workspace: expected one argument`.

```powershell
Set-Location 'D:\Paulo\Cursos\DMC\template-bmad'
$Engine    = (Get-Location).Path
$Python    = Join-Path $Engine 'bmad-control-center\backend\.venv\Scripts\python.exe'
$Workspace = 'D:\Proyectos\MiNuevoProyecto'
$Project   = 'mi-nuevo-proyecto'
```

✅ **VERIFICACIÓN:** `$Workspace; $Project` debe imprimir las dos cadenas, no líneas vacías.

### Paso 4.1 — Elegir el identificador

El `project_id` debe tener 1 a 64 caracteres: letras ASCII, dígitos, `_` o `-`. Debe empezar por
letra o dígito y no puede ser un nombre reservado de Windows (`CON`, `NUL`, `COM1`…). Usa minúsculas
y guiones, por ejemplo `mi-nuevo-proyecto`. Es la **identidad permanente** del proyecto: no la
cambies después.

🔴 **IMPORTANTE:** la carpeta del proyecto **no puede estar dentro del motor** ni contenerlo.
`D:\Proyectos\...` es correcto; `D:\Paulo\Cursos\DMC\template-bmad\MiProyecto` no lo es.

### Paso 4.2 — Crear la carpeta (opcional)

El inicializador crea la carpeta si no existe. Si prefieres crearla tú:

```powershell
New-Item -ItemType Directory -Path 'D:\Proyectos\MiNuevoProyecto'
```

### Paso 4.3 — Inicializar el workspace (comando automático)

**Sí existe un inicializador automático:** `init_bmad.py`. Primero, la vista previa:

```powershell
& $Python (Join-Path $Engine 'init_bmad.py') --workspace $Workspace --project $Project --dry-run
```

Muestra en JSON las rutas que se usarán (`WORKSPACE_ROOT`, `BMAD_TRACKER`, …) **sin crear nada**.

Después, la inicialización real:

```powershell
& $Python (Join-Path $Engine 'init_bmad.py') --workspace $Workspace --project $Project
if ($LASTEXITCODE -ne 0) { throw 'Falló el bootstrap; revisa el error.' }
```

- **Resultado esperado:** un JSON con `ENGINE_ROOT`, `WORKSPACE_ROOT`, `PROJECT_ID`, `BMAD_TRACKER`, etc.
- Es **aditivo**: si lo repites, no sobrescribe archivos, no vacía el tracker y no inicializa Git.
  Si `project.json` ya existe, el `--project` debe coincidir con él.

### Paso 4.4 — Qué crea el framework automáticamente

```text
D:\Proyectos\MiNuevoProyecto\
├── project.json                      identidad del proyecto (se edita en el paso 4.6)
├── AGENTS.md                         contrato de rutas para los agentes (generado; no hace falta tocarlo)
├── docs\<rol>\                       15 carpetas, una por rol, más docs\business-analyst\HUs-stakeholders\
├── app\                              vacía; el código irá en app\backend y app\frontend por defecto
├── handoffs\tracker_bmad.md          tracker vacío (el "bus" de mensajes entre agentes)
├── specs\README.md                   ledger de Historias de Usuario (HU)
├── .specify\memory\constitution.md   constitución técnica del proyecto, neutral, con stack pendiente
├── .specify\scripts\, .specify\templates\   copia de Spec Kit
├── state\config_bmad.json            configuración efectiva generada (no editar)
├── state\bootstrap.lock              lock del bootstrap (normal que quede)
└── logs\, temp\                      vacías
```

Lo que **no** crea: repositorio Git, `.gitignore`, README del proyecto, documentos de negocio,
historias de usuario ni código. Tampoco copia agentes ni skills: se leen desde el motor.

✅ **VERIFICACIÓN:**

```powershell
Get-Content -LiteralPath (Join-Path $Workspace 'project.json')
Test-Path (Join-Path $Workspace 'handoffs\tracker_bmad.md')
```

`project.json` muestra `"project_id": "mi-nuevo-proyecto"` y `Test-Path` devuelve `True`.

### Paso 4.5 — Qué debes preparar tú (manual)

| Qué | ¿Obligatorio? | Paso |
|---|---|---|
| Completar `project.json` (nombre, tipo, carpetas de código) | Recomendado | 4.6 |
| Crear `.gitignore` y el repositorio Git del proyecto | **Sí**, para el flujo GitOps (ramas por HU) | 4.7 |
| Registrar el proyecto en `config_bmad.json` del motor | Opcional (necesario para usar solo `--project` y para que el dashboard lo liste) | 4.8 |
| Escribir el stack técnico en la constitución | Opcional en proyectos nuevos | 4.9 |
| Copiar perfiles de agentes, skills o plantillas | **No.** Se leen del motor | — |
| Crear README, `docs`, tracker o HUs | **No.** Los generan el bootstrap y los agentes | — |

### Paso 4.6 — Completar `project.json`

Abre `D:\Proyectos\MiNuevoProyecto\project.json` con un editor. Al principio contiene:

```json
{
  "schema_version": 1,
  "project_id": "mi-nuevo-proyecto",
  "config": {}
}
```

Rellena `config`. Ejemplo para una aplicación con interfaz:

```json
{
  "schema_version": 1,
  "project_id": "mi-nuevo-proyecto",
  "config": {
    "project_name": "Mi Nuevo Proyecto",
    "project_type": "fullstack",
    "ux_phase": "auto",
    "code_dirs": {"backend": "app/backend", "frontend": "app/frontend"}
  }
}
```

- **No cambies** `schema_version` ni `project_id`.
- `config` solo acepta `project_name`, `project_type`, `ux_phase`, `code_dirs` y `ai`. Cualquier otra
  clave produce un error.
- `project_type`: el único valor con efecto especial es `headless`, que omite el diseño UX y su panel.
  Para una app con interfaz usa otro valor, como `fullstack`.
- `ux_phase`: `auto` (cada HU decide según su línea `Requiere interfaz: Sí|No`), `on` (siempre
  diseño UX) u `off` (nunca diseño UX).
- `code_dirs`: solo `backend` y `frontend`, rutas dentro del proyecto. Si las omites, se usan
  `app/backend` y `app/frontend`.
- `ai`: opcional, para cambiar proveedor, modelo o esfuerzo solo en este proyecto.

### Paso 4.7 — Git del proyecto (obligatorio para el flujo de HU)

El motor **nunca inicializa Git** y rechaza usar un repositorio padre. Las ramas por HU, el freeze de
especificaciones y el merge final necesitan un repositorio **propio** del proyecto. Hazlo **antes**
de lanzar los agentes.

1. Crea el archivo `D:\Proyectos\MiNuevoProyecto\.gitignore` con un editor. Contenido sugerido,
   basado en lo que pide la documentación (secretos, dependencias, `state/`, `logs/`, `temp/`):

```text
state/
logs/
temp/
node_modules/
.venv/
.env
```

2. Inicializa y haz el primer commit. Estos comandos usan `git -C`, así que funcionan desde la
   carpeta del motor:

```powershell
git -C $Workspace init
git -C $Workspace add .
git -C $Workspace diff --cached --stat
git -C $Workspace commit -m 'chore: initialize BMAD workspace'
git -C $Workspace rev-parse --show-toplevel
```

✅ **VERIFICACIÓN:** la última línea muestra exactamente la carpeta del proyecto
(`D:/Proyectos/MiNuevoProyecto`). Si muestra otra carpeta, el proyecto está dentro de otro
repositorio y GitOps lo rechazará.

Si `git commit` pide tu nombre o correo, configúralos con `git config --global user.name "..."` y
`git config --global user.email "..."` y repite el commit.

### Paso 4.8 — Registrar el proyecto en el motor (opcional)

Registrarlo permite usar solo `--project mi-nuevo-proyecto` sin `--workspace` y que el dashboard lo
liste. **Sin registrarlo todo funciona** pasando siempre `--workspace` y `--project`, como en esta guía.

Abre `D:\Paulo\Cursos\DMC\template-bmad\config_bmad.json` con un editor y cambia la línea final

```text
    "projects": {}
```

por (barras `/` para no tener que escapar `\`):

```text
    "projects": {
        "mi-nuevo-proyecto": "D:/Proyectos/MiNuevoProyecto"
    }
```

🔴 **IMPORTANTE:** si ya hay proyectos registrados, **añade** el tuyo separado por coma; no borres
los otros. Una ruta relativa se interpreta respecto de la carpeta del motor.

✅ **VERIFICACIÓN:**

```powershell
& $Python (Join-Path $Engine 'init_bmad.py') --project $Project --dry-run
```

Debe mostrar `WORKSPACE_ROOT` = tu carpeta.

### Paso 4.9 — Constitución técnica (opcional en proyectos nuevos)

- `D:\Paulo\Cursos\DMC\template-bmad\constitution.md` es la política común del motor. **No se edita
  por proyecto.**
- `D:\Proyectos\MiNuevoProyecto\.specify\memory\constitution.md` es la constitución técnica **de tu
  proyecto** (la misma que usa Spec Kit). El bootstrap la crea neutral, con el stack "pendiente".

En un proyecto nuevo puedes dejarla así: el **Solutions Architect** propondrá el stack y pedirá tu
aprobación con `@HUMANO:`. Si ya tienes un stack decidido, regístralo en esa constitución antes de
empezar. El inventario va en `docs/architecture/tech-stack.md`, la arquitectura en
`docs/architecture/architecture.md` y las decisiones en `docs/architecture/adr/`.

### Paso 4.10 — Roles: no hay que "habilitarlos"

No existe un paso para activar roles: `start_agents.py` lanza todos los roles con panel.

**Cómo ejecutar `start_agents.py`.** Hazlo después de los pasos 4.6 y 4.7 (`project.json` y Git del
proyecto), porque la configuración se lee al lanzar.

1. **Abre Herdr** (Terminal 1). Abre una PowerShell nueva, ejecuta `herdr` y **déjala abierta**:
   los agentes aparecerán como paneles dentro de esa ventana.

```powershell
herdr
```

2. **En otra PowerShell (Terminal 2)**, pega el bloque de variables del inicio de esta sección y
   comprueba que Herdr responde:

```powershell
herdr agent list
```

   Debe responder sin error (la lista estará vacía). Si falla, Herdr no está abierto.

3. **Vista previa**, que no lanza nada:

```powershell
& $Python (Join-Path $Engine 'utils/start_agents.py') --workspace $Workspace --project $Project --dry-run
```

   Revisa que ninguna fila diga `pending` y que `workspace`/`cwd` sean tu carpeta.

4. **Lanzamiento real:**

```powershell
& $Python (Join-Path $Engine 'utils/start_agents.py') --workspace $Workspace --project $Project
```

   Termina con `Flota iniciada: 13 agentes.` (o `12` sin UX). Si un agente queda retenido por un
   diálogo de confianza, ve a la sección 3, PASO 2b.

Después continúa en la sección 3, **PASO 3 (Watcher)**. Los PASOS 1 y 2 de la sección 3 ya los hiciste
aquí; solo los repetirás en los días siguientes.

| Pestaña de Herdr | Roles (token en el tracker) |
|---|---|
| Negocio y Producto | Business Storyteller `@BS:`, Product Manager `@PM:`, Business Analyst `@BA:`, Product Analyst `@PA:`, QA Documental `@QA:`, Designer UX `@UX:` |
| Arquitectura e Ingeniería | Solutions Architect `@SA:`, Data Architect `@DA:`, API Architect `@API:`, QA Tech `@QT:` |
| Desarrollo y Despliegue | QA Automation `@QA-AUTO:`, Code Review `@CODE-REVIEW:`/`@CR:`, DevOps `@DEVOPS:` |

- **Dev Backend y Dev Frontend no tienen panel:** los ejecuta el watcher como operación headless
  `implement` de Spec Kit.
- **Designer UX** se omite (12 paneles) si `project_type` es `headless` o `ux_phase` es `off`.
- El proveedor de cada rol se elige en `config_bmad.json` (o en `project.json` → `config.ai`),
  por fase, agente u operación.

### Paso 4.11 — Comprobar que los agentes trabajarán solo en este proyecto

1. En los dry-runs (sección 3, PASOS 2 y 3), **todas** las filas muestran `workspace`/`cwd` = tu
   carpeta y `tracker` = `...\MiNuevoProyecto\handoffs\tracker_bmad.md`.
2. `git -C $Workspace rev-parse --show-toplevel` devuelve tu carpeta.
3. Tras lanzar, `herdr agent list` muestra nombres con el prefijo de tu proyecto.
4. El motor comprueba en cada verificación que el `cwd` del panel es tu workspace.

🔴 **IMPORTANTE:** el perímetro de rutas es una regla del motor y del contrato que reciben los
agentes, **no un sandbox del sistema operativo**. Un CLI con permisos amplios podría escribir fuera.
Por eso Claude se lanza por defecto en modo `acceptEdits`: edita dentro del workspace sin preguntar,
pero los comandos de shell y las rutas externas te piden aprobación.

### Paso 4.12 — Confirmar que el proyecto está listo

Lista de comprobación:

- [ ] `project.json` con tu `project_id` y `config` completado.
- [ ] `git -C $Workspace rev-parse --show-toplevel` = tu carpeta, con el primer commit hecho.
- [ ] Dry-run de agentes sin filas `pending` y con tu carpeta en `cwd`.
- [ ] Dry-run del watcher con las 7 operaciones `verified_cli_contract`.

Con esto, vuelve a la **sección 3** para arrancar Herdr, agentes y watcher.

---

## 5. Cómo iniciar el primer flujo BMAD/SDD

### 5.1 El primer agente: Business Storyteller

El flujo siempre empieza en el panel **Business Storyteller**. **No existe importación automática de
un archivo inicial**: la idea se escribe (o pega) directamente en ese panel.

1. En Herdr, pestaña `...-Negocio y Producto`, busca el panel cuyo nombre termina en `-bs`.
2. Escribe la idea con: actores, problema, objetivo, alcance y restricciones. Ejemplo (proyecto
   ficticio "agenda de citas"):

```text
Gestionamos las citas de un centro por teléfono y se producen cruces de horario.
Recepción necesita registrar y consultar reservas. Empezamos con una agenda interna,
sin pagos ni acceso de clientes. Estructura esta idea según tu perfil y el contrato del workspace.
```

Si prefieres escribir la idea en un archivo, guárdalo dentro del proyecto (por ejemplo
`D:\Proyectos\MiNuevoProyecto\docs\business-storyteller\mi-idea.md`) y **dile al panel** la ruta.
Guardar el archivo por sí solo no inicia nada.

### 5.2 Cómo se pasan el trabajo los agentes

- Cada agente escribe su entregable en `docs/<rol>/` y **anexa un bloque** al tracker
  `handoffs/tracker_bmad.md`. El bloque lleva fecha, autor, artefacto, estado y una línea `Handoff`
  con el token del siguiente rol, por ejemplo `@PA:`.
- El **watcher** es el único que despacha: detecta el token, escribe la tarea en
  `handoffs/tasks/<evento>-<intento>.md` y envía al panel del destinatario una línea corta que la referencia.
- Mientras un agente tiene una tarea sin responder, no recibe otra; la siguiente queda en cola.

Para seguir el tracker en vivo (en la Terminal 2 u otra):

```powershell
Get-Content -LiteralPath (Join-Path $Workspace 'handoffs/tracker_bmad.md') -Tail 40 -Wait
```

✅ **VERIFICACIÓN de que el orquestador trabaja:** tras entregar la idea:

1. Aparece en el tracker un bloque del Business Storyteller con `Handoff` a `@PA:`.
2. Existe `docs/business-storyteller/idea-<nombre>.md` en el proyecto.
3. `herdr agent list` muestra al Product Analyst trabajando, y la tarea aparece en `handoffs/tasks/`.

### 5.3 Qué hace el orquestador automáticamente

Resumen del flujo implementado:

1. **B · Business Storyteller** estructura la idea → **Product Analyst** redacta el Product Brief
   (`docs/product-analyst/pb-*.md`) → 🟠 **tú lo apruebas**.
2. **M · Product Manager** prioriza el MVP (`mvp-*.md`), elige una HU, asigna su número en
   `specs/README.md` y abre la rama (`@WATCHER: GITOPS-BRANCH-CREATE feat/NNN-nombre`).
   **Business Analyst** escribe la HU (`docs/business-analyst/NNN-nombre.md`) y **QA Documental** la valida.
3. Tras la aprobación de QA, el watcher ejecuta **Spec Kit `specify` y `clarify`** (headless). Si
   hay ambigüedades, 🟠 **pausa y te pregunta** (ver 5.4).
4. Según `project_type`/`ux_phase` y la HU, pasa por **Designer UX** o va directo a
   **Solutions Architect**, que publica `tech_guidelines.md` y emite `@WATCHER: SDD-FREEZE`.
5. El watcher ejecuta **`plan`, `tasks` y `analyze`**, hace el commit de freeze y deriva a
   **Data Architect** → (**API Architect** si hace falta) → **QA Tech**.
6. El watcher ejecuta **`implement`** (backend y después frontend). **QA Automation** prueba y
   **Code Review** dictamina.
7. Si hay rechazo: `analyze → converge → implement` (máximo 2 iteraciones; después te escala).
   Si se aprueba: `GITOPS-MERGE-CLOSE` cierra la rama y se puede abrir la siguiente HU.

Una HU se termina antes de abrir la siguiente. El identificador `NNN-nombre-en-kebab-case` (tres
dígitos, minúsculas, guiones, sin tildes) se usa igual en la HU, `specs/NNN-nombre/` y la rama
`feat/NNN-nombre`. Un nombre inválido se rechaza y **nada se renombra solo**: corrígelo a mano.

### 5.4 Cuándo debes intervenir — 🟠 CUANDO NECESITES INTERVENIR

| Situación | Cómo la reconoces | Qué haces |
|---|---|---|
| Aprobación de una fase (Product Brief, MVP, etc.) | El último bloque del tracker tiene `@HUMANO:`; el watcher deja de despachar | `utils/approve_step.py` (abajo) o botón **Aprobar** del dashboard |
| Preguntas del Solutions Architect | Bloque del SA con `@HUMANO:` | `utils/response_sa.py` (abajo) |
| Ambigüedad de Spec Kit (`clarify`) | Bloque `WATCHER` con `Ambigüedad detectada por Spec Kit` | Ver "Responder un clarify" abajo |
| Cierre de rama (`GITOPS-MERGE-CLOSE`) | La consola del **watcher** (Terminal 3) pide confirmar el nombre de la rama | Escríbelo en la Terminal 3 |
| Claude pide permiso para un comando de shell | Diálogo en el panel del agente | Responde en el panel (o niégalo) |
| Diálogo de confianza de carpeta | Agente en `awaiting_trust` | Sección 3, PASO 2b |
| Escalado tras 2 rechazos | Bloque con `@HUMANO:` | Revisa el código y decide |

**Aprobar desde la consola** (Terminal 2):

```powershell
& $Python (Join-Path $Engine 'utils/approve_step.py') --workspace $Workspace --project $Project
```

Muestra un menú numerado. Elige la transición que corresponde al último bloque `@HUMANO:`, por
ejemplo `[2] Product Analyst (PA) -> PM` para aprobar el Product Brief o `[3] Product Manager (PM) -> BA`
para el MVP. El script abre el archivo detectado para que lo revises y pide confirmación `(s/n)`.

🔴 **IMPORTANTE:** el menú conserva opciones antiguas de despacho directo a desarrollo (`11`, `11b`,
`12`, `13`) que **no corresponden a la flota actual**. Sigue la ruta de Spec Kit.

**Responder al Solutions Architect** (Terminal 2):

```powershell
& $Python (Join-Path $Engine 'utils/response_sa.py') --workspace $Workspace --project $Project
```

Pega tus respuestas, pulsa Enter, escribe `FIN` y pulsa Enter otra vez.

**Responder un clarify.** 🔴 **IMPORTANTE:** no hay comando ni botón dedicado. Según el código
(`bmad_runtime/workflow.py`), el watcher relanza `clarify` cuando el tracker recibe una línea con
`@WATCHER: /speckit.clarify <tu respuesta>`. Una forma de anexarla como bloque humano, sin reescribir
el archivo:

```powershell
$Hoy  = Get-Date -Format 'dd-MM-yyyy'
$Hora = Get-Date -Format 'HH:mm:ss'
Add-Content -LiteralPath (Join-Path $Workspace 'handoffs/tracker_bmad.md') -Encoding utf8 -Value @(
  '', "### [$Hoy] HUMANO", "- **Hora:** $Hora",
  '- **Handoff:** @WATCHER: /speckit.clarify Tu respuesta en una sola línea'
)
```

Este procedimiento se dedujo del código y **no se ha probado en vivo**. Nunca edites el tracker con
un editor que reescriba el archivo completo o cambie los finales de línea: el watcher lo detecta como
"historial reescrito" y se detiene.

### 5.5 Cómo ver el estado de las tareas

| Quiero ver… | Dónde |
|---|---|
| Qué agente está trabajando, inactivo o bloqueado | `herdr agent list` (estados de Herdr `working`, `idle`, `blocked`, `done`) |
| Estado de cada agente para el orquestador, retenciones y alertas | `& $Python -B -m bmad_runtime.guard --workspace $Workspace --project $Project --status` (solo lectura; se puede usar con el watcher activo) |
| Historial de handoffs y avisos del watcher | `handoffs/tracker_bmad.md` (los avisos del watcher son bloques `WATCHER`) |
| Alertas de bucles o presupuesto | Consola del watcher y `logs/guard.log` del proyecto |
| Estado de las HU (abierta, cerrada) | `& $Python -B -m bmad_runtime.hu_lifecycle --status --workspace $Workspace --project $Project` (solo lectura) |
| Registros pendientes o inciertos | `& $Python -B -m bmad_runtime.state --workspace $Workspace --project $Project` (**solo con el watcher detenido**: toma su lock) |
| Etapas y compuertas en gráfico | Dashboard (sección 7) |

🔴 **IMPORTANTE:** que Herdr muestre un agente `idle` o `done` **no prueba** que terminó su tarea.
Lo que cuenta es el artefacto en `docs/` y su bloque en el tracker.

---

## 6. ¿Y si quiero utilizar Spec Kit?

**Spec Kit no es un flujo separado ni un modo que se active: está integrado en el flujo BMAD.** El
watcher ejecuta en modo headless (sin panel) las 7 operaciones de Spec Kit en momentos concretos del
flujo (sección 5.3).

- **No hay que ejecutar `specify init`:** el bootstrap ya copió `.specify/scripts` y
  `.specify/templates` al proyecto y creó `.specify/memory/constitution.md`.
- **No hay que lanzar `/speckit-*` a mano** en el flujo normal: lo hace el watcher.
- **Resultados:** `specs/NNN-nombre/` (`spec.md`, `plan.md`, `tasks.md`), el ledger `specs/README.md`
  y el código en `code_dirs`.
- **Configuración diferente:** solo el bloque `ai.speckit` (proveedor, modelo y esfuerzo por
  operación) en `config_bmad.json` o en `project.json` → `config.ai.speckit`. Los tiempos máximos se
  ajustan en `ai.limits.operation_timeouts` (solo en el `config_bmad.json` del motor).
- **Comprobarlo:** el dry-run del watcher (sección 3, PASO 3) lista las 7 operaciones con su proveedor.

🔴 **IMPORTANTE:** la versión 1.0 **no ofrece un modo "solo Spec Kit"** sin los agentes BMAD.
Tampoco documenta ni prueba ejecutar los comandos `/speckit-*` a mano dentro de un workspace
orquestado; si lo haces, el watcher no registra esas ejecuciones como fases del flujo.

---

## 7. Cómo utilizar el Control Center

- **URL:** `http://localhost:3000` (con el frontend del PASO 5 y el backend del PASO 4).
- **API directa:** `http://127.0.0.1:8000/api/v1/project` (proyecto seleccionado) y
  `http://127.0.0.1:8000/api/v1/projects` (registro de `config_bmad.json`).

**Qué verás**

1. Cabecera `BMAD · Workspaces`: el proyecto seleccionado y la lista de proyectos registrados en
   `config_bmad.json`, con el botón **Actualizar proyectos**.
2. Panel `BMAD Control Center` del proyecto que sirve ese backend:
   - Un indicador de etapas del flujo con la etapa y el rol activos.
   - Botones **Artefactos** (árbol de `docs`, `specs`, `.specify` y `handoffs`, con visor de
     Markdown y Mermaid) y **Telemetría Git** (rama, cambios y commits del proyecto).
   - Botón **Telemetría**: registro de eventos en vivo y estado del perímetro de rutas.
   - Indicador del estado del WebSocket.
   - Sección **Compuertas Human-in-the-Loop (HITL)** → **Mostrar panel HITL**. Muestra
     `Hay una compuerta esperando decisión.` con los botones **Aprobar** y **Rechazar** (el feedback
     es obligatorio para rechazar), o `Todo en orden, sin compuertas pendientes.`.

**Identificar tu proyecto:** en `Proyecto seleccionado: Nombre (id)`. Si dice
`No hay un proyecto seleccionado.`, el backend arrancó sin `BMAD_WORKSPACE`/`BMAD_PROJECT`.

**Qué NO hace el dashboard** (requiere CLI):

- **No muestra los agentes de Herdr** ni el estado SQLite: usa `herdr agent list` y `guard --status`.
- No crea ni registra proyectos, no lanza ni detiene agentes ni el watcher.
- No responde `clarify` ni las preguntas del SA (`response_sa.py`), ni reconoce eventos (`bmad_runtime.state`).
- Cada backend sirve **un** proyecto; no agrega varios.

**Errores:** las aprobaciones rechazadas devuelven un mensaje (por ejemplo, 422 si la HU tiene un
nombre inválido o falta el artefacto, o 409 si la compuerta ya se resolvió). Los errores del motor
se ven en la consola del watcher, en los bloques `WATCHER` del tracker y en `logs/guard.log`.

🔴 **IMPORTANTE (discrepancia en el código):** si apruebas desde el dashboard un bloque de QA
Documental, el handoff generado va siempre a `@UX:`, **sin consultar** `project_type`/`ux_phase`. En
un proyecto `headless` usa `utils/approve_step.py`, opción `[6] ... -> SA [Bypass Headless]`.

---

## 8. Cómo trabajar con dos o más proyectos

**Idea clave:** un solo motor y un solo Herdr; cada proyecto tiene **su propia carpeta y sus propios
procesos** (agentes, watcher y, si lo quieres, backend y frontend). No hay un selector global de
"proyecto activo": el proyecto lo eligen el `--workspace`/`--project` de cada comando o las variables
de cada terminal.

| Compartido (motor) | Propio de cada proyecto |
|---|---|
| Código del motor, perfiles de rol, skills, `constitution.md` del motor, `config_bmad.json` (incluido el registro `projects`), servidor Herdr | `project.json`, `docs/`, `app/`, `specs/`, `.specify/`, tracker, `state/` (SQLite y locks), `logs/`, repositorio Git, agentes en Herdr (prefijo propio), watcher, backend y frontend |

### Ejemplo: `agenda-citas` y `inventario`

1. 🟡 Crea el segundo proyecto siguiendo la sección 4 entera (init, `project.json`, Git, registro opcional):

```powershell
$WorkspaceB = 'D:\Proyectos\Inventario'
$ProjectB   = 'inventario'
& $Python (Join-Path $Engine 'init_bmad.py') --workspace $WorkspaceB --project $ProjectB
```

2. Para el segundo proyecto abre **otras** terminales (en su bloque de variables cambia `$Workspace`
   y `$Project`) y repite: dry-runs, `start_agents.py` y **su propio watcher**.
3. Dashboard: un backend y un frontend por proyecto, **con puertos distintos**:

```powershell
# Terminal backend de inventario
$env:BMAD_WORKSPACE = 'D:\Proyectos\Inventario'; $env:BMAD_PROJECT = 'inventario'
& $Python -m uvicorn main:app --app-dir (Join-Path $Engine 'bmad-control-center/backend') --host 127.0.0.1 --port 8001
# Terminal frontend de inventario
$env:VITE_BMAD_API_BASE = 'http://localhost:8001/api/v1'
npm --prefix bmad-control-center/frontend run dev -- --port 3001
```

**Evitar escribir en el proyecto equivocado**

- Pasa siempre `--workspace` y `--project` juntos. Si no coinciden con `project.json`, el motor
  falla en vez de adoptar otro proyecto.
- Si usas `$env:BMAD_WORKSPACE`/`$env:BMAD_PROJECT` en una terminal, límpialos al cambiar:
  `Remove-Item Env:BMAD_WORKSPACE, Env:BMAD_PROJECT -ErrorAction SilentlyContinue`.
- Los nombres de agentes en Herdr llevan el `project_id` y un hash de la carpeta; el watcher solo
  despacha a los agentes registrados en el `state/` de **su** proyecto.

🔴 **IMPORTANTE:** el aislamiento entre dos proyectos está probado con dobles de prueba, **no con dos
flotas reales en el mismo Herdr**. Empieza operando un proyecto a la vez y comprueba paneles y puertos
antes de trabajar en paralelo.

---

## 9. Cómo detener todo correctamente

Hazlo en este orden y **no termines procesos a la fuerza** (nada de `Stop-Process`).

1. **Watcher (Terminal 3):** pulsa `Ctrl+C` y espera `🛑 Watcher detenido por el usuario.`. Si
   interrumpes una operación de Spec Kit en curso, puede quedar como `uncertain` y tendrás que
   revisarla al volver.
2. **Agentes:** espera a que estén inactivos (`herdr agent list`: `idle`/`done`) y revisa artefactos.
   Después cierra **solo las pestañas de tu proyecto** (Terminal 2):

```powershell
& $Python (Join-Path $Engine 'utils/stop_agents.py') --workspace $Workspace --project $Project --confirm
```

   Sin `--confirm` no cierra nada. Solo cierra pestañas que el motor creó para este proyecto y cuyos
   agentes están `idle`/`done`; rechaza cerrar si alguno está ocupado.

   **Alternativa:** no cerrar los agentes. Si dejas Herdr y los agentes abiertos, mañana solo tendrás
   que arrancar el watcher.
3. **Herdr:** cerrar la ventana de Herdr no tiene por qué detener su servidor (la sesión es
   persistente). Para detenerlo del todo:

```powershell
herdr server stop
```

   🔴 **IMPORTANTE:** esto detiene **todas** las pestañas y paneles de Herdr, también los de otros
   proyectos. Úsalo solo cuando ninguno siga trabajando.
4. **Backend y frontend (Terminales 4 y 5):** `Ctrl+C` en cada una.

**Qué queda guardado** (en la carpeta del proyecto): `docs/`, `specs/`, `app/`, el tracker, Git y
`state/state.sqlite3` (cursor del tracker, cola, agentes, sesiones y alertas). **No borres** `state/`,
los locks ni el SQLite para "reiniciar": se pierde la recuperación.

### Retomar al día siguiente — 🔵

- **Si dejaste Herdr y los agentes abiertos:** arranca solo el watcher (sección 3, PASO 3) y, si
  quieres, el dashboard. El watcher recupera cursor, cola y rama abierta.
- **Si cerraste los agentes o detuviste Herdr:** sección 3 completa: `herdr` → dry-run →
  `start_agents.py` → watcher. Los diálogos de confianza normalmente no se repiten para la misma carpeta.
- Si al arrancar el watcher ves tareas que esperan a un panel que ya no existe, ve a la sección 10.

---

## 10. Problemas comunes

**El backend no arranca**
- **Causa probable:** dependencias sin instalar o puerto ocupado.
- **Qué comprobar:** `& $Python -c "import fastapi, uvicorn, watchdog"` y el mensaje de uvicorn
  (por ejemplo, dirección en uso).
- **Solución:** repite el paso 2.3 o usa otro `--port` (y ajusta `VITE_BMAD_API_BASE`).

**El backend arranca pero las páginas devuelven 409 `PROJECT_NOT_SELECTED`**
- **Causa:** se lanzó sin `BMAD_WORKSPACE` ni `BMAD_PROJECT`.
- **Solución:** `Ctrl+C`, define las variables en esa terminal y relánzalo (sección 3, PASO 4).

**El frontend no abre o muestra "No se pudo consultar el registro de proyectos."**
- **Causa probable:** el backend no está activo o el frontend apunta a otro puerto.
- **Qué comprobar:** `http://127.0.0.1:8000/api/v1/project` responde, y el valor de
  `$env:VITE_BMAD_API_BASE` en la terminal del frontend.
- **Solución:** arranca el backend; define `VITE_BMAD_API_BASE` **antes** de `npm run dev` y
  reinicia el frontend. Si faltan dependencias, repite el paso 2.4.

**El proyecto no aparece en la lista del Control Center**
- **Causa:** no está en `projects` de `config_bmad.json` (la lista solo muestra el registro).
- **Solución:** paso 4.8 y botón **Actualizar proyectos**. Para supervisarlo necesitas además un
  backend arrancado con ese proyecto.

**El watcher no detecta cambios / no despacha**
- **Qué comprobar:**
  1. Que la consola dice `Escuchando cambios en:` con la ruta de **tu** tracker.
  2. Si el último bloque tiene `@HUMANO:`, el watcher está **en pausa** esperando tu decisión
     (sección 5.4).
  3. `guard --status`: el agente puede estar retenido (`starting`, `awaiting_trust`, `unverified`,
     mantenimiento pendiente o una tarea anterior sin responder).
  4. El watcher solo procesa **líneas completas** (terminadas en salto de línea).
- **Solución:** atiende la pausa o la retención que indique `guard --status`; usa el comando de
  liberación que ese informe muestra.

**El watcher se detiene con `Tracker history changed before the saved cursor`**
- **Causa:** el tracker se acortó, se reescribió o desapareció (por ejemplo, al guardarlo desde un editor).
- **Solución:** con el watcher detenido, inspecciona con
  `& $Python -B -m bmad_runtime.state --workspace $Workspace --project $Project`. Si fue un
  accidente, restaura el tracker (desde Git) y reinicia el watcher. Si el cambio fue intencional,
  revisa que no quede ningún handoff sin atender y ejecuta
  `& $Python -B -m bmad_runtime.state --workspace $Workspace --project $Project --rebaseline-tracker --confirm`.

**Herdr no encuentra una sesión / `herdr agent list` falla**
- **Causa probable:** Herdr no está abierto o su servidor no corre.
- **Qué comprobar:** `herdr status server`.
- **Solución:** abre `herdr` en la Terminal 1. Si un comando falla con `workspace_not_found` (visto
  con un servidor Herdr arrancado sin interfaz), crea un workspace de Herdr:
  `herdr workspace create --cwd 'D:\Proyectos\MiNuevoProyecto' --label mi-nuevo-proyecto`.
  Este último caso está observado en pruebas, no documentado por el motor.

**`start_agents.py` dice `Matching agent names already exist in Herdr`**
- **Causa:** ya hay agentes de este proyecto en Herdr (por ejemplo, de ayer).
- **Solución:** no relances encima. Si siguen válidos, usa solo el watcher; si no, ciérralos con
  `stop_agents.py --confirm` y vuelve a lanzar.

**Claude o Codex piden confiar en una carpeta**
- **Causa:** primera ejecución del CLI en esa carpeta (Codex pregunta por repositorio Git).
- **Solución:** sección 3, PASO 2b: respóndelo **tú** en el panel y después
  `maintenance --reconcile ROL --confirm`. Nunca envíes un Enter o un número a ciegas al panel:
  `2` en Codex significa *Quit*.

**Un agente aparece bloqueado**
- **Qué comprobar:** el panel en Herdr (¿está pidiendo un permiso?) y `guard --status` del agente.
- **Solución:** si pide permiso para un comando, decide tú en el panel. Si `guard` muestra una alerta
  (`no_progress`, `repeated_instruction`, `permission_blocked`…), revisa el panel y el tracker, y
  reconoce la alerta con
  `& $Python -B -m bmad_runtime.guard --workspace $Workspace --project $Project --acknowledge REGLA:AGENTE --confirm`.
  Si el contexto del agente está degradado, consulta
  `& $Python -B -m bmad_runtime.maintenance --workspace $Workspace --project $Project --plan-clear`.

**Una tarea queda esperando aprobación humana**
- **Es lo esperado** cuando el último bloque tiene `@HUMANO:`. Atiéndela con `approve_step.py`,
  `response_sa.py`, el dashboard o la respuesta de clarify (sección 5.4). Hasta entonces el watcher no
  despacha nada que dependa de esa aprobación.

**Una tarea quedó enviada a un panel que ya no existe (Herdr se detuvo)**
- **Síntoma:** el agente sigue con un seguimiento activo y no recibe nuevas tareas.
- **Solución** (con el watcher **detenido**, tras revisar panel y tracker; el ID aparece en la salida de `bmad_runtime.state`):

```powershell
& $Python -B -m bmad_runtime.state --workspace $Workspace --project $Project --acknowledge queued:<event_id> --confirm
& $Python -B -m bmad_runtime.state --workspace $Workspace --project $Project --release-followup business-analyst --confirm
```

**El agente trabaja en el workspace incorrecto**
- **Qué comprobar:** dry-run (`cwd`/`workspace`), `project.json` y `herdr agent list` (prefijo del nombre).
- **Solución:** detén ese watcher, cierra las pestañas de ese proyecto con `stop_agents.py --confirm`
  y relanza con el `--workspace`/`--project` correctos. No cambies el `project_id` para "tomar" otras sesiones.

**El tracker no se actualiza**
- **Causa probable:** el agente no ha terminado o escribió su entregable sin anexar el bloque.
- **Qué comprobar:** el panel del agente y `docs/<rol>/`.
- **Solución:** espera; si el agente terminó sin bloque, el watcher le envía recordatorios y después
  escala. Si un agente anexa un bloque **sin** que se le haya despachado, el watcher registra
  `protocol_violation:<n>` y retiene los despachos hasta que revises y ejecutes, con el watcher detenido,
  `& $Python -B -m bmad_runtime.state --workspace $Workspace --project $Project --acknowledge protocol_violation:<n> --confirm`.

**Git rechaza la rama o el merge**
- **Qué comprobar:** `git -C $Workspace status` y `git -C $Workspace rev-parse --show-toplevel`.
- **Solución:** resuelve tus cambios o conflictos a mano, sin `checkout` forzado.

**Cambié `config_bmad.json` o `project.json` y no se nota**
- **Causa:** los procesos guardan la configuración en caché.
- **Solución:** reinicia el watcher (y el backend). Para que los agentes usen otro proveedor hay que
  cerrarlos y relanzarlos.

**Hooks de tu Claude Code global dentro de los paneles**
- Las configuraciones globales de tu usuario (`~/.claude`) también se cargan en los paneles de los
  agentes Claude. En pruebas se observó que un hook global puede interrumpir su primera edición. Si
  un agente se detiene por un mensaje de un hook, revisa tu configuración global de Claude Code.

---

## 11. Chuleta de comandos

Ejecuta todos los comandos en PowerShell desde `D:\Paulo\Cursos\DMC\template-bmad`, con el bloque de
variables de la sección 3.

| Para… | Comando |
|---|---|
| 🟢 Instalar dependencias Python | `& $Python -m pip install -r bmad-control-center/backend/requirements.txt` |
| 🟢 Instalar dependencias frontend | `npm --prefix bmad-control-center/frontend ci` |
| 🟡 Crear workspace (vista previa) | `& $Python init_bmad.py --workspace $Workspace --project $Project --dry-run` |
| 🟡 Crear workspace | `& $Python init_bmad.py --workspace $Workspace --project $Project` |
| 🟡 Git del proyecto | `git -C $Workspace init` + `add` + `commit` (paso 4.7) |
| 🔵 Iniciar Herdr | `herdr` |
| 🔵 Revisar plan de agentes | `& $Python utils/start_agents.py --workspace $Workspace --project $Project --dry-run` |
| 🔵 Lanzar agentes | `& $Python utils/start_agents.py --workspace $Workspace --project $Project` |
| 🟠 Liberar agente tras diálogo | `& $Python -B -m bmad_runtime.maintenance --workspace $Workspace --project $Project --reconcile ROL --confirm` |
| 🔵 Revisar plan del watcher | `& $Python watcher_bmad.py --workspace $Workspace --project $Project --dry-run` |
| 🔵 Iniciar watcher | `& $Python watcher_bmad.py --workspace $Workspace --project $Project` |
| 🔵 Iniciar backend | `$env:BMAD_WORKSPACE=$Workspace; $env:BMAD_PROJECT=$Project; & $Python -m uvicorn main:app --app-dir bmad-control-center/backend --host 127.0.0.1 --port 8000` |
| 🔵 Iniciar frontend | `npm --prefix bmad-control-center/frontend run dev -- --port 3000` |
| ✅ Ver agentes | `herdr agent list` |
| ✅ Estado del orquestador por agente | `& $Python -B -m bmad_runtime.guard --workspace $Workspace --project $Project --status` |
| ✅ Estado de las HU | `& $Python -B -m bmad_runtime.hu_lifecycle --status --workspace $Workspace --project $Project` |
| ✅ Seguir el tracker | `Get-Content -LiteralPath (Join-Path $Workspace 'handoffs/tracker_bmad.md') -Tail 40 -Wait` |
| 🔵 Iniciar flujo | Escribir la idea en el panel `...-bs` de Herdr |
| 🟠 Aprobar una compuerta | `& $Python utils/approve_step.py --workspace $Workspace --project $Project` |
| 🟠 Responder al SA | `& $Python utils/response_sa.py --workspace $Workspace --project $Project` |
| ✅ Registros pendientes (watcher detenido) | `& $Python -B -m bmad_runtime.state --workspace $Workspace --project $Project` |
| Detener watcher, backend, frontend | `Ctrl+C` en su terminal |
| Cerrar agentes del proyecto | `& $Python utils/stop_agents.py --workspace $Workspace --project $Project --confirm` |
| 🔴 Detener el servidor Herdr (todos los proyectos) | `herdr server stop` |

---

## Limitaciones conocidas de la versión 1.0

- No existe un comando para **registrar** un proyecto en `config_bmad.json`: se edita a mano (paso 4.8).
- No existe **importación automática** de la idea inicial: se escribe en el panel del Business Storyteller.
- No hay comando ni botón para **responder `clarify`** (sección 5.4).
- Spec Kit no tiene un **modo independiente** del flujo BMAD.
- El dashboard **no muestra agentes** ni sirve varios proyectos a la vez.
- El motor **no responde diálogos de confianza** ni de permisos: siempre los respondes tú.
- No hay prueba automatizada de **dos flotas reales** en el mismo Herdr.
- Gemini está registrado pero **no puede ejecutarse** (sale `pending` en los dry-runs).
- **Puertos:** `GUIDE.md` usa 8001/3001 para el dashboard y `ARCHITECTURE.md` 8000/3000. Los dos
  funcionan; esta guía usa 8000/3000 para el primer proyecto porque son los valores por defecto del frontend.

Para profundizar (no es necesario para empezar): [SETUP.md](SETUP.md), [GUIDE.md](GUIDE.md) y
[ARCHITECTURE.md](ARCHITECTURE.md).
