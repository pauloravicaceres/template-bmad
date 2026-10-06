---
description: 'Plantilla maestra para la generación del Reporte de Impacto y Code Review Vivo.'
---

# 🏗️ PLANTILLA MAESTRA: REPORTE DE IMPACTO Y CODE REVIEW VIVO (`impact-analysis-report.md`)

## 🎯 OBJETIVO Y REGLA CRÍTICA DE RENDERIZADO SELECTIVO
Este documento dicta la estructura obligatoria del archivo `impact-analysis-report.md` que debes crear o actualizar en `documents/code-review/` (ruta obligatoria: `documents/code-review/impact-analysis-report.md`) tras auditar el código de una Historia de Usuario (HU).

**🚨 REGLA CRÍTICA DE RENDERIZADO SELECTIVO:** 
NO debes mapear la arquitectura de todo el repositorio desde cero en cada iteración. Al auditar una HU, debes mantener la estructura global del documento intacta y **SOLO modificar o generar los diagramas Mermaid y reportes correspondientes a los archivos, APIs y componentes alterados en la iteración/HU actual**. Las zonas del código no impactadas se ignoran o se declaran explícitamente como "Sin impacto en este PR/HU".

---

## 📄 ESTRUCTURA OBLIGATORIA DEL DOCUMENTO CONSOLIDADO

Tu archivo `impact-analysis-report.md` debe contener obligatoriamente las siguientes secciones. Completa y actualiza cada una utilizando la sintaxis de Markdown y diagramas de Mermaid correspondientes:

### 1. AI Code Review Dashboard
- Un panel resumen en texto (estilo ASCII art) mostrando las métricas del análisis.
- Incluye: Archivos analizados, Violaciones arquitectónicas detectadas, Problemas de seguridad/calidad, Deuda técnica encontrada y Cobertura de tests faltante.

### 2. Architecture Compliance & Traceability
- **Diagrama de Cumplimiento (Mermaid):** Diagrama `flowchart` que demuestre el flujo **real** implementado conectando capas (ej. Frontend Component -> Service -> Backend API -> Controller -> DB).
- **Alerta de Desviación:** Si el código no respeta la arquitectura definida (ej. un Controller llama directamente al Repository saltándose el Service), este diagrama debe **señalar explícitamente el "salto de capa"** o desviación.

### 3. Change Impact Diagram
- **Diagrama de Impacto de Cambios (Mermaid):** (El diagrama más crítico de la revisión).
- Muestra visualmente qué Controladores, Servicios, Repositorios o Componentes UI se ven afectados por los cambios introducidos en la HU.
- Debe incluir nodos que representen las pruebas unitarias/integración asociadas para visualizar rápidamente si los componentes alterados están cubiertos por tests o no.

### 4. Dependency / Coupling Graph
- **Grafo de Acoplamiento (Mermaid):** Diagrama que exponga las dependencias y el acoplamiento real entre los módulos modificados.
- Útil para advertir deuda técnica temprana (ej. módulos circulares o servicios de dominio dependiendo excesivamente de infraestructura externa).
