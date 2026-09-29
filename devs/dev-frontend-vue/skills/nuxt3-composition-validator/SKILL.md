---
name: nuxt3-composition-validator
description: Skill de auto-auditoría estricta para validar que el código Vue cumple con Composition API (<script setup>), Nitro SSR y tipado estricto antes del handoff.
type: skill
tags: [frontend, vue3, nuxt3, nitro, auditoria, dev]
---

# Nuxt 3 & Composition API Code Validator — Auditoría de Calidad Frontend

## Workflow de Auto-Revisión OBLIGATORIO
Antes de escribir `@QA-AUTO:` o `@CODE-REVIEW:` en el tracker, debes ejecutar mentalmente este checklist sobre los componentes (`.vue`) y endpoints Nitro (`.ts`) que acabas de escribir. Si algún paso falla, usa `write_file` para corregirlo inmediatamente:

1. **Regla de Composition API Estricta:** 
   - Abre mentalmente tus archivos `.vue`. ¿Usaste el bloque `<script setup lang="ts">`? ¿Hay algún rastro de Options API (`export default { ... }`)? Si lo hay, refactoriza a Composition API INMEDIATAMENTE.
2. **Regla de Fetching SSR (Nuxt):**
   - ¿Estás usando `axios` o `fetch` nativo dentro del ciclo de vida del componente (`onMounted`)? Si es así, cámbialo INMEDIATAMENTE a `useFetch` o `useAsyncData` para garantizar hidratación correcta y evitar doble renderizado.
3. **Regla de Integración Nitro:**
   - Si creaste un endpoint para el frontend (BFF), ¿lo colocaste correctamente en `server/api/` y usaste `defineEventHandler`?
4. **Regla de Tipado Estricto:**
   - ¿Hay algún tipo `any` en los modelos, `ref()`, o props de los componentes? Usa `defineProps<{ miProp: string }>()` para tipado perfecto.
5. **Regla UI PrimeVue / Tailwind CSS:**
   - ¿Usaste `<style scoped>` para acomodar un flexbox o márgenes? Bórralo INMEDIATAMENTE y usa las clases utilitarias de Tailwind en el `<template>`.

No notifiques finalización en el tracker hasta que este checklist esté 100% verificado en el código fuente.
