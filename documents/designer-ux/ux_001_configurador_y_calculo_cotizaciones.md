# ESPECIFICACIÓN DE DISEÑO UX: Configuración Interactiva y Cálculo de Cotizaciones

- **Historia de Usuario Fuente:** 001-HU_configurador_y_calculo_cotizaciones.md
- **Fecha de Diseño:** 2026-10-02
- **Diseñador UX:** Agente UX Senior BMAD

---

## 1. RESUMEN DE DISEÑO
- **Historia Base:** Configuración Interactiva y Cálculo de Cotizaciones (`001-HU_configurador_y_calculo_cotizaciones`).
- **Enfoque de Usabilidad:** Interfaz interactiva de dos paneles (Catálogo/Configurador y Resumen Transaccional) que calcula automáticamente los subtotales e importe total general en tiempo real tras la selección de servicios o ajuste de parámetros, proporcionando retroalimentación inmediata ante entradas inválidas o carritos vacíos.

---

## 2. MAPA DE ESTADOS VISUALES

### Estado 1: Configurador con Ítems Seleccionados y Cálculo en Tiempo Real (Happy Path)
- **Escenario Cubierto:** Escenario 01 — Cálculo automático de subtotales y total general (Happy Path)
- **Wireframe Estructural (ASCII):**
```text
+-----------------------------------------------------------------------------------+
|  [Logo] Generador de Cotizaciones Web                    [Usuario: Freelance Dev] |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  1. CONFIGURADOR DE SERVICIOS                          2. RESUMEN DE COTIZACIÓN   |
|  -----------------------------------                   -------------------------  |
|  +---------------------------------+                   +------------------------+ |
|  | [✓] Desarrollo Landing Page     |                   | ÍTEMS EN COTIZACIÓN:   | |
|  |     Tarifa base: $ 300.00         |                   | 1. Landing Page        | |
|  |     Cantidad: [ 1 ]             |                   |    1 x $300 = $300.00  | |
|  +---------------------------------+                   | 2. Módulo E-commerce   | |
|  | [✓] Módulo E-Commerce Standard  |                   |    2 x $500 = $1000.00 | |
|  |     Tarifa base: $ 500.00         |                   +------------------------+ |
|  |     Cantidad: [ 2 ]             |                   | SUBTOTAL:     $1,300.00| |
|  +---------------------------------+                   | DESCUENTO:        $0.00| |
|  | [ ] Integración Pasarela Pago   |                   | TOTAL GENERAL:$1,300.00| |
|  |     Tarifa base: $ 200.00         |                   +------------------------+ |
|  |     Cantidad: [ 0 ]             |                   | [ (✓) Generar PDF ]    | |
|  +---------------------------------+                   +------------------------+ |
+-----------------------------------------------------------------------------------+
```
- **Nota de Interfaz:** Cada selección de checkbox o cambio de input numérico en el panel de configuración actualiza reactivamente el panel de resumen en tiempo real sin recarga de página. El botón "Generar PDF" se encuentra activo.

---

### Estado 2: Validación de Cantidades Inválidas / Formulario Incompleto (Sad Path)
- **Escenario Cubierto:** Escenario 02 — Selección vacía de servicios o cantidades inválidas (Sad Path)
- **Wireframe Estructural (ASCII):**
```text
+-----------------------------------------------------------------------------------+
|  [Logo] Generador de Cotizaciones Web                    [Usuario: Freelance Dev] |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  1. CONFIGURADOR DE SERVICIOS                          2. RESUMEN DE COTIZACIÓN   |
|  -----------------------------------                   -------------------------  |
|  +---------------------------------+                   +------------------------+ |
|  | [✓] Desarrollo Landing Page     |                   | ÍTEMS EN COTIZACIÓN:   | |
|  |     Tarifa base: $ 300.00         |                   | ⚠️ Error en ítem 1     | |
|  |     Cantidad: [ -1 ] ⚠️        |                   +------------------------+ |
|  |     * Error: Cantidad debe > 0 *|                   | SUBTOTAL:         $0.00| |
|  +---------------------------------+                   | TOTAL GENERAL:    $0.00| |
|  | ! ALERTA: Corrija los errores en los campos antes de continuar.                | |
|  +--------------------------------------------------------------------------------+ |
|                                                        | [ (X) Generar PDF ]    | |
|                                                        |   (Deshabilitado)      | |
+-----------------------------------------------------------------------------------+
```
- **Nota de Interfaz:** Al ingresar una cantidad ≤ 0, el input resalta en estado de error (borde destacado y alerta), se muestra un mensaje explicativo al usuario y el botón de acción principal ("Generar PDF") queda deshabilitado para prevenir cálculos inconsistentes.

---

### Estado 3: Cotización Vacía / Eliminación de Todos los Ítems (Happy / Sad Path Edge Case)
- **Escenario Cubierto:** Escenario 03 — Modificación o eliminación de ítems / Deselección total
- **Wireframe Estructural (ASCII):**
```text
+-----------------------------------------------------------------------------------+
|  [Logo] Generador de Cotizaciones Web                    [Usuario: Freelance Dev] |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  1. CONFIGURADOR DE SERVICIOS                          2. RESUMEN DE COTIZACIÓN   |
|  -----------------------------------                   -------------------------  |
|  +---------------------------------+                   +------------------------+ |
|  | [ ] Desarrollo Landing Page     |                   | 🛒 No hay ítems en la  | |
|  |     Tarifa base: $ 300.00         |                   |    cotización activa.  | |
|  |     Cantidad: [ 0 ]             |                   |                        | |
|  +---------------------------------+                   | Seleccione al menos un | |
|  | [ ] Módulo E-Commerce Standard  |                   | servicio del catálogo. | |
|  |     Tarifa base: $ 500.00         |                   +------------------------+ |
|  |     Cantidad: [ 0 ]             |                   | SUBTOTAL:         $0.00| |
|  +---------------------------------+                   | TOTAL GENERAL:    $0.00| |
|  | [ (Trash) Limpiar Configuración ]|                   +------------------------+ |
|  +---------------------------------+                   | [ (X) Generar PDF ]    | |
+-----------------------------------------------------------------------------------+
```
- **Nota de Interfaz:** Al deseleccionar todos los ítems o pulsar "Limpiar Configuración", el sistema limpia el resumen, resetea los montos a 0.00, muestra el estado de vista vacía (Empty State) y deshabilita la acción de emisión.

---

## 3. DECISIONES DE DISEÑO Y PUNTOS PENDIENTES
- **Heurísticas Aplicadas:** Layout de dos columnas para facilitar la visualización simultánea de la selección y el resumen recalculado; validación reactiva campo por campo en el evento `onChange`; inhabilitación proactiva de la acción primaria ante inconsistencias.
- **Bloqueos de UX / Consultas para BA:** Ninguno. Se mantiene pendiente únicamente la definición formal tributaria (IGV/Retenciones), la cual se integrará como un modificador opcional en versiones posteriores sin alterar la estructura actual.

---

## 4. ORDEN DE DELEGACIÓN PARA EL TRACKER
@SA: El diseño visual de la HU 001-HU_configurador_y_calculo_cotizaciones ha sido completado exitosamente. Por favor, procede con la fase de arquitectura técnica y diseño detallado de solución (tech-design).
