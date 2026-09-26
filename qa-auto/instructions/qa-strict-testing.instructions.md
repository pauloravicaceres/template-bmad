---
description: 'Estándares estrictos de testing automatizado, cobertura de Criterios de Aceptación, política de Cero Tautologías y reporte en el tracker para el agente QA Automation.'
applyTo: '**'
---

# QA Automation Standards — Rigor de Pruebas & Zero-Tautology

## 1. Convenciones y Diseño de Pruebas Obligatorio
- **Patrón AAA:** Toda prueba unitaria o de integración debe estructurarse visualmente con bloques `// Arrange`, `// Act`, `// Assert`.
- **Nomenclatura BDD:** Formato obligatorio `NombreMetodo_EstadoBajoPrueba_ComportamientoEsperado` (ej. `CreateOrder_ConStockInsuficiente_DebeLanzarValidationException`).
- **Cobertura Mínima por Feature:** Cada slice o componente probado debe contar con al menos **1 Happy Path** y **2 Sad Paths** (pruebas de límites, datos nulos, IDs inexistentes).
- **Prohibición de Mocks Tautológicos:** Tienes estrictamente prohibido escribir pruebas donde se configure un mock para devolver un valor y simplemente se verifique que el mock devolvió ese valor. Las pruebas deben validar lógica condicional, transformaciones, validadores y mutación de estado.

## 2. Directivas Técnicas por Plataforma
- **Backend (.NET 8/10 Modulith):**
  - Pruebas unitarias de Handlers y validadores con `xUnit`, `NSubstitute` y `FluentAssertions`.
  - Pruebas de integración de Minimal APIs con `WebApplicationFactory<Program>`.
  - Pruebas con base de datos efímera usando `Testcontainers` (PostgreSQL) implementando `IAsyncLifetime` o `ICollectionFixture<T>` para no levantar contenedores por cada prueba individual.
- **Frontend (Angular 22 Zoneless):**
  - Pruebas con `Jest` y `provideHttpClientTesting`.
  - Validación de estado reactivo mediante verificación de valores en `Signals` (`expect(component.mySignal()).toBe(...)`).

## 3. Protocolo de Reporte y Handoff
1. Tras escribir los archivos de prueba con `write_file`, ejecuta `read_file` para certificar que el archivo existe y compila sintácticamente.
2. Si todas las pruebas pasan y la cobertura es sólida, realiza el handoff hacia el `@CODE-REVIEW:`.
3. Si detectas fallos en el código de los desarrolladores, no lo modifiques; reporta `[RECHAZADO]` en el tracker y devuelve el turno al `@DEV-BACK:` o `@DEV-FRONT:`.

[IMPORT_SKILL: skills/qa-strict-testing/SKILL.md]
[IMPORT_SKILL: skills/tracker-logger/SKILL.md]
