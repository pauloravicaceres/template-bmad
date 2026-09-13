# PRODUCT BRIEF: Ámely - Spá Podológico

## 1. PROBLEMA
- **Hechos (Comprobables según la idea original):**
  - Desorganización operativa actual en el proceso de agendamiento de citas.
  - Cruces de horarios en las agendas de los profesionales podólogos.
  - Falta de confirmación inmediata con el cliente al momento de agendar.
  - La gestión manual genera cuellos de botella y pérdidas de tiempo en la operación diaria del spá.
- **Inferencias:**
  - El proceso manual mediante canales no automatizados incrementa el margen de error humano y reduce la eficiencia administrativa.
  - La falta de confirmación inmediata e informativa puede incrementar el riesgo de inasistencias o agendamientos duplicados.

## 2. USUARIOS
- **Cliente:** Persona que requiere atención podológica; busca conocer al equipo profesional, explorar la oferta de servicios y agendar o anular sus citas de forma autónoma e inmediata desde cualquier dispositivo.
- **Profesional Podólogo:** Especialista en podología; requiere un panel de gestión sencillo para consultar su agenda personalizada, revisar sus atenciones programadas y realizar el seguimiento en tiempo real de su jornada laboral.
- **Dueño y Administrador del Spá:** Gestor del negocio que busca resolver la desorganización operativa, evitar el traslape de agendas y optimizar la atención a los clientes.

## 3. OBJETIVO (OUTCOME)
- Resolver la desorganización operativa y eliminar por completo los cruces de horarios en las agendas de los podólogos.
- Proveer una plataforma intuitiva que permita al cliente autogestionar (agendar y anular) sus citas en tiempo real.
- Garantizar la confirmación e información inmediata de reservas y liberaciones de agenda mediante notificaciones automáticas vía WhatsApp.
- Optimizar el tiempo operativo de los podólogos a través de una agenda digitalizada y centralizada.

## 4. ALCANCE INICIAL
El MVP abarca los siguientes módulos funcionales e interfaces:
- **Vitrina de Profesionales y Servicios:** Sección interactiva pública que presenta al equipo de podólogos y detalla los servicios disponibles con su tiempo promedio/duración de atención.
- **Motor de Reservas Inteligente y Validación de Disponibilidad:** Selección autónoma de uno o varios servicios y del podólogo preferido, cálculo automático del tiempo total estimado (suma de duraciones promedio) y bloqueo inmediato del bloque horario correspondiente para prevenir sobreposiciones.
- **Sistema de Notificaciones por WhatsApp:** Notificaciones automáticas informativas enviadas vía WhatsApp al cliente y al podólogo asignado tras confirmar una cita, así como aviso inmediato al podólogo ante la anulación de una reserva para liberar su disponibilidad.
- **Panel de Gestión de Citas para Profesionales:** Módulo privado donde cada podólogo visualiza su agenda diaria, consulta el historial y estado de sus atenciones y realiza el seguimiento de sus citas.
- **Plataforma Web Responsiva:** Experiencia optimizada para navegadores en PCs, laptops, tablets y smartphones.

## 5. RESTRICCIONES
- **Ocultamiento Estratégico de Precios:** Por estrategia comercial explícita, los precios de los servicios NO deben ser visibles al público en ninguna sección de la plataforma.
- **Cero Cruces de Agenda:** El motor de reservas debe garantizar la no sobreposición de citas para un mismo podólogo en el mismo rango horario.
- **Compatibilidad Multiplataforma:** La interfaz debe adaptarse de manera fluida a distintos tamaños de pantalla (móvil, tablet, laptop, PC).
- **Simplicidad para el Profesional:** El panel del podólogo debe ser intuitivo y sencillo para minimizar la carga operativa durante la atención de pacientes.

## 6. CRITERIOS DE ÉXITO
- **Reducción total de cruces de agenda:** 0 incidentes reportados por duplicidad o sobreposición de reservas en la agenda de un profesional.
- **Inmediatez en notificaciones:** Envío y entrega de notificaciones informativas por WhatsApp en un intervalo de tiempo inmediato tras la reserva o anulación.
- **Incremento de agendamiento autónomo:** Elevado porcentaje de citas agendadas y anuladas directamente por los clientes a través de la web sin intervención manual del personal.
- **Optimización de tiempos operativos:** Eliminación de cuellos de botella administrativos asociados a la coordinación manual de turnos.

## 7. SUPUESTOS
- Los clientes cuentan con dispositivos con acceso a internet y una cuenta activa de WhatsApp para recibir las notificaciones.
- Los profesionales podólogos disponen de conexión a internet y dispositivos en el spá para consultar su panel en tiempo real.
- La suma directa de los tiempos promedio de cada servicio seleccionado refleja adecuadamente la duración total requerida para citas multiservicio.
- La omisión de precios en la vitrina pública no afectará negativamente la tasa de conversión en la reserva de citas.

## 8. PREGUNTAS ABIERTAS
1. **Datos requeridos para la reserva:** Información no proporcionada. ¿Qué datos personales mínimos (ej. nombre completo, número de teléfono WhatsApp, correo electrónico) se solicitarán al cliente para validar y confirmar la cita?
2. **Políticas de cancelación autónoma:** Información no proporcionada. ¿Existe un límite de tiempo previo (ej. máximo 2 horas antes de la cita) para permitir que el cliente anule su reserva autónomamente?
3. **Definición de turnos y disponibilidad laboral:** Información no proporcionada. ¿Cómo se configurarán los horarios de atención, días laborables, descansos y ausencias de cada podólogo en el sistema?
4. **Modificación / Reagendamiento de Citas:** Información no proporcionada. ¿El cliente podrá modificar la fecha, hora o especialista de una cita agendada, o la plataforma exigirá anular la cita existente y crear una nueva?
5. **Infraestructura de WhatsApp:** Información no proporcionada. ¿Se utilizará la API Oficial de WhatsApp Business para la automatización de los mensajes informativos?
6. **Gestión Administrativa y Roles:** Información no proporcionada. ¿Se requiere un módulo o rol de Administrador General para gestionar el alta/baja de podólogos, modificar duraciones de servicios y supervisar todas las agendas?
