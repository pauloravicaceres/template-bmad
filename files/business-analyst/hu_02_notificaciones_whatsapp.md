## 1. HISTORIA DE USUARIO

- **Épica:** Notificaciones Automáticas e Inmediatas vía WhatsApp
- **Título de la HU:** Envío Automático e Inmediato de Notificaciones por WhatsApp para Confirmación y Cancelación de Citas

> **Como** sistema del Spá Podológico  
> **Quiero** enviar notificaciones automáticas e inmediatas a través de WhatsApp al cliente y al podólogo ante la creación o cancelación de una reserva  
> **Para** garantizar la confirmación oportuna de la cita, reducir la tasa de inasistencia y mantener al equipo informado sin exponer información de precios.

## 2. ALCANCE ESPECÍFICO (SCOPE)

- **Incluye:**
  - Disparo automático de notificación de confirmación vía WhatsApp al cliente tras un agendamiento exitoso, incluyendo detalles de la cita (servicios seleccionados, podólogo asignado, fecha, hora).
  - Disparo automático de notificación de aviso vía WhatsApp al podólogo asignado tras una nueva reserva (datos del cliente, servicios, fecha, hora).
  - Disparo automático de notificación de cancelación vía WhatsApp al podólogo asignado cuando un cliente anula su cita.
  - Garantía de no inclusión de precios ni montos económicos en las plantillas o contenido de los mensajes de WhatsApp.
- **NO Incluye:**
  - Inclusión de precios o cobros en los mensajes enviados (restricción estricta de ocultación de precios).
  - Envío de notificaciones por otros canales como correo electrónico o SMS (el único canal autorizado en el MVP es WhatsApp).
  - Recordatorios automáticos periódicos previos a la cita (ej. avisos a las 24h o 2h antes).
  - Respuestas interactivas o chatbots automatizados dentro de WhatsApp.

## 3. REGLAS DE NEGOCIO

- **RN-01:** Las notificaciones por WhatsApp deben gatillarse de forma inmediata e incondicional tras el evento de confirmación o cancelación de reserva en el sistema.
- **RN-02:** Los mensajes enviados vía WhatsApp no deben contener bajo ninguna circunstancia información sobre precios, costos de servicios o tarifas.
- **RN-03:** El canal de notificación debe ser única y exclusivamente WhatsApp.
- **RN-04:** En la notificación de confirmación al cliente se deben detallar: nombre del cliente, servicios agendados, podólogo asignado, fecha y hora de la cita.
- **RN-05:** Si el envío de la notificación falla por problemas del proveedor técnico o número inválido, la reserva registrada en el sistema no debe revertirse, pero el evento de fallo debe quedar registrado en el log del sistema.

## 4. CRITERIOS DE ACEPTACIÓN (Gherkin BDD)

**Escenario 1: Envío exitoso de notificación de confirmación al cliente y podólogo (Happy Path)**
- **Dado** que se ha registrado y bloqueado exitosamente una nueva cita en el motor de reservas
- **Cuando** el sistema procesa el evento de confirmación de la cita
- **Entonces** el sistema envía de manera inmediata e incondicional una notificación por WhatsApp al cliente indicando el podólogo asignado, servicios, fecha y hora sin mostrar precios
- **Y** envía de manera inmediata una notificación por WhatsApp al podólogo asignado con el detalle del cliente y la reserva efectuada.

**Escenario 2: Envío exitoso de notificación de cancelación de cita al podólogo (Happy Path / Cancelación)**
- **Dado** que un cliente anula exitosamente una reserva previamente agendada
- **Cuando** el sistema procesa el evento de cancelación de la cita
- **Entonces** el sistema envía de forma automática e inmediata una notificación por WhatsApp al podólogo asignado informando la liberación del bloque horario y los datos de la cita anulada.

**Escenario 3: Fallo en el envío de notificación por WhatsApp debido a número inválido o error del proveedor (Sad Path / Error Técnico)**
- **Dado** que el cliente registra una reserva con un número telefónico que no posee WhatsApp activo o ocurre una falla temporal en la API de WhatsApp
- **Cuando** el sistema intenta enviar la notificación automática de confirmación
- **Entonces** el sistema detecta la falla del canal de comunicación y registra el evento de error en el log de notificaciones
- **Y** mantiene la reserva registrada en el sistema sin interrumpir la confirmación en la pantalla del usuario.

## 5. PUNTOS ABIERTOS / DEPENDENCIAS

- **Punto Abierto 1 (Proveedor e Integración de API WhatsApp):** En el PRD/MVP se marca como punto abierto la definición del proveedor técnico o API específica (ej. WhatsApp Business Cloud API, Twilio, Meta Direct API) y la gestión de plantillas de mensaje preaprobadas por Meta.
- **Punto Abierto 2 (Mecanismo de Fallback en Notificaciones):** No se especifica si ante fallas continuas de envío en WhatsApp debe existir algún canal secundario de reintento o si basta con el registro de errores en el log.
- **Dependencia:** Esta historia depende directamente del evento de confirmación generado por el Motor de Reservas (Épica P1, `hu_01_reserva_citas.md`).

## 6. ORDEN DE DELEGACIÓN PARA EL QA

@QA: La Historia de Usuario Envío Automático e Inmediato de Notificaciones por WhatsApp para Confirmación y Cancelación de Citas está lista en el archivo hu_02_notificaciones_whatsapp.md. Por favor, procede con la auditoría documental contra el Product Brief para asegurar que la historia cumple con los requerimientos originales.
