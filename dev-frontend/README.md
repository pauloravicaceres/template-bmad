# Dev Frontend

Fase D; token `@DEV-FRONT:`.

Implementa tareas frontend SpecKit según UX y contratos. El watcher monta este perfil headless y exige arquitectura de capa y README.

## Directivas

El perfil [AGENTS.md](AGENTS.md) se compila desde [dev-frontend.agent.md](agents/dev-frontend.agent.md), sus instrucciones y skills:

- [zero-hallucination-policy.instructions.md](instructions/zero-hallucination-policy.instructions.md)

## Contexto del proyecto

Las entradas y entregables están en [GUIDE.md](../GUIDE.md#7-entradas-y-entregables-por-rol). Se escriben en el workspace seleccionado; el tracker usa `BMAD_TRACKER`, la configuración efectiva `BMAD_CONFIG` y los perfiles compartidos `ENGINE_ROOT`. Conserva el historial y registra un único destinatario por handoff.

La selección de proveedor y effort sigue el [contrato del runtime](../bmad_runtime/README.md). Consulta [GUIDE.md](../GUIDE.md) para compuertas, implementación y retrabajo.
