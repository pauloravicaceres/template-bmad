# BMAD Framework Template

Motor Python que orquesta un equipo de 15 roles de IA con la metodología BMAD y el desarrollo
guiado por especificaciones (SDD) de Spec Kit. Es una plataforma genérica multiworkspace:
el motor se instala una vez y cada proyecto vive en su propio workspace, con su identidad,
configuración, entregables, código, tracker y estado. El stack de cada aplicación lo define o
lo descubre su workspace; el motor no lo impone.

## Funcionalidades

- **Workspaces aislados:** bootstrap aditivo con identidad explícita, perímetro de rutas,
  sesiones con nombre `ID-hash-rol` y estado SQLite y locks por proyecto.
- **Flota interactiva en Herdr:** 13 paneles en 3 tabs (12 si se omite UX).
- **Watcher del tracker:** lee `handoffs/tracker_bmad.md`, despacha a agentes propios inactivos,
  respeta pausas humanas y persiste cursor y cola recuperables.
- **SDD headless:** siete operaciones Spec Kit (`specify`, `clarify`, `plan`, `tasks`, `analyze`,
  `converge`, `implement`); backend y frontend se implementan sin panel propio.
- **Multiproveedor:** Claude y Codex interactivos y headless, seleccionables por fase, agente u
  operación, con traducción nativa de `effort`. Gemini está registrado sin ejecución.
- **Contexto técnico por rol:** política del motor, constitución local, guías, ADRs y
  descubrimiento acotado del stack Brownfield, sin inferir aprobaciones.
- **GitOps del workspace:** rama por HU, freeze de especificaciones y cierre con merge.
- **Dashboard opcional:** FastAPI + Nuxt con etapas, compuertas humanas, entregables, eventos
  en vivo y telemetría Git de un proyecto por proceso.

## Requisitos mínimos

Python 3.10+, Git, PowerShell, Herdr abierto y los CLIs de Claude y/o Codex instalados y
autenticados. Node.js y npm solo para el dashboard. Detalle en [SETUP.md](SETUP.md).

## Inicio rápido

Desde la raíz del motor, con las dependencias instaladas según [SETUP.md](SETUP.md):

```powershell
$Engine = (Get-Location).Path
$Python = Join-Path $Engine 'bmad-control-center/backend/.venv/Scripts/python.exe'
$Workspace = Join-Path (Split-Path $Engine -Parent) 'Proyecto A'

# 1. Crear el workspace (aditivo; no inicializa Git)
& $Python (Join-Path $Engine 'init_bmad.py') --workspace $Workspace --project proyecto-a

# 2. Revisar flota y operaciones Spec Kit sin lanzar agentes
& $Python (Join-Path $Engine 'utils/start_agents.py') --workspace $Workspace --project proyecto-a --dry-run
& $Python (Join-Path $Engine 'watcher_bmad.py') --workspace $Workspace --project proyecto-a --dry-run

# 3. Arrancar la flota y, en otra terminal, el watcher
& $Python (Join-Path $Engine 'utils/start_agents.py') --workspace $Workspace --project proyecto-a
& $Python (Join-Path $Engine 'watcher_bmad.py') --workspace $Workspace --project proyecto-a
```

Antes del paso 3 configura `project.json`, la constitución técnica y el Git propio del
workspace. Después entrega la idea en el panel `business-storyteller` y atiende las compuertas
humanas del tracker. El procedimiento completo y el registro del proyecto por ID
(`--project proyecto-a` sin `--workspace`) están en [GUIDE.md](GUIDE.md).

## Documentación

| Documento | Responsabilidad |
|---|---|
| [SETUP.md](SETUP.md) | Instalación, dependencias, proveedores y effort, Herdr, variables de entorno, configuración, validación y diagnóstico |
| [GUIDE.md](GUIDE.md) | Operación: workspaces Brownfield y Greenfield, flota, watcher, flujo de HU, roles, compuertas, dashboard, parada y resultados |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Componentes, carpetas, datos, estados, secuencias, contexto y orquestación de uno y varios proyectos |
| [bmad_runtime/README.md](bmad_runtime/README.md) | Contrato por módulo: funciones, consumidores, efectos y CLI |
| [constitution.md](constitution.md) | Política operativa compartida que el runtime inyecta a los agentes |
| [AGENTS.md](AGENTS.md) | Instrucciones para mantener el motor |
| `<rol>/README.md` | Directivas y fuentes de cada perfil |
| [Backend](bmad-control-center/backend/README.md) y [frontend](bmad-control-center/frontend/README.md) | Ejecución, API y pruebas del dashboard |
