# PRODUCT BRIEF: Ámely - Spá Podológico

## 1. PROBLEMA
Actualmente, Ámely - Spá Podológico enfrenta serios problemas operativos derivados de una gestión manual de citas. 

### Hechos (mencionados explícitamente en la idea):
- Solapamientos y cruces en las agendas de trabajo de los podólogos.
- Tiempos muertos ineficientes entre atenciones.
- Errores en la estimación de la duración total de la atención cuando los clientes seleccionan múltiples servicios.
- Pérdida constante de clientes debido a la ausencia de un canal de comunicación inmediato y automatizado.

### Inferencias:
- La falta de visibilidad en tiempo real de la agenda impide a los podólogos organizar de manera óptima su jornada diaria.
- La inexistencia de confirmaciones e notificaciones instantáneas genera incertidumbre en los clientes, aumentando la tasa de inasistencia o abandono.

---

## 2. USUARIOS

- **Clientes del Spá Podológico:** Personas que desean conocer los servicios del spá, agendar citas seleccionando uno o varios servicios y el profesional de su preferencia, y gestionar (cancelar) sus reservas desde cualquier dispositivo.
- **Profesionales Podólogos:** Especialistas del equipo del spá que requieren consultar sus atenciones diarias y semanales en una interfaz clara y recibir avisos inmediatos ante reservas o cancelaciones.

---

## 3. OBJETIVO (OUTCOME)

Profesionalizar la atención al cliente y eliminar los errores operativos derivados del agendamiento manual mediante un aplicativo web moderno, elegante, ligero y 100% responsivo. Con esta solución se busca:
- Automatizar la reserva de citas con cálculo dinámico de duración y bloqueo en tiempo real de agendas.
- Establecer un canal directo y automático de confirmación y aviso vía WhatsApp tanto para clientes como para profesionales.
- Facilitar la autogestión de citas para clientes y el seguimiento organizado del flujo de atenciones para los podólogos.

---

## 4. ALCANCE INICIAL

El Producto Mínimo Viable (MVP) comprenderá los siguientes bloques funcionales:

1. **Vitrina Digital e Identidad del Spá:**
   - Sección de presentación del equipo podológico (perfiles, especialidades y fotografías).
   - Catálogo interactivo de servicios con indicación del tiempo promedio estimado de atención para cada uno.

2. **Motor de Reservas Inteligente y Control de Disponibilidad:**
   - Selección de uno o múltiples servicios y elección del profesional podólogo preferido.
   - Cálculo automático y dinámico de la duración acumulada de la atención.
   - Reserva y bloqueo automático del bloque de tiempo exacto en la agenda del profesional.

3. **Notificaciones Inmediatas vía WhatsApp:**
   - Notificación automática por WhatsApp al cliente y al profesional confirmando la reserva con el detalle de servicios, fecha y hora.
   - Notificación automática por WhatsApp al profesional asignado cuando un cliente anula su cita.

4. **Panel de Gestión para Profesionales y Autogestión del Cliente:**
   - Dashboard para el podólogo con visualización diaria y semanal de atenciones programadas.
   - Módulo de autogestión para que el cliente pueda cancelar su reserva de forma directa.

5. **Diseño y Experiencia:**
   - Plataforma web 100% responsiva (smartphones, tablets, laptops y PCs).

---

## 5. RESTRICCIONES

- **Ocultación de Precios:** Por política estricta de negocio, los precios de los servicios NO deben mostrarse al público en la interfaz del sistema.
- **Canal de Notificación Obligatorio:** El envío de notificaciones automáticas debe realizarse exclusivamente a través de WhatsApp.
- **Diseño Responsivo:** La aplicación debe adaptarse sin fricciones a cualquier tipo de pantalla y dispositivo.

---

## 6. CRITERIOS DE ÉXITO

- Reducción al 0% de sobreposiciones o cruces de citas en las agendas de los podólogos.
- Eliminación total de errores en la estimación del tiempo total en citas multiservicio.
- 100% de notificaciones de confirmación y cancelación enviadas oportunamente por WhatsApp.
- Reducción de tiempos muertos entre atenciones.
- Experiencia de reserva y cancelación calificada como fluida e intuitiva por clientes y profesionales.

---

## 7. SUPUESTOS

- Los clientes prefieren un canal de reserva autoservicio vía web responsiva en lugar de realizar llamadas o enviar mensajes manuales.
- El equipo de podólogos adoptará activamente el dashboard web como su herramienta principal de consulta de agenda.
- Los tiempos promedio estimados por servicio son representativos de la duración real del procedimiento.
- Los clientes disponen de una cuenta de WhatsApp activa asociada al número de contacto provisto.

---

## 8. PREGUNTAS ABIERTAS

1. **Tiempos de anticipación y reglas de cancelación:** ¿Existe una política de límite de tiempo para agendar o cancelar citas (ejemplo: cancelar con mínimo 2 horas de anticipación)?
2. **Datos del cliente y verificación:** ¿Qué datos personales se solicitarán obligatoriamente al cliente al agendar (nombre, teléfono WhatsApp, correo, DNI) y cómo se verificará la autenticidad de la reserva?
3. **Gestión de horarios del Spá y podólogos:** ¿Cómo se configurarán los días laborables, turnos de trabajo, horarios de descanso o ausencias de cada podólogo en el sistema?
4. **Reprogramación de citas:** La idea menciona la cancelación directa por parte del cliente, ¿se contempla también la opción de reprogramar (cambiar fecha/hora) o esta funcionalidad queda excluida del MVP?
5. **Proveedor de notificaciones de WhatsApp:** ¿El spá cuenta con alguna cuenta oficial de WhatsApp Business API o preferencia sobre el mecanismo de integración?
