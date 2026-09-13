Soy el dueño de Ámely - Spá Podológico. Actualmente enfrentamos ineficiencias en la reserva de citas y gestión de agendas de nuestros profesionales podólogos, lo que genera cruce de horarios, agendamientos manuales lentos y falta de confirmación inmediata con nuestros clientes. Necesitamos una solución web moderna, elegante, ligera y completamente responsiva (adaptable a PCs, laptops, tablets y smartphones) que centralice el flujo de reservas y optimice la experiencia del usuario.

El sistema debe atender a tres actores principales:
1. Clientes: Quienes buscan informarse sobre nuestros profesionales y catálogo de servicios podológicos, agendar citas según su preferencia y disponibilidad real, recibir confirmaciones automáticas y poder anular citas si lo requieren.
2. Profesionales Podólogos: Quienes necesitan visualizar su agenda individual organizada en un panel de gestión para hacer seguimiento a sus atenciones diarias y recibir notificaciones instantáneas de nuevas reservas o cancelaciones.
3. Administración del Spa: Encargados de mantener actualizada la oferta del spa y la asignación de profesionales.

Para la primera versión (MVP), organizamos el aplicativo en los siguientes bloques funcionales:

- Módulo de Vitrina Digital y Equipo:
  * Presentación visual elegante del spa, sus instalaciones e interfaz amigable.
  * Perfiles de los profesionales podólogos que laboran en el spa.
  * Catálogo de servicios podológicos ofertados, especificando detalladamente la duración o tiempo promedio de atención de cada servicio (los precios de los servicios se mantendrán ocultos al cliente en la vista pública).

- Motor Inteligente de Reservas y Gestión de Disponibilidad:
  * Permite al cliente seleccionar uno o múltiples servicios podológicos y elegir su profesional de preferencia.
  * Cálculo automático acumulativo del tiempo total estimado de atención basado en la suma de duraciones de los servicios seleccionados.
  * Validación en tiempo real de la disponibilidad del profesional elegido, bloqueando en su agenda el bloque horario completo correspondiente a la suma calculada para evitar cruces con otros clientes.

- Sistema de Notificaciones Automatizadas por WhatsApp:
  * Generación y envío de notificación automática vía WhatsApp al cliente al concretar exitosamente su reserva.
  * Envío de notificación automática vía WhatsApp al profesional asignado notificándole los detalles de la nueva cita.
  * Notificación automática al WhatsApp del profesional ante cualquier anulación realizada por el cliente.

- Gestión de Citas y Cancelaciones:
  * Panel de gestión de citas con acceso para los profesionales, permitiéndoles revisar el cronograma de sus atenciones, estado de citas y seguimiento diario.
  * Funcionalidad de anulación de cita accesible para el cliente (mediante código/enlace de reserva), que libera automáticamente el tiempo agendado en el calendario del profesional.
