# DevOps

Fase D; token `@DEVOPS:`.

Define infraestructura, contenedores y CI/CD según diseño aprobado. Mantiene secretos fuera de archivos versionados y documenta la operación.

## Directivas

El perfil [AGENTS.md](AGENTS.md) se compila desde [devops.agent.md](agents/devops.agent.md), sus instrucciones y skills:

- [cli-headless-execution.instructions.md](instructions/cli-headless-execution.instructions.md)
- [devops-architecture-template.instructions.md](instructions/devops-architecture-template.instructions.md)
- [devops-strict-infra.instructions.md](instructions/devops-strict-infra.instructions.md)

## Contexto del proyecto

Las entradas y entregables están en [GUIDE.md](../GUIDE.md#7-entradas-y-entregables-por-rol). Se escriben en el workspace seleccionado; el tracker usa `BMAD_TRACKER`, la configuración efectiva `BMAD_CONFIG` y los perfiles compartidos `ENGINE_ROOT`. Conserva el historial y registra un único destinatario por handoff.

La selección de proveedor y effort sigue el [contrato del runtime](../bmad_runtime/README.md). Consulta [GUIDE.md](../GUIDE.md) para compuertas, implementación y retrabajo.
