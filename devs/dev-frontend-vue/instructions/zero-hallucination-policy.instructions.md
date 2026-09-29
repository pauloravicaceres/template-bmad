---
description: 'Política estricta de Cero Alucinación para el agente Frontend Developer. Prohíbe mocks, uso de tipo "any", Options API y fuerza Vue 3 Composition API con Nuxt 3 SSR.'
applyTo: '**'
---

# Zero Hallucination Policy — Frontend (Vue 3 / Nuxt 3)

## 1. Fronteras Estrictas de Implementación
- **Cero Placeholders y Mocks:** Tienes PROHIBIDO dejar funciones vacías (ej. `const saveData = () => { // TODO }`) o inicializar `ref` con arrays ficticios. Debes usar `useFetch` o crear el endpoint en `server/api/` (Nitro) para consumir o mockear datos formales.
- **Cero Tipo "any":** Tienes estrictamente PROHIBIDO tipar variables, `ref<T>`, funciones o props con `any`. Todo debe estar fuertemente tipado mediante Interfaces o Types de TypeScript.
- **Cero Código Obsoleto (Legacy Vue 2 / Options API):** 
  - 🚫 PROHIBIDO usar Options API (`export default { data() {} }`).
  - 🚫 PROHIBIDO usar Vuex. Si hay estado global, usa Pinia o el composable nativo `useState` de Nuxt.
  - ✅ OBLIGATORIO usar el bloque `<script setup lang="ts">`.
- **Cero CSS Hackeado / Maquetación Prohibida en Componentes:**
  - 🚫 PROHIBIDO usar `:deep()` para sobrescribir estilos estructurales sin justificación extrema.
  - 🚫 PROHIBIDO escribir reglas de maquetación (márgenes, paddings, flexbox, grids, gaps, posicionamiento) dentro de la etiqueta `<style scoped>` de los componentes `.vue`.
  - ✅ OBLIGATORIO usar EXCLUSIVAMENTE las clases utilitarias de **Tailwind CSS** directamente en el `<template>`. Ejemplos canónicos:
    - Layout: `flex`, `flex-col`, `flex-row`, `flex-wrap`
    - Alineación: `justify-between`, `justify-center`, `items-center`
    - Espaciado: `p-2`, `p-4`, `m-0`, `gap-3`, `px-3`, `py-2`
    - Grid Responsivo: `grid`, `grid-cols-12`, `md:col-span-6`, `lg:col-span-4`
  - Para ajustes visuales propios de un componente PrimeVue usa las propiedades nativas (ej. `unstyled`, `pt` (Pass Through) o `class`).

## 2. Fidelidad Absoluta al Contrato
- Las interfaces de TypeScript que definas para los payloads HTTP deben mapear exactamente con los DTOs expuestos en el `tech-design_*.md`. Si el diseño dice `productId: string`, no lo declares como `number`.

## 3. Protocolo Anti-Confirmación Fantasma
1. Ejecuta `write_file` para generar los componentes (`.vue`, `.ts`).
2. Obligatorio: Ejecuta `read_file` sobre las rutas recién escritas para verificar que el código está completo y bien formado.
3. Solo tras validar físicamente los archivos, notifica la finalización en el tracker.

[IMPORT_SKILL: skills/nuxt3-composition-validator/SKILL.md]
[IMPORT_SKILL: skills/tracker-logger/SKILL.md]