---
description: 'Plantilla maestra para la generación y mantenimiento de la Matriz de Calidad y Trazabilidad Viva (QA).'
---

# 🏗️ PLANTILLA MAESTRA: REPORTE DE CALIDAD Y TRAZABILIDAD VIVA (`qa-report.md`)

## 🎯 OBJETIVO Y REGLA CRÍTICA DE RENDERIZADO SELECTIVO
Este documento dicta la estructura obligatoria del archivo `qa-report.md` (o `qa-traceability-matrix.md`) que debes mantener actualizado en la carpeta correspondiente a QA/Testing de tu proyecto.

**🚨 REGLA CRÍTICA DE RENDERIZADO SELECTIVO:** 
NO debes regenerar la matriz o el reporte de todo el sistema desde cero en cada iteración. Al validar una nueva Historia de Usuario (HU), debes mantener la estructura de este documento intacta y **SOLO modificar o agregar a los diagramas Mermaid los flujos, pruebas y criterios correspondientes a la HU actual**. Las áreas del sistema no afectadas por la HU actual se declaran implícita o explícitamente como "Sin cambios en esta iteración" para proteger el límite de tokens y acelerar el procesamiento.

---

## 📄 ESTRUCTURA OBLIGATORIA DEL DOCUMENTO CONSOLIDADO

Tu archivo `qa-report.md` debe contener obligatoriamente las siguientes secciones. Completa y actualiza cada una utilizando la sintaxis de Markdown y diagramas de Mermaid correspondientes:

### 1. AI QA Review Dashboard
- Un panel de texto (estilo ASCII art o tabla) que resuma la ejecución global y de la iteración actual.
- Debe incluir: Tests ejecutados, Pasados, Fallados, Bloqueados, Cobertura Funcional y Nivel de Riesgo.

### 2. Requirements Traceability
- **Diagrama de Trazabilidad:** Diagrama `flowchart` de Mermaid que conecte visualmente: Historia de Usuario (HU) -> Criterios de Aceptación (CA) -> Casos de Prueba (TC).
- *(Añade a este diagrama únicamente los nodos de la HU que estás probando en el ciclo actual).*

### 3. Failure Impact Diagram (En caso de fallos)
- Si un test falla, crea un diagrama `flowchart` que mapee el impacto del defecto.
- Debe conectar el Test Fallido -> Componentes Arquitectónicos involucrados (Controladores, DB, APIs) -> Funcionalidades del Negocio afectadas.
- Si no hay fallos, deja esta sección vacía o con un indicador de "0 fallos críticos detectados".

### 4. State Transition / User Journey
- **Recorrido del Usuario o Transición de Estados:** Diagrama `flowchart` o `stateDiagram-v2` que demuestre el flujo real que ha sido probado (muy útil para workflows o journeys de usuario end-to-end).
- Muestra el camino de éxito y dónde se rompen los flujos si hay errores detectados en la prueba.

### 5. Test Coverage & Hotspots
- Un mapa rápido (visual con Mermaid o en texto) que muestre qué módulos de la aplicación tienen mayor cobertura de pruebas y dónde se concentran los defectos (Defect Hotspots).
- *(Actualiza los porcentajes y áreas de riesgo a medida que vas introduciendo y ejecutando nuevas pruebas).*
