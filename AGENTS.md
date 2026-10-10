# Instrucciones para mantener el motor BMAD

## CodeGraph

Si existe `.codegraph/` en la raíz, utiliza `codegraph_explore` o `codegraph explore` antes de buscar o leer código para comprender símbolos y sus consumidores. Sin índice, utiliza `rg`; no indexes automáticamente.

## Fuentes canónicas

- Rutas e identidad: `bmad_runtime/context.py`; bootstrap: `bmad_runtime/workspace.py`.
- Configuración: `bmad_runtime/config.py`; selección y comandos nativos: `registry.py` y `providers.py`.
- Orquestación: `runtime.py`, `fleet.py`, `services.py` y `herdr.py`.
- Handoffs, locks y cola: `state.py`, `watcher_service.py` y `workflow.py`.
- Contrato por módulo: [bmad_runtime/README.md](bmad_runtime/README.md); arquitectura y diagramas: [ARCHITECTURE.md](ARCHITECTURE.md).

Conserva multiworkspace, selección por fase/agente/operación y traducción de effort. Resuelve escrituras mediante ProjectContext; nunca uses el cwd del motor como salida implícita de un proyecto seleccionado. No modifiques trackers, handoffs activos, workspaces externos, secretos ni entregables de `app/` o `docs/` durante el mantenimiento del motor.

Inspecciona `git status` antes de editar y respeta cambios previos. Comprueba consumidores por imports, carga dinámica, CLI, perfiles, skills y tareas antes de eliminar módulos. Las copias instaladas de skills son dependencias que se cotejan contra `.github/skills`, no duplicados prescindibles.

## Validación

Desde la raíz, usa el Python del entorno backend:

```powershell
& 'bmad-control-center/backend/.venv/Scripts/python.exe' -B tests/run_isolated.py tests -q
& 'bmad-control-center/backend/.venv/Scripts/python.exe' -B tests/validate_offline.py
git diff --check
```

El harness aísla temporales y desactiva contratos de CLIs reales. Usa dobles para flotas, despacho y GitOps; los dry-runs no lanzan agentes. Las instrucciones del usuario determinan si se permite arranque real, red, commits o cambios de estado.
