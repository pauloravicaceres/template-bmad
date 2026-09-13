# 1. HISTORIA DE USUARIO

- **Épica:** Notificaciones Automáticas por WhatsApp
- **Título de la HU:** Envío automático de notificaciones de confirmación y anulación de cita vía WhatsApp

> **Como** Cliente y Especialista Podólogo de Ámely Spá  
> **Quiero** recibir un mensaje automático por WhatsApp al confirmarse o anularse una reserva de cita  
> **Para** disponer de la información actualizada del agendamiento de forma inmediata en mi dispositivo móvil  

## 2. ALCANCE ESPECÍFICO (SCOPE)

- **Incluye:**
  - Emisión automática de notificación por WhatsApp al cliente tras confirmar exitosamente una reserva de cita.
  - Emisión automática de notificación por WhatsApp al especialista podólogo tras confirmarse una nueva cita en su agenda.
  - Emisión automática de notificación por WhatsApp al especialista podólogo cuando un cliente anula una cita programada.
  - Inclusión de los detalles básicos del agendamiento en el cuerpo del mensaje (fecha, hora, especialista y servicios solicitados).
- **NO Incluye:**
  - Envío de notificaciones por otros canales (correo electrónico, SMS, notificaciones push).
  - Respuestas interactivas o atención por chatbot/bot de conversación a través de WhatsApp.
  - Envío de recordatorios periódicos previos a la cita (ej. 24 horas antes).

## 3. REGLAS DE NEGOCIO

- **RN-01:** La notificación de confirmación debe enviarse de forma inmediata tras el evento de reserva exitosa en el motor de agendamiento.
- **RN-02:** La notificación de anulación dirigida al especialista debe enviarse inmediatamente después de que la cita sea cancelada en el sistema.
- **RN-03:** Los mensajes enviados no deben contener montos ni información de precios de los servicios reteniendo la restricción de ocultamiento de precios del spá.

## 4. CRITERIOS DE ACEPTACIÓN (Gherkin BDD)

**Escenario 1: Envío de notificación por WhatsApp tras confirmación de cita (Happy Path)**
- **Dado** que se ha completado con éxito la reserva de una cita en el motor de agendamiento
- **Cuando** el sistema procesa la confirmación del agendamiento
- **Entonces** el sistema envía de forma automática e inmediata un mensaje de WhatsApp al cliente con el detalle de su cita (fecha, hora, servicios y especialista)
- **Y** envía de forma simultánea un mensaje de WhatsApp al especialista asignado notificándole la nueva atención agendada.

**Escenario 2: Envío de notificación por WhatsApp tras anulación de cita por parte del cliente (Flujo de Anulación)**
- **Dado** que una cita previamente agendada es anulada por el cliente
- **Cuando** el sistema procesa la anulación de la cita
- **Entonces** el sistema envía de forma automática e inmediata un mensaje de WhatsApp al especialista podólogo informándole sobre la liberación del bloque horario previamente reservado.

**Escenario 3: Fallo en la entrega de la notificación por proveedor/red (Sad Path)**
- **Dado** que ocurre un agendamiento o anulación de cita exitoso en el sistema
- **Cuando** el servicio de notificaciones de WhatsApp detecta un error o imposibilidad de envío por parte del proveedor externo
- **Entonces** el sistema registra el fallo del intento de envío sin revertir ni afectar el estado reservado o anulado de la cita en el motor de agendamiento.

## 5. PUNTOS ABIERTOS / DEPENDENCIAS

- **Proveedor de API de WhatsApp:** No se especifica en el PRD la herramienta o proveedor externo de mensajería (ej. Meta Business API, Twilio, etc.) a utilizar para el envío automático de notificaciones.
- **Plantilla visual y copia de los mensajes:** Las plantillas exactas de texto y formato de los mensajes de WhatsApp no están definidas formalmente.

## 6. ORDEN DE DELEGACIÓN PARA EL QA

@QA: La Historia de Usuario Envío automático de notificaciones de confirmación y anulación de cita vía WhatsApp está lista en el archivo hu_03_notificaciones.md. Por favor, procede con la auditoría documental contra el Product Brief para asegurar que la historia cumple con los requerimientos originales.
