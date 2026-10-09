# QA Documental

Fase M; token `@QA:`.

Contrasta HU y Product Brief y documenta aprobación o feedback. La aprobación habilita la compuerta de negocio SpecKit.

## Directivas

El perfil [AGENTS.md](AGENTS.md) se compila desde [qa-documental.agent.md](agents/qa-documental.agent.md), sus instrucciones y skills:

- [anti-hallucination-policy.instructions.md](instructions/anti-hallucination-policy.instructions.md)
- [qa-report-template.instructions.md](instructions/qa-report-template.instructions.md)
- [qa-validation-standards.instructions.md](instructions/qa-validation-standards.instructions.md)

## Contexto del proyecto

Las entradas y entregables están en [INPUTS_POR_AGENTE.md](../INPUTS_POR_AGENTE.md). Se escriben en el workspace seleccionado; el tracker usa `BMAD_TRACKER`, la configuración efectiva `BMAD_CONFIG` y los perfiles compartidos `ENGINE_ROOT`. Conserva el historial y registra un único destinatario por handoff.

La selección de proveedor y effort sigue el [contrato del runtime](../bmad_runtime/README.md). Consulta [GUIDE.md](../GUIDE.md) para compuertas, implementación y retrabajo.
