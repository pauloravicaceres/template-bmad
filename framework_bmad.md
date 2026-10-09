# Principios BMAD y SDD

BMAD distribuye el trabajo de negocio, gestión, arquitectura e ingeniería entre 15 roles. SDD mantiene `spec.md`, `plan.md` y `tasks.md` como base de implementación. [GUIDE.md](GUIDE.md) describe las compuertas ejecutadas; [ARCHITECTURE.md](ARCHITECTURE.md) identifica los módulos que las implementan.

## Gobernanza del proyecto

Procesa una HU completa antes de iniciar la siguiente. Mantén el identificador `XXX-HU_nombre_en_snake_case` en artefactos, carpeta de spec y rama `feat/XXX-HU_nombre_en_snake_case`. El ledger `specs/README.md` usa las columnas `N°`, `Épica Origen`, `Nombre spec / HU`, `Qué aporta`, `Estado` y `Rama`.

La constitución en `.specify/memory/constitution.md` fija restricciones de stack y arquitectura. Las guidelines, modelos de datos y contratos deben respetarlas. El tracker comunica instrucciones y decisiones; las respuestas no sustituyen documentos de diseño ni justifican inventar requisitos.

Los roles usan perfiles y skills del motor compartido. El contrato de `ProjectContext` define las rutas del proyecto: todos los entregables, código, memoria y handoffs se escriben en el workspace, con independencia del cwd del operador. Consulta [INPUTS_POR_AGENTE.md](INPUTS_POR_AGENTE.md) para la matriz de artefactos.

## Adaptación de la fase de ingeniería

Backend y frontend se ejecutan headless mediante SpecKit con sus perfiles como directivas. QA Automation, Code Review y DevOps disponen de paneles interactivos. Cambiar el stack requiere ajustar la constitución, las instrucciones de los roles y las tareas del proyecto; no existe un catálogo de stacks instalables ni un comando de sustitución de cartuchos.

Las rutas del código se configuran con `code_dirs.backend` y `code_dirs.frontend` dentro de `app/`. El watcher exige documentar `documents/dev-backend/backend-architecture.md`, `documents/dev-frontend/frontend-architecture.md` y los README correspondientes al código.

El proveedor se elige por defaults, fase, agente u operación SpecKit sin cambiar el flujo de negocio. `effort` se traduce en el adaptador nativo. La configuración y sus límites están en [bmad_runtime/README.md](bmad_runtime/README.md).

## Git y revisiones

GitOps trabaja sobre el repositorio propio del workspace y rechaza staging previo al freeze y cambios de rama sobre árboles sucios. `ai.git.auto_commit=false` desactiva el autosave; las macros y el freeze conservan sus operaciones Git. No habilites el watcher para una tarea que prohíba esas operaciones.

Un rechazo de revisión se corrige desde la capa que lo origina (spec, plan, tasks o código), mediante el ciclo de retrabajo SDD acotado. El humano resuelve las ambigüedades que bloquean el avance; el motor registra y despacha las transiciones en el tracker.
