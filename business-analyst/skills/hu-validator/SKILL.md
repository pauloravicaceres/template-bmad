---
name: hu-validator
description: Skill de auto-auditoría estricta para validar que una Historia de Usuario (HU) en formato Markdown cumple con todos los estándares de calidad, BDD y políticas anti-alucinación antes de ser delegada.
type: skill
tags: [qa, auditoria, bdd, gherkin, business-analyst]
---

# HU Validator — Auditoría y Control de Calidad de Historias de Usuario

## Goal
Garantizar que la Historia de Usuario generada cumpla estrictamente con la plantilla base (secciones, Criterios de Aceptación, trazabilidad) antes de realizar el handoff (delegación) al agente QA Documental.

## Input
- El borrador de la Historia de Usuario recién generado (`hu_[ID]_[nombre_corto].md`).
- El contexto actual del agente (Product Brief o requerimiento original).

## Workflow

Ejecuta el siguiente flujo de validación paso a paso de forma interna. Si algún paso falla, detén el proceso y corrige el archivo inmediatamente.

1. **Validar Estructura y Nomenclatura:**
   - Verifica que el nombre del archivo use `snake_case`, tenga máximo 4 palabras descriptivas y NO incluya el nombre del proyecto.
   - Confirma la existencia exacta de las 5 secciones obligatorias (`1. HISTORIA DE USUARIO`, `2. CRITERIOS DE ACEPTACIÓN`, `3. DIAGRAMAS`, `4. DEFINITION OF DONE`, `5. ORDEN DE DELEGACIÓN`).

2. **Validar Criterios de Aceptación (BDD):**
   - Asegura que haya ≥ 2 Criterios de Aceptación.
   - Verifica que exista explícitamente al menos un "Sad Path" (camino de error).
   - Confirma que la sintaxis de todos los criterios sea Gherkin (`Dado` / `Cuando` / `Entonces`).

3. **Validar Política Anti-Alucinación:**
   - Escanea el texto en busca de cualquier asunción, funcionalidad o tecnología no presente en el Product Brief.
   - Si existe, verifica que esté marcada con la etiqueta `⚠️ [PROPUESTO]`.
   - Elimina cualquier detalle de implementación técnica (nombres de BD, APIs específicas, frameworks).

4. **Validar Trazabilidad:**
   - Confirma que el pie de página ("Origen") esté documentado.
   - Revisa que el Definition of Done (DoD) contenga los 4 ítems obligatorios.

5. **Validar Handoff (Criterio de Salida):**
   - Asegura que el mensaje `@QA: ...` en la sección 5 esté escrito en una ÚNICA línea de texto continuo, sin saltos de línea (para que el Watcher Python no falle).

## Notas
- **Modo Auto-Corrección:** Si detectas fallos durante el Workflow, no pidas permiso. Sobreescribe tu propio archivo `hu_*.md` con las correcciones antes de registrar el token en el tracker.
- Nunca escribas en el `tracker_bmad.md` hasta que el Workflow se complete con 100% de éxito.