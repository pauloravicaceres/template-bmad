# Dev Backend

Fase D; token `@DEV-BACK:`.

Implementa tareas backend SpecKit con pruebas y contratos. El watcher monta este perfil headless y exige arquitectura de capa y README.

## Directivas

El perfil [AGENTS.md](AGENTS.md) se compila desde [dev-backend.agent.md](agents/dev-backend.agent.md), sus instrucciones y skills:

- [zero-hallucination-policy.instructions.md](instructions/zero-hallucination-policy.instructions.md)

## Contexto del proyecto

Las entradas y entregables están en [INPUTS_POR_AGENTE.md](../INPUTS_POR_AGENTE.md). Se escriben en el workspace seleccionado; el tracker usa `BMAD_TRACKER`, la configuración efectiva `BMAD_CONFIG` y los perfiles compartidos `ENGINE_ROOT`. Conserva el historial y registra un único destinatario por handoff.

La selección de proveedor y effort sigue el [contrato del runtime](../bmad_runtime/README.md). Consulta [GUIDE.md](../GUIDE.md) para compuertas, implementación y retrabajo.
