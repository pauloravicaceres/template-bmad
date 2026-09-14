## 1. RESUMEN DE DISEÑO

- **Historia Base:** Anulación Autónoma de Citas Previas por el Cliente (`hu_04_anulacion_citas.md`)
- **Enfoque de Usabilidad:** Se diseñó un módulo de autogestión de turnos que permite consultar citas activas mediante código o teléfono celular, visualizar los detalles de la atención podológica y solicitar la anulación a través de un modal de confirmación explícita. El flujo garantiza la liberación instantánea del bloque horario en la agenda del especialista y previene cancelaciones accidentales sin exhibir datos monetarios.

## 2. MAPA DE ESTADOS VISUALES

### Estado 1: Consulta y Confirmación Explícita de Anulación de Cita (Happy Path)

**Escenario cubierto:** Escenario 1: Anulación exitosa de cita por parte del cliente (Happy Path)

- **ID de Pantalla en Stitch:** `projects/13539032631391197448/screens/d313fd1d80634c30bb6e0531a57c4957`
- **Proyecto Stitch:** `projects/13539032631391197448` (Motor de Reservas Spa Amely)

**Nota de Interfaz:** Tras localizar la cita activa (#AMP-2847), la tarjeta presenta el resumen de tratamientos (75 min total), podóloga asignada (Dra. Elena Ramos) y horario (15:15 - 16:30 hrs). Al hacer clic en `Anular esta Cita`, el sistema abre un modal de verificación con dos botones (`Sí, Confirmar Anulación` y `No, Conservar mi Cita`). La confirmación gatilla la liberación inmediata del bloque de tiempo en la agenda y la notificación vía WhatsApp al profesional.

### Estado 2: Consulta de Cita Inexistente o Ya Anulada (Sad Path)

**Escenario cubierto:** Escenario 2: Intento de consulta de cita inexistente o ya anulada (Sad Path)

- **ID de Pantalla en Stitch:** `projects/13539032631391197448/screens/d313fd1d80634c30bb6e0531a57c4957`
- **Proyecto Stitch:** `projects/13539032631391197448` (Motor de Reservas Spa Amely)

**Nota de Interfaz:** Si el cliente ingresa un código de reserva erróneo o de una cita previamente cancelada, el buscador despliega un banner informativo de aviso (`No se encontraron citas activas asociadas a este identificador`) inhabilitando las acciones de cancelación y sugiriendo la opción de `Agendar Nueva Cita` o `Verificar Código`.

### Estado 3: Verificación de Restricción Inquebrantable (No Precios)

**Escenario cubierto:** Escenario 3: Verificación de Prohibición de Precios en el Módulo de Anulación

- **ID de Pantalla en Stitch:** `projects/13539032631391197448/screens/d313fd1d80634c30bb6e0531a57c4957`

**Nota de Interfaz:** Se realiza la auditoría visual en el buscador, ficha de cita activa y modal de confirmación, asegurando la omisión total de divisas ($), importes monetarios o costos de cancelación.

## 3. DECISIONES DE DISEÑO Y PUNTOS PENDIENTES

- **Heurísticas aplicadas:**
  - *Prevención de errores (Heurística 5):* Modal de confirmación en dos pasos para impedir anulaciones accidentales por toques inadvertidos.
  - *Visibilidad del Estado del Sistema (Heurística 1):* Mensaje explícito del impacto de la anulación ("Su turno de 75 min quedará liberado de inmediato para la comunidad de pacientes").
  - *Consistencia y Estándares (Heurística 4):* Adaptación estética del lenguaje *Serene Podiatric Sanctuary* con botones de advertencia en tono terracota desaturado para acciones destructivas.
- **Bloqueos o Consultas:**
  - *Consulta para el BA / Product Owner:* Se asume provisionalmente la búsqueda por código único de reserva (#AMP-XXXX) o número celular como mecanismo de autenticación del cliente (Punto Abierto 1 de la HU).

# 4. ORDEN DE DELEGACIÓN PARA EL TRACKER

@PM: Los wireframes para la HU Anulación Autónoma de Citas Previas por el Cliente están listos en D:\Paulo\Cursos\DMC\template-bmad\files\designer-ux\ux_04_anulacion_citas.md. Por favor, lee el historial, identifica la siguiente Épica pendiente en el backlog y asígnala al BA.
