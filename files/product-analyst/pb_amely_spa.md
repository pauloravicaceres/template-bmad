# PRODUCT BRIEF: Ámely - Spá Podológico

## 1. PROBLEMA
**Hechos comprobables (mencionados en la idea):**
- Ineficiencias operativas y pérdida de tiempo causadas por agendamientos manuales de citas.
- Ocurrencia de cruces involuntarios en las agendas de los podólogos.
- Falta de confirmaciones inmediatas tras solicitar una cita.
- Existencia de ausencias de clientes (no-shows) y fricción general en la atención al cliente.

**Inferencias lógicas:**
- La gestión manual recarga administrativamente al personal o interrumpe la labor asistencial de los podólogos.
- La ausencia de confirmación o recordatorio instantáneo incrementa las inasistencias por olvido o falta de compromiso del cliente.
- La imposibilidad de consultar la disponibilidad en tiempo real genera insatisfacción en los clientes al intentar reservar horarios ya ocupados.

## 2. USUARIOS
- **Clientes Finales:** Usuarios que requieren tratamientos podológicos en el spá, que desean explorar la trayectoria del staff, consultar el catálogo de servicios, reservar citas de forma autónoma según disponibilidad real y gestionar o anular sus citas fácilmente desde cualquier dispositivo (PCs, laptops, tablets y smartphones).
- **Profesionales Podólogos:** Especialistas del equipo que necesitan consultar y administrar su agenda diaria en tiempo real, monitorear el estado de cada atención y recibir notificaciones instantáneas de nuevas reservas o cancelaciones.

## 3. OBJETIVO (OUTCOME)
- Centralizar y automatizar el proceso de reservas podológicas mediante una plataforma web responsiva, moderna, ligera y accesible.
- Optimizar la ocupación y el tiempo de atención de los podólogos, eliminando los cruces de agenda y la carga operativa del agendamiento manual.
- Profesionalizar y agilizar la comunicación con clientes y profesionales a través de un flujo automatizado de notificaciones instantáneas vía WhatsApp.

## 4. ALCANCE INICIAL (MVP)
1. **Vitrina Digital Institucional y Staff:** Presentación del perfil y trayectoria de los podólogos, junto con un catálogo detallado de servicios podológicos ofertados con su tiempo promedio de atención.
2. **Motor Inteligente de Reservas y Agenda Dinámica:** Selección multilista de uno o varios servicios, selección o asignación de podólogo, cálculo automático del tiempo total acumulado y validación de disponibilidad en tiempo real bloqueando el intervalo continuo necesario.
3. **Sistema Integrado de Notificaciones vía WhatsApp:** Envío de notificación/confirmación automática al cliente al concretar la reserva, y alertas instantáneas al podólogo ante una nueva reserva o la anulación de una cita.
4. **Panel de Gestión de Citas (Portal del Profesional):** Módulo privado para que el podólogo visualice su agenda diaria, consulte el historial de clientes y actualice el estado de las citas (confirmada, atendida, cancelada).
5. **Módulo de Gestión / Cancelación de Citas por el Cliente:** Opción para que el cliente solicite la anulación de su cita agendada, liberando inmediatamente el bloque de tiempo en la agenda del podólogo y disparando la notificación por WhatsApp.

## 5. RESTRICCIONES
- **Estrategia comercial de precios:** Los precios de los servicios NO deben ser visibles al cliente en ninguna sección de la plataforma.
- **Canal de notificaciones:** El envío de notificaciones y alertas automáticas debe realizarse de forma estricta vía WhatsApp.
- **Adaptabilidad multi-dispositivo:** La plataforma web debe ser completamente responsiva (adaptada para PCs, laptops, tablets y smartphones).
- **Restricciones metodológicas (BMAD):** Sin definición de arquitectura técnica, stack tecnológico, código ni requisitos funcionales exhaustivos en esta fase de definición inicial.

## 6. CRITERIOS DE ÉXITO
- **Reducción de cruces de agenda:** 0% de solapamientos involuntarios de citas en la agenda de los podólogos.
- **Adopción de reservas autónomas:** Incremento significativo en el porcentaje de citas agendadas directamente por clientes vía web vs. agendamiento manual.
- **Reducción de inasistencias (No-shows):** Disminución de la tasa de inasistencias gracias al envío inmediato de confirmaciones por WhatsApp.
- **Eficiencia en la notificación:** Emisión inmediata (< 1 minuto) de notificaciones por WhatsApp ante reservas y cancelaciones.

## 7. SUPUESTOS
- Los clientes cuentan con acceso a internet y dispositivos móviles o PCs para realizar el agendamiento autónomo en la plataforma.
- Los clientes y podólogos disponen de números y cuentas activas de WhatsApp para recibir notificaciones automáticas.
- Cada servicio podológico cuenta con una duración promedio estándar estimada que permite el cálculo exacto del bloque continuo de tiempo.
- Los podólogos mantendrán actualizado el estado de las citas (atendida, cancelada) ingresando regularmente a su panel privado.

## 8. PREGUNTAS ABIERTAS
1. **Autenticación e Identificación de Clientes:** ¿El cliente necesitará crear una cuenta con contraseña para agendar/cancelar, o el acceso/gestión de citas se realizará mediante validación de teléfono/correo o un enlace único enviado a su WhatsApp?
2. **Administración de Horarios de Atención de Podólogos:** ¿Cómo y dónde se definirán los horarios de trabajo regular, turnos, descansos y días libres de cada podólogo?
3. **Ventana Límite para Cancelaciones:** ¿Existe una restricción de tiempo mínimo previo a la cita (ej. X horas antes) para que el cliente pueda realizar la anulación en la plataforma?
4. **Política de Reagendamiento / Modificación:** ¿Se permitirá cambiar fecha u hora de una cita agendada directamente, o la gestión por parte del cliente requiere anular la cita actual y crear una nueva reserva?
5. **Criterio de Asignación por Defecto de Podólogo:** Cuando un cliente no selecciona un podólogo de preferencia, ¿cuál es la regla de negocio para asignar uno (ej. primer podólogo con horario disponible, asignación equitativa por rotación)?
6. **Módulo de Administración de Catálogo y Staff:** ¿Se requiere un rol de Administrador General del Spá para dar de alta/baja a podólogos o agregar/modificar servicios en el catálogo digital?
