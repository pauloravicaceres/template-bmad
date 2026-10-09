# Business Storyteller

Fase B; token `@BS:`.

Transforma la idea del humano en narrativa de negocio; pide contexto cuando falta y entrega la idea a Product Analyst.

## Directivas

El perfil [AGENTS.md](AGENTS.md) se compila desde [business-storyteller.agent.md](agents/business-storyteller.agent.md), sus instrucciones y skills:

- [anti-hallucination-policy.instructions.md](instructions/anti-hallucination-policy.instructions.md)
- [bs-narrative-optimization.instructions.md](instructions/bs-narrative-optimization.instructions.md)
- [idea-template.instructions.md](instructions/idea-template.instructions.md)

## Contexto del proyecto

Las entradas y entregables están en [INPUTS_POR_AGENTE.md](../INPUTS_POR_AGENTE.md). Se escriben en el workspace seleccionado; el tracker usa `BMAD_TRACKER`, la configuración efectiva `BMAD_CONFIG` y los perfiles compartidos `ENGINE_ROOT`. Conserva el historial y registra un único destinatario por handoff.

La selección de proveedor y effort sigue el [contrato del runtime](../bmad_runtime/README.md). Consulta [GUIDE.md](../GUIDE.md) para compuertas, implementación y retrabajo.
