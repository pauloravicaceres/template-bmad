---
description: 'Usar al generar interfaces visuales y wireframes ASCII. Establece la regla 1 a 1 de escenarios Gherkin vs estados visuales y el estándar de diseño estructural.'
applyTo: '**'
---

# Estándares de Diseño UX y Protocolo Híbrido

> Metodología visual obligatoria para la especificación de interfaces en el framework BMAD.

---

## 1. Principio Fundamental: 1 Escenario BDD = 1 Estado Visual
Cada Criterio de Aceptación (CA) redactado bajo sintaxis Gherkin (`Dado / Cuando / Entonces`) en la Historia de Usuario aprobada debe contar con **una representación visual dedicada**:

- **Happy Path (Flujo Exitoso):** Estado interactivo ideal con datos completos, botones principales habilitados y flujo fluido.
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

## 3. Notas de Interfaz (Handoff para el Desarrollador Frontend)
Cada estado visual debe concluir obligatoriamente con una **Nota de Interfaz** que detalle:
- **Disparadores de Estado:** Qué evento exacto provoca la transición hacia esta pantalla.
- **Reglas de Componente:** Comportamiento dinámico (ej. campos con auto-focus, dropdowns con búsqueda en tiempo real, modales con backdrop no descartable).

---

## 4. Directiva para Ecosistemas Preexistentes (Modo Brownfield)
Si existe el archivo `files/context/legacy_ecosystem.md`:
- **Coexistencia y Ergonomía Visual:** Lee las especificaciones de interfaz y tecnología de presentación descritas en el archivo legacy.
- Documenta en las Notas de Interfaz si la pantalla se concibe como una interfaz integrada, un módulo embebido o una aplicación satélite independiente, garantizando consistencia ergonómica sin asumir capacidades que el entorno legacy no soporte.
- Si el archivo NO existe (Modo Greenfield), diseña la interfaz moderna libremente sin restricciones heredadas.


[IMPORT_SKILL: skills/tracker-logger/SKILL.md]
