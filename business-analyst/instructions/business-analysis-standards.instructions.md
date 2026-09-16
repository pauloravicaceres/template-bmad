---
description: 'Usar al redactar Historias de Usuario, Criterios de Aceptación y cualquier contenido funcional. Define los principios INVEST, trazabilidad obligatoria de fuente, reglas de fidelidad al input y separación negocio/técnica.'
applyTo: '**'
---

# Estándares de Análisis de Negocio

> Referencia de habilidades transversales para el agente BA de BMAD.
> Aplicable en todos los escenarios: HU nueva o corrección por feedback del QA.

## Principios INVEST (aplicados a la HU)

| Letra | Principio | Verificación práctica |
|---|---|---|
| **I** | Independent | La HU puede desarrollarse y desplegarse sin bloquear a otra HU del backlog |
| **N** | Negotiable | El scope está delimitado, pero la solución técnica es abierta |
| **V** | Valuable | El "Para [valor de negocio]" es claro y verificable por el PO |
| **E** | Estimable | El equipo técnico puede estimarla sin pedir más clarificaciones |
| **S** | Small | Cubre una sola transacción o un solo valor entregado |
| **T** | Testable | Cada CA tiene un resultado medible; un QA puede convertirlo en caso de prueba |

## Trazabilidad Obligatoria

- **Cada regla de negocio, dato o CA incluido debe indicar su fuente.** Si proviene del Product Brief, del Plan de Gestión o de una decisión explícita registrada, citarlo. Sin fuente → marcar como `⚠️ [PROPUESTO]`.
- El pie de cada HU debe incluir: `> **Origen:** [Nombre del archivo fuente]. Todo contenido generado que no esté en la fuente se marca ⚠️ [PROPUESTO].`

## Formato de Criterios de Aceptación (CA)

- Estructura verificable: **Dado [contexto] / Cuando [acción] / Entonces [resultado medible]**.
- Cada CA debe ser **testable**: un ingeniero de QA puede convertirlo directamente en un caso de prueba automatizado.
- Cobertura obligatoria:
  - ✅ **Happy Path:** El flujo ideal sin errores.
  - ❌ **Sad Path(s):** Al menos un escenario de error, dato inválido o restricción de negocio conocida.
  - Los escenarios de error deben provenir del input, no ser inventados.

## Separación Negocio / Técnica

- El cuerpo de la HU **no menciona** tecnologías, nombres de bases de datos, frameworks, endpoints REST ni tipos de variables.
- Los detalles técnicos (si aplican) van en la sección **Notas Técnicas** (opcional) o se delegan a una subtarea del equipo técnico.
- Usar lenguaje centrado en comportamiento observable: "el sistema solicita confirmación", "el usuario selecciona la opción", "el sistema registra el evento".

## Codificación de Archivos

Todos los archivos de salida generados por el agente BA (`hu_*.md`) deben ser **UTF-8 sin BOM**. Al usar `write_file` vía MCP, verificar que el resultado no indique advertencias de codificación.

## Reglas de Fidelidad a la Fuente

- Usar ÚNICAMENTE los datos del Product Brief y el Plan de Gestión para completar los campos directos (objetivo, alcance, reglas, CAs).
- Cualquier contenido que el agente añada más allá del input → marcarlo `⚠️ [PROPUESTO]`.
- La HU debe separar claramente los **datos del usuario** (fuente citada) de la **propuesta del agente** (marcada).
