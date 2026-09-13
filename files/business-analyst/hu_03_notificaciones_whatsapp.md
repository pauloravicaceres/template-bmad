## 1. HISTORIA DE USUARIO

- **Épica:** Notificaciones Automatizadas por WhatsApp
- **Título de la HU:** Envío automático de notificaciones de confirmación y cancelación de citas por WhatsApp

> **Como** Cliente y Podólogo del spá podológico
> **Quiero** recibir notificaciones automáticas inmediatas vía WhatsApp cuando se reserve o cancele una cita
> **Para** disponer de la confirmación oportuna de la atención y permitir la liberación/reaprovechamiento inmediato de los horarios en la agenda del profesional

## 2. ALCANCE ESPECÍFICO (SCOPE)

- **Incluye:**
  - Envío automático de un mensaje de confirmación por WhatsApp al cliente al concretar una reserva (incluyendo detalle de servicios, fecha, hora, duración total y podólogo asignado).
  - Envío automático de una notificación de confirmación por WhatsApp al podólogo asignado sobre la nueva cita en su agenda.
  - Envío automático de una notificación inmediata por WhatsApp al podólogo asignado cuando un cliente anula o cancela una cita agendada.
  - Estructuración estandarizada de las plantillas de mensaje para asegurar claridad en la información transmitida.

- **NO Incluye:**
  - Envío de notificaciones por otros canales no mandatorios (ej. SMS, Email o notificaciones Push fuera del alcance de WhatsApp).
  - Recordatorios automáticos periódicos (ej. 24 horas antes o 2 horas antes de la cita) salvo que se definan en iteraciones posteriores.
  - Chat interactivo bidireccional o bot de conversación dentro de WhatsApp (el envío es unidireccional o transaccional).
  - Configuración manual de plantillas de mensaje por parte del podólogo o cliente.

## 3. REGLAS DE NEGOCIO

- **RN-01:** Canal Mandatorio Exclusivo: El envío de notificaciones automáticas del sistema (confirmación y cancelación) debe realizarse obligatoriamente a través del canal WhatsApp.
- **RN-02:** Desencadenamiento Inmediato: La notificación debe dispararse en tiempo real tras la confirmación de la reserva (Épica P1) o tras la anulación de la cita (Épica P5).
- **RN-03:** Notificación Dual en Confirmación: Cada nueva reserva confirmada debe enviar un mensaje de confirmación al número telefónico registrado del cliente y una alerta al podólogo asignado.
- **RN-04:** Alerta al Podólogo en Cancelación: Toda cancelación efectuada libera la agenda y notifica inmediatamente al podólogo asignado para posibilitar el reaprovechamiento del bloque horario.
- **RN-05:** Tolerancia a Fallos de Red/API: Ante un fallo en la API externa de WhatsApp, el sistema debe registrar el intento fallido en bitácora sin revertir ni interrumpir el estado de la reserva o cancelación en la base de datos.

## 4. CRITERIOS DE ACEPTACIÓN (Gherkin BDD)

**Escenario 1: Envío exitoso de notificación de confirmación al cliente y podólogo (Happy Path)**
- **Dado** que un cliente ha completado exitosamente la reserva de una cita para el servicio "Perfilado Podológico" el día "2026-09-15 10:00" con el "Dr. Carlos Ruiz"
- **Cuando** la transacción de reserva es confirmada en la base de datos
- **Entonces** el sistema dispara automáticamente un mensaje de confirmación por WhatsApp al número telefónico del cliente con el detalle de la cita
- **Y** envía una notificación por WhatsApp al "Dr. Carlos Ruiz" informando sobre la nueva cita agendada en su horario

**Escenario 2: Notificación inmediata al podólogo tras anulación de cita por parte del cliente**
- **Dado** que el cliente tenía una cita agendada con la "Dra. María López" para el día "2026-09-16 11:00"
- **Cuando** el cliente efectúa la anulación de la cita desde el módulo de autogestión
- **Entonces** el sistema procesa la cancelación, libera el horario en la agenda
- **Y** dispara inmediatamente un mensaje de alerta por WhatsApp a la "Dra. María López" notificando la anulación de la cita para que disponga del horario

**Escenario 3: Intento de envío con número telefónico con formato no válido o ausente (Sad Path)**
- **Dado** que se confirma una reserva pero el número telefónico registrado posee una estructura o prefijo no válido para WhatsApp
- **Cuando** el motor de notificaciones intenta despachar el mensaje
- **Entonces** la API de notificación identifica el error de formato, aborta el envío
- **Y** el sistema registra el evento en la bitácora de errores manteniendo la reserva activa en la agenda

**Escenario 4: Indisponibilidad temporal o fallo de conexión con la API de WhatsApp (Sad Path / Resiliencia)**
- **Dado** que la API empresarial de WhatsApp se encuentra fuera de servicio o no responde al momento de confirmar una reserva
- **Cuando** el sistema intenta enviar la notificación automática
- **Entonces** el sistema detecta el timeout o error de conexión de la API
- **Y** no bloquea ni revierte la reserva de la cita, garantizando que el agendamiento quede guardado correctamente en la agenda del podólogo

## 5. PUNTOS ABIERTOS / DEPENDENCIAS

- **Proveedor de API Empresarial de WhatsApp:** El Product Brief señala como pregunta abierta la elección de la API (ej. Twilio WhatsApp API o Meta Business API). Arquitectura deberá definir el proveedor y credenciales requeridas.
- **Estructura Definitiva de Plantillas (Templates):** Las plantillas de texto deben ser formalizadas y, en caso de usarse la API oficial de Meta, sometidas a aprobación previa de plantilla.
- **Dependencia de Disparo (Triggers):** Requiere la interacción previa de la Épica P1 (Motor de Reservas) para confirmaciones y de la Épica P5 (Auto-Gestión y Cancelación) para anulación.

## 6. ORDEN DE DELEGACIÓN PARA EL QA

@QA: La Historia de Usuario Envío automático de notificaciones de confirmación y cancelación de citas por WhatsApp está lista en el archivo hu_03_notificaciones_whatsapp.md. Por favor, procede con la auditoría documental contra el Product Brief para asegurar que la historia cumple con los requerimientos originales.
