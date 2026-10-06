---
description: 'Usar para estructurar la salida física del archivo ux_[ID]_[nombre_corto].md en la carpeta designer-ux. Define las secciones obligatorias y las plantillas de delegación en el tracker.'
applyTo: '**'
---

# Plantilla Determinista del Entregable UX

> Estructura canónica obligatoria para el archivo `ux_[ID]_[nombre_corto].md` en BMAD.

---

## Convención de Nombres de Archivo
```
ux_[ID]_[nombre_corto].md
```
- Se deriva directamente del nombre del archivo de la Historia de Usuario aprobada (ej. de `012-HU_motor_reservas.md` se genera obligatoriamente `ux_012_motor_reservas.md`: sin `HU_` y con guion bajo tras el correlativo).

---

## Estructura Canónica del Documento

```markdown
# ESPECIFICACIÓN DE DISEÑO UX: {{TITULO_HISTORIA_DE_USUARIO}}

- **Historia de Usuario Fuente:** {{NOMBRE_ARCHIVO_HU}}
- **Fecha de Diseño:** {{FECHA_ACTUAL}}
- **Diseñador UX:** Agente UX Senior BMAD

---

## 1. RESUMEN DE DISEÑO
- **Historia Base:** {{Título formal de la HU evaluada}}.
- **Enfoque de Usabilidad:** {{Resumen de 2 a 3 líneas explicando cómo la arquitectura de información y la disposición de componentes resuelven la necesidad del usuario sin fricción}}.

---

## 2. MAPA DE ESTADOS VISUALES

### Estado 1: {{Nombre del Estado - Happy Path}}
- **Escenario Cubierto:** {{Referencia exacta al Criterio de Aceptación, ej. CA-01}}
- **Wireframe Estructural (ASCII):**
\`\`\`text
{{Diagrama ASCII limpio representando la jerarquía de la pantalla}}
\`\`\`
- **Nota de Interfaz:** {{Instrucciones de comportamiento interactivo para el desarrollador frontend}}.

---

### Estado 2: {{Nombre del Estado - Sad Path / Error}}
- **Escenario Cubierto:** {{Referencia al Criterio de Aceptación de error, ej. CA-02 o CA-03}}
- **Wireframe Estructural (ASCII):**
\`\`\`text
{{Diagrama ASCII mostrando el modal, toast o mensaje de validación fallida}}
\`\`\`
- **Nota de Interfaz:** {{Comportamiento de bloqueo, deshabilitación o recuperación del error}}.

<!-- Repetir la estructura para cada CA definido en la Historia de Usuario -->

---

## 3. DECISIONES DE DISEÑO Y PUNTOS PENDIENTES
- **Heurísticas Aplicadas:** {{Decisiones de usabilidad tomadas de forma estándar sin alterar reglas de negocio}}.
- **Bloqueos de UX / Consultas para BA:** {{Preguntas críticas o inconsistencias encontradas en la HU, o 'Ninguno'}}.

---

## 4. ORDEN DE DELEGACIÓN PARA EL TRACKER
*(Instrucción de una sola línea plana que se anexa a tracker_bmad.md al terminar el diseño)*

**Regla de Handoff Autónomo:** 
Usa `read_file` para obtener el texto del tracker, añade un salto de línea, y luego usa `write_file` para pegar únicamente la orden de delegación sin destruir el historial.

**Imprime siempre exactamente esto (el traspaso es incondicional al `@SA:` y no depende de cuántas épicas o HU falten; elegir la siguiente historia es del PM):**
`@SA: El diseño visual de la HU [NNN-HU_nombre] ha concluido exitosamente en [Archivo]. Procede con el tech-design y arquitectura.`

```

[IMPORT_SKILL: skills/tracker-logger/SKILL.md]
