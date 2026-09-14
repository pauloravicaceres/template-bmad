## 1. RESUMEN DE DISEÑO

- **Historia Base:** Reserva e Integración de Citas Podológicas en Tiempo Real
- **Enfoque de Usabilidad:** Se implementó una interfaz limpia de flujo continuo en tres componentes principales: selección multivariable de tratamientos podológicos con cálculo dinámico de duración acumulada, selección de podólogo especializado y un selector de bloques horarios inteligentes en tiempo real que previene cruces y respeta estrictamente la regla inquebrantable de 0 precios visibles.

## 2. MAPA DE ESTADOS VISUALES

### Estado 1: Selección de Servicios, Profesional y Disponibilidad (Happy Path)

**Escenario cubierto:** Escenario 1: Reserva exitosa de cita con profesional y múltiples servicios (Happy Path)

- **ID de Pantalla en Stitch:** `projects/13539032631391197448/screens/38474b96f8cc4f9c83b847767108cbc8`
- **Proyecto Stitch:** `projects/13539032631391197448` (Motor de Reservas Spa Amely)

**Nota de Interfaz:** El botón principal 'Confirmar Reserva' se mantiene deshabilitado dinámicamente hasta que el cliente seleccione al menos un servicio podológico y un bloque horario continuo suficiente para cubrir la duración total acumulada (ej: 45 min + 30 min = 75 min). Todas las tarjetas de servicio y resúmenes omiten absolutamente símbolos de moneda ($) o montos monetarios.

### Estado 2: Detección de Solapamiento y Alerta de Cruce (Sad Path)

**Escenario cubierto:** Escenario 2: Intento de reserva en un horario con cruce o solapamiento (Sad Path)

- **ID de Pantalla en Stitch:** `projects/13539032631391197448/screens/a06641df8a6a48329ec5980dae2e8179`
- **Proyecto Stitch:** `projects/13539032631391197448` (Motor de Reservas Spa Amely)

**Nota de Interfaz:** Cuando la agenda detecta un solapamiento en tiempo real con una cita previamente reservada para el mismo profesional (ej: Dra. Elena Ramos de 10:00 a 11:00 hrs), el sistema deshabilita la franja conflictiva e invoca un modal accesible con backdrop-blur. El modal explica el motivo del bloqueo (incluyendo buffer de ventilación/esterilización) y propone dos botones de selección directa con bloques continuos alternativos disponibles sin solapamientos (ej: 11:15 - 12:30 hrs o 15:15 - 16:30 hrs).

### Estado 3: Verificación de Restricción Inquebrantable (No Precios)

**Escenario cubierto:** Escenario 3: Verificación de Restricción Inquebrantable de No Precios

- **ID de Pantalla en Stitch:** `projects/13539032631391197448/screens/38474b96f8cc4f9c83b847767108cbc8`

**Nota de Interfaz:** Tanto en el panel dinámico de resumen (Sticky Card) como en la confirmación de la cita, únicamente se detallan los nombres de los tratamientos podológicos seleccionados, la duración calculada en minutos/horas, el profesional y gabinete asignado, y las instrucciones de higiene/llegada. Queda prohibida la inclusión de subtotales, precios unitarios, impuestos o totales monetarios.

## 3. DECISIONES DE DISEÑO Y PUNTOS PENDIENTES

- **Heurísticas aplicadas:**
  - *Visibilidad del estado del sistema (Heurística 1):* Indicación visual en tiempo real del tiempo total acumulado en minutos (ej: "Duración Total: 75 min") para dar certidumbre al usuario sobre la duración necesaria.
  - *Prevención de errores (Heurística 5):* Ocultamiento/deshabilitado de franjas horarias con cruces y sugerencia proactiva de bloques continuos contiguos libres.
  - *Consistencia y estándares (Heurística 4):* Sistema de diseño *Serene Podiatric Sanctuary* basado en tonos verde salvia (`#3E6B5C`), crema warm linen (`#FAF8F5`) y tipografía Newsreader/Manrope para transmitir pulcritud médica sin la frialdad hospitalaria.
- **Bloqueos o Consultas:**
  - *Consulta para el BA / Stakeholder:* Se mantiene la observación sobre el mecanismo definitivo de identificación del cliente (teléfono / DNI / correo) al momento de enviar las notificaciones automáticas por WhatsApp (Épica P2).

# 4. ORDEN DE DELEGACIÓN PARA EL TRACKER

@PM: Los wireframes para la HU Reserva e Integración de Citas Podológicas en Tiempo Real están listos en D:\Paulo\Cursos\DMC\template-bmad\files\designer-ux\ux_01_motor_reservas.md. Por favor, lee el historial, identifica la siguiente Épica pendiente en el backlog y asígnala al BA.
