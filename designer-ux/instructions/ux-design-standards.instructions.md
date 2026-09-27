---
description: 'Usar al generar interfaces visuales y wireframes ASCII. Establece la regla 1 a 1 de escenarios BDD / tareas de Spec Kit vs estados visuales y el estándar de diseño estructural.'
applyTo: '**'
---

# Estándares de Diseño UX y Protocolo SDD (Spec Kit Bridge)

> Metodología visual obligatoria para la especificación de interfaces en el framework BMAD integrada con GitHub Spec Kit.

---

## 1. Principio Fundamental: 1 Escenario Spec Kit / BDD = 1 Estado Visual
Cada escenario funcional definido en `spec.md` y cada tarea de UI identificada en `tasks.md` (y Criterios de Aceptación Gherkin de la HU técnica) debe contar con **una representación visual dedicada**:

- **Happy Path (Flujo Exitoso):** Estado interactivo ideal con datos completos, botones principales habilitados y flujo fluido según las subtareas de `tasks.md`.
- **Sad Path (Escenarios Alternativos / Error):**
  - Estados deshabilitados (ej. botón inactivo hasta completar validación).
  - Mensajes de error en línea (alertas contextuales junto al campo inválido).
  - Modales o pop-ups de bloqueo / confirmación destructiva.
  - Vistas vacías (Empty States) cuando no hay datos disponibles.

---

## 2. Protocolo de Diseño: Wireframes ASCII

Todo estado visual debe documentarse representando con precisión la topología de la interfaz dentro del bloque de código `text`:

```text
+-------------------------------------------------------------------+
|  [Logo / Título de la Aplicación]              [Usuario / Estado]  |
+-------------------------------------------------------------------+
|                                                                   |
|   TITULO DE LA SECCION                                            |
|   Descripcion breve del flujo o instrucción...                     |
|                                                                   |
|   +-----------------------------------------------------------+   |
|   | Campo 1: [ Valor ingresado o Placeholder............. ]   |   |
|   | Error:   * Mensaje de validación en color destacado *    |   |
|   +-----------------------------------------------------------+   |
|                                                                   |
|   [ (X) Botón Deshabilitado ]         [ [✓] Botón Acción Primaria ]|
+-------------------------------------------------------------------+
```

---

## 3. Mapeo de Tareas Spec Kit y Notas de Interfaz (Handoff Frontend)
Cada estado visual debe concluir obligatoriamente con:
- **ID de Tarea Spec Kit:** Tarea asociada de `tasks.md` (ej. `Task 1.2: UI Component Form`).
- **Disparadores de Estado:** Qué evento exacto provoca la transición hacia esta pantalla.
- **Reglas de Componente:** Comportamiento dinámico (ej. campos con auto-focus, dropdowns con búsqueda en tiempo real, modales con backdrop no descartable).

---

## 4. Directiva para Ecosistemas Preexistentes (Modo Brownfield)
Si existe el archivo `.specify/memory/constitution.md` o `.specify/memory/constitution.md`:
- **Coexistencia y Ergonomía Visual:** Lee las especificaciones de interfaz y tecnología de presentación descritas en la constitución.
- Documenta en las Notas de Interfaz si la pantalla se concibe como una interfaz integrada, un módulo embebido o una aplicación satélite independiente, garantizando consistencia ergonómica sin asumir capacidades que el entorno legacy no soporte.
- Si el archivo NO existe (Modo Greenfield), diseña la interfaz moderna libremente sin restricciones heredadas.

[IMPORT_SKILL: skills/tracker-logger/SKILL.md]
