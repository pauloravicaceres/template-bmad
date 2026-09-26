---
name: qa-strict-testing
description: Skill de rigor analítico para el QA Automation. Fuerza el diseño adversarial, prohíbe tautologías e impone pruebas exhaustivas de validadores y estado reactivo.
type: skill
tags: [qa, testing, xunit, jest, auditoria]
---

# Rigor de Pruebas (Zero-Tautology Policy)

## Workflow de Auto-Auditoría para Pruebas Generadas
Antes de reportar éxito en el tracker, revisa tu propio código de pruebas aplicando este checklist. Si fallas en algo, corrígelo con `write_file`:

### 1. Diseño Adversarial y Casos Límite
- ¿Implementaste al menos **1 Happy Path** y **2 Sad Paths** por cada Feature?
- ¿Probaste condiciones límite (ej. fechas en el pasado, strings vacíos, IDs inexistentes)?
- **Aislamiento de Validación (.NET):** ¿Escribiste pruebas específicas para la clase `AbstractValidator<TCommand>` (ej. usando `TestValidate()`) independientemente del Handler?

### 2. Detección de Pruebas Tautológicas (Anti-Patrón)
- Verifica tus bloques `// Assert`. 
- **PROHIBIDO** mockear un repositorio para que devuelva `X`, inyectarlo en una clase que simplemente devuelve lo que le da el repositorio, y afirmar que `Assert.Equal(X, result)`. 
- *Corrección:* Si el servicio es un simple passthrough, prueba el Endpoint a nivel de integración. En pruebas unitarias, enfócate en la lógica condicional, bucles y transformación de datos.

### 3. Cobertura del Ecosistema Angular 22
- En Jest, ¿estás probando la lógica reactiva? 
- No te limites a probar el DOM (`fixture.nativeElement.querySelector`). Debes invocar los métodos del componente y verificar usando `expect(component.mySignal()).toBe(...)` para asegurar que la mutación del estado reactivo (Signals) es matemáticamente correcta tras la acción.

### 4. Limpieza y Descarte
- Si levantaste contenedores Docker con Testcontainers, ¿te aseguraste de que la clase de prueba implemente `DisposeAsync()` para destruir el contenedor al terminar la suite?

No notifiques finalización hasta que el código de prueba sea robusto, destructivo y mantenible.