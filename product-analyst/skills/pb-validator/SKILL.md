---
name: pb-validator
description: Skill de auto-auditoría estricta para validar que un Product Brief (PB) cumple con las 8 secciones canónicas y políticas anti-alucinación antes de solicitar la revisión manual del humano.
type: skill
tags: [qa, auditoria, product-brief, product-analyst, discovery]
---

# PB Validator — Auditoría y Control de Calidad del Product Brief

## Goal
Garantizar que el borrador del Product Brief cumpla estrictamente con la estructura canónica de 8 secciones y las políticas de certidumbre antes de realizar el handoff o delegación al operador humano[cite: 2, 3].

## Input
- El borrador del Product Brief recién generado (`pb_[Nombre_Corto].md`) en la carpeta `CARPETA_SALIDA`[cite: 3].
- El archivo de la idea de usuario original leído desde la `CARPETA_ENTRADA`[cite: 3].

## Workflow

Ejecuta el siguiente flujo de validación paso a paso de forma interna. Si algún paso falla, detén el proceso y corrige el archivo inmediatamente.

1. **Validar Estructura y Nomenclatura:**
   - Verifica que el nombre del archivo respete la convención `pb_[Nombre_Corto].md` (formato snake_case, con un máximo de 4 palabras representativas del producto)[cite: 2].
   - Confirma la existencia exacta y secuencial de las 8 secciones OBLIGATORIAS: `1. PROBLEMA`, `2. USUARIOS`, `3. OBJETIVO`, `4. ALCANCE INICIAL`, `5. RESTRICCIONES`, `6. CRITERIOS DE ÉXITO`, `7. SUPUESTOS` y `8. PREGUNTAS ABIERTAS`[cite: 2].

2. **Validar Política Anti-Alucinación (Certidumbre):**
   - En la sección "1. PROBLEMA", comprueba que las inferencias lógicas sobre la causa raíz estén separadas de los hechos comprobables y etiquetadas obligatoriamente con `⚠️ SUPUESTO:`[cite: 2].
   - En la sección "6. CRITERIOS DE ÉXITO", verifica que cualquier métrica cuantitativa inventada o no explícita en el input original esté marcada con `⚠️ [PROPUESTO]:` (o como `❓ No documentado` si no hay datos)[cite: 2].
   - En la sección "7. SUPUESTOS", asegura que toda hipótesis operativa, de usuario o canal esté etiquetada con `⚠️ SUPUESTO:`[cite: 2].

3. **Validar Calidad del Alcance y Objetivo:**
   - Verifica que el "3. OBJETIVO (OUTCOME)" sea exclusivamente un resultado de negocio deseado o cambio de comportamiento observable, y NO una lista de funcionalidades[cite: 2].
   - Revisa que el "4. ALCANCE INICIAL (MVP)" contenga un bloque de "Exclusiones Explícitas (Fuera de Alcance)" detallando las capacidades complejas que no deben construirse en el MVP[cite: 2].

4. **Validar Handoff (Criterio de Salida):**
   - Asegura que el mensaje de delegación (Handoff) finalizado invoque únicamente la etiqueta `@HUMANO:`[cite: 3].
   - **Regla Crítica:** Verifica de forma estricta que no exista ninguna inclusión o mención de etiquetas de otros agentes (como `@PM:`, `@BA:`, etc.) en la orden de Handoff[cite: 3].

## Notas
- **Modo Auto-Corrección:** Si detectas fallos durante el Workflow, no pidas permiso. Sobreescribe el archivo `pb_*.md` mediante la herramienta `write_file` con las correcciones antes de avanzar[cite: 3].
- Tienes prohibido escribir la orden de handoff en el `tracker_bmad.md` hasta que este Workflow se complete con 100% de éxito en todos sus puntos.