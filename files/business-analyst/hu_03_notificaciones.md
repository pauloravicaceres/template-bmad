## 1. HISTORIA DE USUARIO

- **Épica:** Notificaciones Automáticas por WhatsApp
- **Título de la HU:** Envío automático de notificaciones de confirmación y anulación de cita vía WhatsApp

> **Como** Cliente y Podólogo del Spa Podológico
> **Quiero** recibir mensajes automáticos e inmediatos a través de WhatsApp al confirmarse o anularse una reserva
> **Para** mantener una comunicación fluida, transparente y reducir los tiempos de gestión operativa manual de citas

## 2. ALCANCE ESPECÍFICO (SCOPE)

- **Incluye:**
  - Envío automático de mensaje de confirmación por WhatsApp al cliente al registrarse exitosamente una reserva (incluyendo detalles de servicio, podólogo, fecha y hora).
  - Envío automático de notificación por WhatsApp al podólogo asignado al confirmarse una nueva reserva en su agenda.
  - Envío automático de notificación inmediata por WhatsApp al podólogo asignado cuando un cliente anula una reserva existente.
  - Integración exclusiva con el canal de mensajería de WhatsApp.

- **NO Incluye:**
  - Envío de notificaciones por otros canales como SMS, correo electrónico o notificaciones push.
  - Envío de recordatorios previos a la cita (ej. 24 horas o 2 horas antes), dado que no están especificados en el alcance inicial del MVP.
  - Selección de proveedor específico de API de WhatsApp Business (definición declarada como punto abierto a nivel de infraestructura/arquitectura).
  - Interacción bidireccional por bot en el chat de WhatsApp (la notificación actúa como mensaje saliente de estado).

## 3. REGLAS DE NEGOCIO

- **RN-01:** Exclusividad de Canal: Las notificaciones automáticas del sistema deben enviarse de forma única y obligatoria a través de WhatsApp.
- **RN-02:** Disparo Inmediato: Las notificaciones deben ser desencadenadas de forma inmediata tras la confirmación exitosa de la reserva o la anulación de la misma.
- **RN-03:** Contenido Informativo Completo: Las notificaciones enviadas deben contener los datos esenciales del agendamiento (Servicio(s), Podólogo, Fecha, Hora y Cliente/Teléfono) sin revelar precios ni información tarifaria.

## 4. CRITERIOS DE ACEPTACIÓN (Gherkin BDD)

**Escenario 1: Envío exitoso de notificación de confirmación de reserva (Happy Path)**
- **Dado** que un cliente ha completado con éxito la reserva de un horario disponible con un podólogo
- **Cuando** el sistema procesa y confirma el agendamiento
- **Entonces** el sistema dispara automáticamente un mensaje de confirmación por WhatsApp al número telefónico del cliente con los datos de su cita
- **Y** el sistema envía simultáneamente una notificación por WhatsApp al podólogo informando sobre la nueva reserva agendada en su agenda

**Escenario 2: Notificación inmediata al podólogo por anulación de reserva (Happy Path / Anulación)**
- **Dado** que existe una cita confirmada en la agenda de un podólogo
- **Cuando** el cliente anula exitosamente su reserva desde la plataforma
- **Entonces** el sistema envía de forma inmediata una notificación por WhatsApp al podólogo indicando la anulación de la cita y la liberación del horario

**Escenario 3: Fallo en el envío de la notificación por problema de integración/red (Sad Path)**
- **Dado** que se ha confirmado o anulado una reserva en la plataforma
- **Cuando** el servicio de envío de WhatsApp falla por problemas de conectividad o disponibilidad del proveedor
- **Entonces** el sistema registra el evento de fallo en los registros de auditoría
- **Y** garantiza que el estado de la reserva en el sistema (agendada o anulada) se mantenga guardado correctamente sin revertir la transacción del negocio

## 5. PUNTOS ABIERTOS / DEPENDENCIAS

- **Proveedor de Servicio de WhatsApp (API):** El PRD no especifica cuál es la solución o proveedor tecnológico seleccionado (ej. Twilio, Meta WhatsApp Business API, etc.) para el envío de los mensajes automáticos. Se declara formalmente como Punto Abierto para la fase de arquitectura.
- **Formato y Plantillas de Mensajes:** No se han definido los textos exactos ni las plantillas homologadas por WhatsApp que se utilizarán para la confirmación y anulación.

## 6. ORDEN DE DELEGACIÓN PARA EL QA

@QA: La Historia de Usuario Envío automático de notificaciones de confirmación y anulación de cita vía WhatsApp está lista en el archivo hu_03_notificaciones.md. Por favor, procede con la auditoría documental contra el Product Brief para asegurar que la historia cumple con los requerimientos originales.
