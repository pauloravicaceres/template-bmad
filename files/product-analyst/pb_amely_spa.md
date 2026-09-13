# PRODUCT BRIEF: Ámely - Spá Podológico

## 1. PROBLEMA

### Hechos (Mencionados explícitamente)
- Existen ineficiencias operativas en la programación manual de atenciones en el spa.
- Se presentan cruces eventuales de horarios (solapamientos) en las agendas de los podólogos.
- Se registran pérdidas de tiempo en el seguimiento manual de las citas.

### Inferencias (Deducciones lógicas)
- El proceso manual actual genera fricción e insatisfacción tanto en los clientes como en el equipo podológico por retrasos o cancelaciones imprevistas.
- La ausencia de un sistema centralizado en tiempo real impide tener visibilidad clara sobre la disponibilidad real del personal.

---

## 2. USUARIOS

- **Clientes:** Personas que requieren servicios podológicos. Accederán a la plataforma web/móvil para explorar servicios y personal, agendar citas seleccionando profesional de su preferencia, y anular reservas si es necesario.
- **Podólogos / Profesionales:** Personal especializado del spa. Utilizarán el portal profesional para visualizar su agenda asignada y actualizar/dar seguimiento al estado de las atenciones.
- **Administrador / Propietario del Spa:** *(Implícito/Inferencia)* Supervisará la operación del spa, aunque su rol funcional no está detallado en la propuesta inicial.

---

## 3. OBJETIVO (OUTCOME)

- Eliminar completamente los cruces de agenda mediante una validación automática y en tiempo real de la disponibilidad de los podólogos.
- Optimizar la experiencia del usuario cliente mediante una interfaz digital moderna, fluida, ligera y con enfoque mobile-first.
- Reducir los tiempos de gestión operativa manual a través de notificaciones automáticas y agendas digitalizadas.
- Elevar el nivel de profesionalismo en la atención y comunicación con los clientes del spa.

---

## 4. ALCANCE INICIAL

El Producto Mínimo Viable (MVP) contempla los siguientes componentes:

1. **Vitrina Digital de Personal y Servicios:**
   - Catálogo visual de profesionales de la salud podológica.
   - Detalle de servicios ofrecidos indicando únicamente su tiempo promedio de atención.

2. **Motor de Reservas y Agenda Inteligente:**
   - Selección flexible de uno o más servicios y elección del podólogo de preferencia.
   - Cálculo automático de la duración total requerida (suma continua de tiempos).
   - Bloqueo de horario continuo en la agenda del profesional con validación en tiempo real para evitar solapamientos.

3. **Gestión de Anulación de Reservas por Clientes:**
   - Opción para que el cliente anule su reserva previamente realizada desde la interfaz web.

4. **Sistema de Notificaciones vía WhatsApp:**
   - Notificación automática al cliente y al podólogo al confirmarse una reserva.
   - Notificación inmediata al podólogo cuando un cliente anula una reserva.

5. **Panel de Gestión de Atenciones (Portal Profesional):**
   - Interfaz simplificada dedicada para que cada podólogo revise y gestione sus citas agendadas.

6. **Diseño Mobile-First y Responsivo:**
   - Interfaz optimizada para teléfonos móviles, tablets, laptops y PCs.

---

## 5. RESTRICCIONES

- **Ocultamiento de Precios al Público:** Por decisión estratégica de negocio, los servicios expuestos en la interfaz pública DEBEN mostrar únicamente el tiempo promedio de atención, omitiendo de forma explícita cualquier información sobre precios.
- **Diseño Mobile-First y Responsivo:** La interfaz debe ser moderna, elegante y extremadamente ligera, garantizando usabilidad sin fallas en dispositivos móviles y de escritorio.
- **Validación Estricta de Disponibilidad:** No se debe permitir la superposición de citas para un mismo podólogo en ningún horario.
- **Canal Obligatorio de Notificaciones:** Las notificaciones automáticas del sistema deben integrarse de forma exclusiva y directa con WhatsApp.

---

## 6. CRITERIOS DE ÉXITO

- **Cero (0%) Cruces de Horario:** Eliminación total de eventos de sobreposición en la agenda de todos los podólogos.
- **Disminución del Tiempo Operativo Manual:** Reducción sustancial del tiempo dedicado por el personal a coordinar y confirmar citas telefónica o manualmente.
- **Tasa de Adopción de Reservas Digitales:** Porcentaje significativo de reservas gestionadas directamente por los clientes a través del canal digital.
- **Tasa de Entrega de Notificaciones:** Entrega efectiva e inmediata de notificaciones de confirmación y anulación por WhatsApp.

---

## 7. SUPUESTOS

- Se asume que los clientes cuentan con acceso a la aplicación de WhatsApp y a un número de teléfono activo para la recepción de confirmaciones y alertas.
- Se asume que los podólogos contarán con un dispositivo (móvil, tablet o PC) con conexión a internet en el spa para consultar su panel en tiempo real.
- Se asume que la suma simple de duraciones promedio de los servicios seleccionados es suficiente para estimar con precisión el tiempo total de la cita continua.
- Se asume que existe un horario laboral estándar predefinido por profesional dentro del cual el motor de reservas puede buscar disponibilidad.

---

## 8. PREGUNTAS ABIERTAS

1. **Gestión de Administración y Configuración:** *Información no proporcionada.* ¿Cómo y quién registrará o editará la lista de podólogos, los servicios, sus duraciones promedio y los horarios laborales de los profesionales? ¿Se requiere incluir un módulo de Administración en este alcance inicial?
2. **Identificación / Autenticación de Clientes:** *Información no proporcionada.* ¿El cliente requiere crear una cuenta con contraseña para reservar o anular, o se identificará únicamente mediante datos básicos de contacto (ej. nombre, teléfono, DNI)?
3. **Políticas y Tiempos Limite de Cancelación:** *Información no proporcionada.* ¿Existe algún límite de tiempo previo (ej. máximo 2 horas antes de la cita) para permitir que un cliente anule su reserva desde la web?
4. **Manejo de Tiempos de Limpieza/Desinfección o Pausas:** *Información no proporcionada.* ¿Se debe contemplar un margen de tiempo adicional entre citas continuas para desinfección de herramientas o descanso del podólogo?
5. **Proveedor de Servicio de WhatsApp:** *Información no proporcionada.* ¿El spa cuenta actualmente con un proveedor de API de WhatsApp Business (ej. Twilio, Meta API, etc.) o se requiere recomendar una solución tecnológica para la mensajería automática?
