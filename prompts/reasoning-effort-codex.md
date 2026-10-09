# Feature: Soporte de Reasoning Effort en CodexProvider

Actúa como Senior Python Architect especializado en arquitectura hexagonal, SOLID, patrones de diseño y orquestación multiproveedor de agentes de IA.

## Contexto

Mi proyecto BMAD + SDD utiliza Herdr para orquestar agentes mediante Claude, Codex y, próximamente, Gemini.

La refactorización multiproveedor ya existe en `bmad_runtime/`.

Actualmente, el adaptador Codex rechaza la opción `effort` con el error:

`Unsupported Codex option; effort/profile overrides are pending verification.`

**Objetivo: implementar soporte real de reasoning effort para Codex sin modificar mi configuración actual ni romper la compatibilidad con Claude.**

## Requisitos funcionales

### RF01. Soportar effort en CodexProvider

Agregar soporte para la opción `effort` en `CodexProvider`.

La traducción debe ser:

- `low` → `-c model_reasoning_effort=low`
- `medium` → `-c model_reasoning_effort=medium`
- `high` → `-c model_reasoning_effort=high`
- `xhigh` → `-c model_reasoning_effort=xhigh`
- `max` → `-c model_reasoning_effort=max`, cuando el modelo lo admita.

No utilizar `--effort` en Codex.

No introducir opciones arbitrarias ni permitir inyección de argumentos CLI.

### RF02. Compatibilidad con Herdr

Verificar que Herdr 0.8.2 transmite correctamente los argumentos de Codex.

El comando debe construirse mediante una lista de argumentos, sin `shell=True`.

Ejemplo conceptual:

`herdr agent start solutions-architect --kind codex --pane <pane_id> -- -m gpt-6-astra -c model_reasoning_effort=medium`

Conservar los argumentos existentes de sandbox, directorio y carga de perfil. No sustituirlos por el ejemplo simplificado.

### RF03. Compatibilidad con Spec Kit

Las operaciones headless deben soportar el mismo parámetro.

Ejemplo:

`codex exec -m gpt-6-astra -c model_reasoning_effort=medium --sandbox workspace-write`

Verificar la posición y compatibilidad de argumentos con la versión instalada.

### RF04. Respetar la precedencia de configuración

Mantener:

`agents/speckit > phases > defaults`

Conservar la regla existente que impide heredar opciones incompatibles cuando cambia el proveedor.

No modificar `config_bmad.json` ni eliminar ninguno de sus campos `effort`.

### RF05. Extensibilidad y SOLID

Mantener la lógica específica de Codex encapsulada en `CodexProvider`.

No introducir condicionales `if provider == "codex"` en `fleet.py`, `workflow.py`, `watcher_service.py` ni en los servicios de orquestación.

Si se requiere validación de capacidades, utilizar la abstracción existente de proveedores.

### RF06. Validación

Verificar la versión instalada mediante `codex --version`, `codex --help` y `codex exec --help`.

Comprobar los valores de esfuerzo admitidos por `gpt-6-astra`.

No declarar compatibilidad de un nivel sin evidencia.

## Pruebas obligatorias

Agregar pruebas unitarias para:

1. Codex con `effort=low`.
2. Codex con `effort=medium`.
3. Codex con `effort=high`.
4. Codex sin `effort`, respetando el default del CLI.
5. Rechazo de valores inválidos.
6. Comandos interactivos mediante Herdr.
7. Comandos headless de Spec Kit.
8. Conservación del comportamiento de Claude.
9. Precedencia de configuración y overrides por agente.
10. Ausencia de argumentos específicos de Claude en comandos Codex.

Ejecutar ambos dry-runs con el `config_bmad.json` original.

No iniciar agentes reales ni modificar ramas, commits o archivos del tracker.

## Criterios de aceptación

- Los cinco campos `effort` existentes son aceptados.
- Ambos dry-runs terminan sin el error de opciones Codex.
- Los comandos muestran `model_reasoning_effort` con el valor correcto.
- Claude continúa utilizando su propia sintaxis.
- Las pruebas existentes no presentan regresiones nuevas.
- La configuración multiproveedor sigue siendo extensible.
- El código de orquestación permanece independiente de los proveedores.

## Entregables

1. Código refactorizado.
2. Pruebas unitarias.
3. Actualización de `bmad_runtime/README.md`.
4. Evidencia de los dry-runs.
5. Resumen de archivos modificados y resultados.

Implementa los cambios mínimos necesarios. No reescribas la arquitectura existente.