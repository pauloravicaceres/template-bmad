---
description: 'Usar al generar interfaces visuales, llamadas al servidor Stitch y wireframes ASCII. Establece la regla 1 a 1 de escenarios Gherkin vs estados visuales y el estándar de diseño estructural.'
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

## 2. Protocolo Híbrido: Stitch + Wireframes ASCII

Todo estado visual debe documentarse bajo una estructura dual:

### Acción A — Generación en Stitch (Servidor MCP)
1. Invocar la herramienta `generate_screen_from_text` (o la herramienta correspondiente del servidor `stitch`).
2. **Estructura del Prompt en Stitch:** Redactar la descripción detallada en **inglés**, especificando:
   - Tipo de dispositivo (Responsive Mobile / Desktop).
   - Jerarquía visual y componentes (Cards, Inputs, Primary Buttons, Alerts).
   - Estilo funcional limpio, sin distracciones estéticas irrelevantes.
3. Extraer el identificador generado (`screenId`) y registrarlo con la URL canónica del proyecto.

### Acción B — Wireframing Estructural en ASCII
Dentro del bloque de código `text` de cada estado, representar con precisión la topología de la interfaz:

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
