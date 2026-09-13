# PRODUCT BRIEF: Ámely - Spá Podológico

## 1. PROBLEMA

### Hechos Comprobables
- Ineficiencias en la reserva de citas y gestión de agendas de los profesionales podólogos.
- Ocurrencia de cruce de horarios en las atenciones.
- Proceso de agendamiento manual y lento.
- Falta de confirmación inmediata de citas con los clientes.

### Inferencias Lógicas
- La falta de confirmación inmediata y los cruces de horario provocan insatisfacción o pérdida de clientes.
- La gestión manual genera sobrecarga operativa y desperdicio de tiempo laboral para los podólogos y la administración.

## 2. USUARIOS

1. **Clientes:**
   - Personas que buscan información sobre los profesionales y el catálogo de servicios podológicos del spa.
   - Usuarios que realizan reservas de citas seleccionando servicios y profesionales según disponibilidad.
   - Personas que reciben confirmaciones automáticas de sus reservas.
   - Usuarios que necesitan anular sus citas agendadas en caso de requerirlo.

2. **Profesionales Podólogos:**
   - Especialistas del spa que necesitan consultar su agenda individual diaria en un panel de gestión.
   - Profesionales que requieren hacer seguimiento a sus atenciones diarias y recibir notificaciones instantáneas de reservas o anulaciones.

3. **Administración del Spa:**
   - Encargados de gestionar y mantener actualizada la oferta de servicios podológicos y la asignación de profesionales en la plataforma.

## 3. OBJETIVO (OUTCOME)

- Centralizar el flujo de reservas y optimizar la experiencia del usuario (clientes y profesionales).
- Eliminar el cruce de horarios y automatizar la confirmación/anulación de citas.
- Optimizar la gestión de agendas de los profesionales podólogos mediante un panel organizado y notificaciones en tiempo real.

## 4. ALCANCE INICIAL (MVP)

El MVP estará compuesto por cuatro bloques funcionales principales:

1. **Módulo de Vitrina Digital y Equipo:**
   - Presentación visual elegante e interfaz amigable del spa e instalaciones.
   - Perfiles de los profesionales podólogos que laboran en el spa.
   - Catálogo de servicios podológicos ofertados, especificando detalladamente la duración o tiempo promedio de atención de cada servicio (precios ocultos al cliente en la vista pública).

2. **Motor Inteligente de Reservas y Gestión de Disponibilidad:**
   - Selección de uno o múltiples servicios podológicos y del profesional de preferencia por parte del cliente.
   - Cálculo automático acumulativo del tiempo total estimado de atención (suma de duraciones de servicios seleccionados).
   - Validación en tiempo real de la disponibilidad del profesional elegido, bloqueando en su agenda el bloque horario completo correspondiente a la suma calculada para evitar cruces.

3. **Sistema de Notificaciones Automatizadas por WhatsApp:**
   - Generación y envío de notificación automática vía WhatsApp al cliente al concretar exitosamente su reserva.
   - Envío de notificación automática vía WhatsApp al profesional asignado notificándole los detalles de la nueva cita.
   - Notificación automática al WhatsApp del profesional ante cualquier anulación realizada por el cliente.

4. **Gestión de Citas y Cancelaciones:**
   - Panel de gestión de citas para los profesionales, permitiéndoles revisar el cronograma de sus atenciones, estado de citas y seguimiento diario.
   - Funcionalidad de anulación de cita accesible para el cliente mediante código o enlace de reserva, liberando automáticamente el tiempo agendado en el calendario del profesional.

## 5. RESTRICCIONES

- **Visibilidad de Precios:** Los precios de los servicios podológicos deben mantenerse ocultos al cliente en la vista pública.
- **Interfaz y Adaptabilidad:** La solución debe ser una aplicación web moderna, elegante, ligera y completamente responsiva (adaptable a PCs, laptops, tablets y smartphones).
- **Notificaciones:** El canal obligatorio de notificación automatizada es WhatsApp.
- **Mecanismo de Anulación:** La anulación por parte del cliente debe ser accesible mediante código o enlace de reserva.

## 6. CRITERIOS DE ÉXITO

- **Eliminación de cruces de horarios:** 0% de solapamientos de citas agendadas por profesional gracias al cálculo del tiempo acumulado y bloqueo en tiempo real.
- **Efectividad en notificaciones:** 100% de envío exitoso e instantáneo de notificaciones por WhatsApp ante eventos de reserva y anulación.
- **Liberación inmediata de agenda:** Desbloqueo automático e inmediato del bloque de tiempo en la agenda del profesional al realizarse una anulación por el cliente.
- **Usabilidad del panel:** Adopción por parte de los profesionales para la revisión diaria de su agenda y seguimiento de atenciones.

## 7. SUPUESTOS

- Los clientes cuentan con un número telefónico activo con WhatsApp para recibir notificaciones automáticas.
- Tanto clientes como profesionales tienen acceso a dispositivos con navegador web e internet para interactuar con la plataforma.
- La estimación de duración asignada a cada servicio en el catálogo es precisa y refleja la duración real de la atención podológica.
- Los clientes utilizarán responsablemente la opción de anulación mediante código/enlace sin necesidad de autenticación compleja.

## 8. PREGUNTAS ABIERTAS

1. **Gestión de Horarios y Turnos:** ¿Cómo se definen y gestionan los horarios de atención y turnos laborales (días festivos, descansos, pausas) de los profesionales podólogos en el spa?
2. **Políticas y Tiempos Límite de Cancelación:** ¿Existe un margen mínimo de tiempo antes de la cita (ej. 2 horas antes) para permitir la anulación por parte del cliente?
3. **Detalles de Integración de WhatsApp:** ¿Se empleará la API oficial de WhatsApp Business o algún proveedor de mensajería API en particular? ¿Cuál será la plantilla exacta del mensaje?
4. **Administración y Configuración del Spa:** ¿Qué funcionalidades exactas requerirá el módulo administrativo en el MVP para la alta/baja/modificación de profesionales y servicios?
5. **Capacidad Operativa e Infraestructura del Spa:** ¿Existen limitaciones de infraestructura (ej. cantidad de sillones podológicos o salas disponibles simultáneamente) que deban considerarse más allá de la disponibilidad del profesional?
6. **Captura de Datos del Cliente:** ¿Qué información obligatoria del cliente se debe solicitar en el formulario de reserva (ej. nombre, apellidos, teléfono, correo electrónico, notas médicas/observaciones)?
