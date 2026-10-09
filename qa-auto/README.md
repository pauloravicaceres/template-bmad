# QA Automation

Fase D; token `@QA-AUTO:`.

Verifica criterios de aceptación con pruebas de comportamiento observable. Registra resultados para Code Review o retrabajo SDD.

## Directivas

El perfil [AGENTS.md](AGENTS.md) se compila desde [qa-auto.agent.md](agents/qa-auto.agent.md), sus instrucciones y skills:

- [cli-headless-execution.instructions.md](instructions/cli-headless-execution.instructions.md)
- [qa-report-template.instructions.md](instructions/qa-report-template.instructions.md)
- [qa-strict-testing.instructions.md](instructions/qa-strict-testing.instructions.md)
- [rework-layer-labeling.instructions.md](instructions/rework-layer-labeling.instructions.md)

## Contexto del proyecto

Las entradas y entregables están en [INPUTS_POR_AGENTE.md](../INPUTS_POR_AGENTE.md). Se escriben en el workspace seleccionado; el tracker usa `BMAD_TRACKER`, la configuración efectiva `BMAD_CONFIG` y los perfiles compartidos `ENGINE_ROOT`. Conserva el historial y registra un único destinatario por handoff.

La selección de proveedor y effort sigue el [contrato del runtime](../bmad_runtime/README.md). Consulta [GUIDE.md](../GUIDE.md) para compuertas, implementación y retrabajo.
