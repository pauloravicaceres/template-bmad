---
description: 'Política estricta de Cero Alucinación para el agente Backend Developer. Prohíbe el uso de mocks, excepciones no implementadas y librerías ajenas a la Lex Superior de .NET Modulith.'
applyTo: '**'
---

# Zero Hallucination Policy — Backend (.NET 8/10)

## 1. Fronteras Estrictas de Implementación
- **Cero Placeholders:** Tienes PROHIBIDO escribir comentarios como `// TODO: Implement database call` o usar `throw new NotImplementedException()`. Cada Handler o Endpoint que generes debe estar 100% funcional.
- **Cero Mocks Hardcodeados:** Si el Tech Design exige consultar datos, inyecta obligatoriamente el `DbContext` y usa Entity Framework Core. Está estrictamente prohibido simular respuestas en memoria (ej. `var users = [];`).
- **Cero Magic Strings:** Tienes prohibido usar cadenas de texto literales para nombres de propiedades, roles o esquemas de base de datos dentro de la lógica. Utiliza `nameof()`, constantes (const) o variables `static readonly`.
- **Librerías Fantasma Prohibidas:** 
  - 🚫 Usa `Mapster`, NUNCA `AutoMapper`.
  - 🚫 Usa `System.Text.Json`, NUNCA `Newtonsoft.Json`.
  - 🚫 Usa `ICarterModule`, NUNCA `[ApiController]`.

## 2. Fidelidad Absoluta al Contrato
- Los nombres de las propiedades en los `Record` (Commands/Queries/Responses) y los tipos de datos deben ser **copias exactas byte por byte** de los JSON del `tech-design_*.md`. No apliques transformaciones de nombres por iniciativa propia (ej. de `customerId` a `clientId`).

## 3. Protocolo Anti-Confirmación Fantasma
1. Ejecuta `write_file` para generar el código `.cs`.
2. Obligatorio: Ejecuta `read_file` sobre la ruta exacta recién escrita para verificar que el archivo existe y no está truncado.
3. Solo tras validar físicamente el archivo, notifica la finalización en el tracker.

[IMPORT_SKILL: skills/vsa-validator/SKILL.md]
[IMPORT_SKILL: skills/tracker-logger/SKILL.md]
