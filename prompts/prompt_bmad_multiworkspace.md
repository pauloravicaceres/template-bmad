# Refactorización BMAD: motor único y workspaces independientes

## Rol
Actúa como arquitecto de software y desarrollador Python senior. Trabaja **sobre el repositorio real abierto en tu sesión**, inspecciona sus archivos antes de cambiar código y adapta esta especificación a la implementación existente. No supongas que los nombres o módulos propuestos ya existen.

## Contexto
Este repositorio contiene un ecosistema BMAD + SDD que orquesta un enjambre de agentes mediante Herdr, con CLI de IA (Claude/Codex/Gemini según configuración). Actualmente los handoffs/tracker se escriben en `utils/`, los artefactos en `documents/` y la aplicación generada en `app/`. Para cada nuevo proyecto se está copiando todo el repositorio. Quiero una **única instalación del motor BMAD** capaz de trabajar con **múltiples proyectos independientes** en rutas configurables, sin duplicar agentes, prompts, código del orquestador ni dependencias.

## Objetivo
Separar rigurosamente:
- **ENGINE_ROOT**: directorio del ecosistema compartido; código del orquestador, agentes, skills, plantillas, configuración base y herramientas.
- **WORKSPACE_ROOT**: directorio específico del proyecto activo; artefactos, código generado, handoffs, tracker, logs y estado de ejecución.

Cada ejecución debe recibir explícitamente un identificador de proyecto y/o ruta de workspace. No debe existir dependencia implícita del directorio desde el que se invoca el CLI ni de rutas relativas al repositorio del motor para escribir datos del proyecto.

## Diseño de referencia (adaptable)
```text
<engine-root>/
  bmad_runtime/          # motor compartido, si existe
  utils/                 # utilidades compartidas; NO handoffs de proyectos nuevos
  skills/
  config_bmad.json       # defaults globales
  ...

<workspaces-root>/
  <project-id>/
    project.json         # configuración/identidad del proyecto
    documents/           # Product Brief, PRD, arquitectura, specs, etc.
    app/                 # código fuente desarrollado
    handoffs/            # mensajes y tracker del proyecto
    state/               # checkpoints, locks, sesiones, estado de workflow
    logs/                # logs y trazas del proyecto
```

Los nombres exactos de subcarpetas pueden ajustarse a contratos existentes, pero deben quedar documentados y ser coherentes. No dupliques innecesariamente `.claude`, `.specify`, agentes o skills en cada workspace; si alguna herramienta necesita archivos locales, usa una estrategia explícita, mínima y reproducible (p. ej., configuración por cwd, referencias absolutas o bootstrap de plantillas), sin romper su funcionamiento.

## Trabajo solicitado

### Fase 1: auditoría y diseño
1. Revisa los entrypoints, `config_bmad.json`, `AGENTS.md`, `manifest.yaml`, watcher, launcher, registro de agentes, orquestador, Herdr, SpecKit, dashboard, scripts, prompts y pruebas existentes.
2. Inventaría **todas** las lecturas/escrituras y rutas relativas de `utils/`, `documents/`, `app/`, `specs/`, `.specify/`, `temp/`, trackers, handoffs, archivos de lock, logs y archivos de estado.
3. Identifica cómo se fija el directorio de trabajo de los procesos hijo, cómo se pasan rutas a agentes, y qué rutas quedan codificadas en prompts o instrucciones.
4. Registra el diseño elegido, compatibilidad hacia atrás, riesgos y plan de migración en `documents/` **del motor** solo para documentación técnica del refactor (no para artefactos de proyectos nuevos).

### Fase 2: configuración y resolución de rutas
5. Implementa un objeto central de contexto, por ejemplo `ProjectContext`, con `engine_root`, `workspace_root`, `project_id` y rutas derivadas tipadas (`documents_dir`, `app_dir`, `handoffs_dir`, `tracker_path`, `state_dir`, `logs_dir`, etc.).
6. Resuelve rutas con `pathlib.Path`, normalízalas y valida su existencia y permisos. Acepta rutas absolutas Windows con espacios y caracteres Unicode. Evita concatenaciones manuales.
7. Soporta selección explícita de proyecto por CLI (`--project` y/o `--workspace`, de acuerdo con el CLI existente), configuración de proyecto y valores globales; define y documenta precedencia. Nunca elijas silenciosamente otro proyecto si falta una ruta.
8. Conserva las opciones existentes de proveedores/modelos/esfuerzo por fase/agente/SpecKit; la configuración de proyecto puede sobrescribir solo los campos previstos sin modificar defaults globales.
9. Agrega inicialización idempotente de workspace, sin borrar ni sobrescribir artefactos existentes, con validación de nombres y rutas. Evita escapes fuera del workspace para rutas de salida controladas por el proyecto; no bloquees lecturas legítimas de plantillas del motor.

### Fase 3: integración de procesos
10. Refactoriza launcher, watcher y workflow para recibir el mismo `ProjectContext`. El watcher observa exclusivamente el tracker del proyecto activo; su lock/checkpoint y su deduplicación también son por proyecto.
11. Asegura que las sesiones y paneles de Herdr tengan identidad única por proyecto y agente; define cwd, variables de entorno y/o argumentos para que los agentes lean instrucciones compartidas pero **escriban** dentro del workspace activo.
12. Propaga explícitamente `ENGINE_ROOT`, `WORKSPACE_ROOT`, `PROJECT_ID` y rutas de salida al entorno o contexto de cada agente. Actualiza prompts y documentación para prohibir que los agentes escriban handoffs en `engine_root/utils`, artefactos en `engine_root/documents` o código en `engine_root/app`.
13. Revisa SpecKit, sus comandos, scripts y directorios (`.specify`, `specs`, etc.) para garantizar que los resultados pertenezcan al workspace correcto. Evita crear repositorios Git o modificar archivos de otro proyecto por accidente.
14. Aísla logs, archivos temporales, checkpoints, locks, métricas y reportes por proyecto. Mantén las rutas de herramientas y plantillas compartidas ancladas al motor.
15. Si existe dashboard/API, adapta sus operaciones para identificar el proyecto y no mezclar datos de workspaces diferentes.
16. Define comportamiento seguro ante dos ejecuciones simultáneas: en proyectos distintos deben ser independientes; en el mismo proyecto deben detectar conflictos o utilizar un lock exclusivo, sin corromper estado.

### Fase 4: compatibilidad y migración
17. Conserva, cuando sea razonable, la ejecución legacy sin `--workspace` para proyectos existentes, pero emite una advertencia explícita de deprecación; documenta fecha/criterio de retiro. No migres ni muevas datos automáticamente.
18. Ofrece un comando/script de migración en modo **dry-run** que inventaríe qué datos se copiarían desde `utils/`, `documents/`, `app/` y otras rutas legacy hacia un workspace; requiere confirmación explícita antes de escribir, nunca borra el origen y detecta conflictos de destino.
19. Actualiza README, guía de inicio, ejemplos Windows PowerShell y archivos de ejemplo. Incluye un procedimiento para crear y ejecutar un proyecto nuevo sin copiar el motor.

### Fase 5: pruebas y validación
20. Agrega pruebas unitarias y de integración con `tmp_path` para: resolución de rutas, precedencia, bootstrap idempotente, paths Windows con espacios, watcher aislado, sesiones Herdr diferenciadas, rutas de artefactos y aplicación, configuración por proyecto y protección contra traversal.
21. Prueba dos proyectos A/B en paralelo (simulado o con mocks): un handoff de A no dispara watcher B; los artefactos y código de A nunca aparecen en B ni en el motor; las sesiones/locks son distintos.
22. Ejecuta las pruebas existentes relevantes y reporta regresiones. Distingue fallos previos de nuevos con evidencia; no afirmes E2E real si solo hubo mocks o dry-run.
23. Incluye comandos de validación y ejemplos completos de uso desde PowerShell.

## Criterios de aceptación
- Un único motor BMAD orquesta proyectos A y B con `workspace_root` distintos.
- Handoffs, tracker, `documents`, `app`, `specs`, estado y logs se escriben únicamente en el workspace correspondiente.
- No hay rutas hardcoded al proyecto de ejemplo ni dependencia del cwd del operador.
- El cambio de workspace no exige copiar agentes, prompts, `utils` ni el runtime.
- Se mantienen Claude/Codex/Gemini y las opciones existentes de modelo y `effort`.
- El watcher y Herdr identifican el proyecto correctamente; hay protección ante concurrencia.
- El bootstrap no destruye datos y la migración legacy es opcional, reversible y auditable.
- Tests automatizados verifican aislamiento A/B y compatibilidad documentada.

## Restricciones operativas
- **Primero inspecciona, luego diseña y finalmente implementa.** No reescribas el repositorio desde cero.
- No ejecutes la flota real de agentes, ni llamadas de pago, ni instalaciones globales, ni comandos que requieran desactivar el sandbox.
- No borres artefactos ni carpetas existentes. No hagas `git commit`, `push` o cambios de rama.
- No modifiques permisos NTFS ni configuración global de Codex/Claude/Gemini.
- Si encuentras una decisión que pueda romper la arquitectura o exija una migración destructiva, detente y solicita aprobación antes de realizarla.
- Trabaja por incrementos pequeños y verifica cada etapa.

## Entregables
1. Código refactorizado y pruebas.
2. Documentación de arquitectura y migración.
3. Configuración de ejemplo para dos proyectos con rutas independientes.
4. Comandos exactos de PowerShell para inicializar y ejecutar cada workspace.
5. Informe final: archivos cambiados, decisiones, comandos ejecutados, pruebas y resultados, riesgos y validaciones E2E pendientes.

Comienza mostrando un diagnóstico breve del código real y el plan de archivos a modificar. Después implementa sin esperar confirmación, salvo cuando una acción pueda ser destructiva o requiera decidir entre alternativas incompatibles.
