# Code Review

Fase D; token `@CODE-REVIEW:`.

Audita código, pruebas y seguridad contra diseño y constitución. Emite un dictamen; los rechazos activan analyze, converge e implement.

## Directivas

El perfil [AGENTS.md](AGENTS.md) se compila desde [code-review.agent.md](agents/code-review.agent.md), sus instrucciones y skills:

- [code-review-template.instructions.md](instructions/code-review-template.instructions.md)
- [rework-layer-labeling.instructions.md](instructions/rework-layer-labeling.instructions.md)
- [secops-strict-audit.instructions.md](instructions/secops-strict-audit.instructions.md)

## Contexto del proyecto

Las entradas y entregables están en [GUIDE.md](../GUIDE.md#7-entradas-y-entregables-por-rol). Se escriben en el workspace seleccionado; el tracker usa `BMAD_TRACKER`, la configuración efectiva `BMAD_CONFIG` y los perfiles compartidos `ENGINE_ROOT`. Conserva el historial y registra un único destinatario por handoff.

La selección de proveedor y effort sigue el [contrato del runtime](../bmad_runtime/README.md). Consulta [GUIDE.md](../GUIDE.md) para compuertas, implementación y retrabajo.
