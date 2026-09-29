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
- **Cero CSS Hackeado / Maquetación Prohibida en Componentes:**
  - 🚫 PROHIBIDO usar `::ng-deep` para sobrescribir estilos de PrimeNG.
  - 🚫 PROHIBIDO escribir reglas de maquetación (márgenes, paddings, flexbox, grids, gaps, posicionamiento) en los archivos `.css` o `.scss` de los componentes.
  - ✅ OBLIGATORIO usar EXCLUSIVAMENTE las clases utilitarias de **PrimeFlex** directamente en el `.html`. Ejemplos canónicos:
    - Layout: `flex`, `flex-column`, `flex-row`, `flex-wrap`
    - Alineación: `justify-content-between`, `justify-content-center`, `align-items-center`
    - Espaciado: `p-2`, `p-4`, `m-0`, `gap-3`, `px-3`, `py-2`
    - Grid Responsivo: `col-12`, `md:col-6`, `lg:col-4`
    - Bordes/Efectos: `border-round`, `border-round-lg`, `shadow-2`
  - Para ajustes visuales propios de un componente PrimeNG usa exclusivamente `[style]`, `[class]` o `styleClass` en el propio tag del componente.

## 2. Fidelidad Absoluta al Contrato
- Las interfaces de TypeScript que definas para los payloads HTTP deben mapear exactamente con los DTOs expuestos en el `tech-design_*.md`. Si el diseño dice `productId: string`, no lo declares como `number`.

## 3. Protocolo Anti-Confirmación Fantasma
1. Ejecuta `write_file` para generar los componentes (`.ts`, `.html`).
2. Obligatorio: Ejecuta `read_file` sobre las rutas recién escritas para verificar que el código está completo y bien formado.
3. Solo tras validar físicamente los archivos, notifica la finalización en el tracker.


[IMPORT_SKILL: skills/zoneless-validator/SKILL.md]
[IMPORT_SKILL: skills/tracker-logger/SKILL.md]
