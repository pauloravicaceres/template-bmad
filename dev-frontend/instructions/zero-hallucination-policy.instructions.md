---
description: 'Política estricta de Cero Alucinación para el agente Frontend Developer. Prohíbe mocks, uso de tipo "any", directivas legacy y fuerza Angular 22 Zoneless con Signals.'
applyTo: '**'
---

# Zero Hallucination Policy — Frontend (Angular 22)

## 1. Fronteras Estrictas de Implementación
- **Cero Placeholders y Mocks:** Tienes PROHIBIDO dejar funciones vacías (ej. `saveData() { // TODO }`) o inicializar Signals con arrays ficticios. Debes crear e inyectar el servicio `HttpClient` para consumir los datos reales.
- **Cero Tipo "any":** Tienes estrictamente PROHIBIDO tipar variables, observables, signals o parámetros de función con `any`. Todo debe estar fuertemente tipado mediante Interfaces o Types.
- **Cero Código Obsoleto (Legacy Angular):** 
  - 🚫 PROHIBIDO importar `zone.js` o usar `NgModules`.
  - 🚫 PROHIBIDO usar `*ngIf` o `*ngFor`.
  - 🚫 PROHIBIDO suscribirte manualmente con `.subscribe()` cuando el flujo pueda resolverse nativamente con `toSignal()` o pipelines reactivos.
- **Cero CSS Hackeado:** Está prohibido el uso de `::ng-deep` para sobrescribir estilos de PrimeNG. Debes utilizar las propiedades nativas del componente (ej. `[style]`, `[class]`, `styleClass`) o el sistema de grillas estándar.

## 2. Fidelidad Absoluta al Contrato
- Las interfaces de TypeScript que definas para los payloads HTTP deben mapear exactamente con los DTOs expuestos en el `tech-design_*.md`. Si el diseño dice `productId: string`, no lo declares como `number`.

## 3. Protocolo Anti-Confirmación Fantasma
1. Ejecuta `write_file` para generar los componentes (`.ts`, `.html`).
2. Obligatorio: Ejecuta `read_file` sobre las rutas recién escritas para verificar que el código está completo y bien formado.
3. Solo tras validar físicamente los archivos, notifica la finalización en el tracker.


[IMPORT_SKILL: skills/zoneless-validator/SKILL.md]
