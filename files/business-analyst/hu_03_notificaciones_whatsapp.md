## 1. HISTORIA DE USUARIO

- **Épica:** Sistema de Notificaciones Automatizadas por WhatsApp
- **Título de la HU:** Envío automático de notificaciones vía WhatsApp por confirmación de reserva y anulación de cita

> **Como** cliente y profesional podólogo del spa
> **Quiero** recibir una notificación automática instantánea por WhatsApp tras la confirmación o anulación de una cita
> **Para** disponer de la confirmación inmediata del servicio y mantener el cronograma de atenciones siempre actualizado

## 2. ALCANCE ESPECÍFICO (SCOPE)

- **Incluye:**
  - Desencadenamiento automático de notificación por WhatsApp al cliente al concretarse exitosamente un agendamiento de cita.
  - Desencadenamiento automático de notificación por WhatsApp al podólogo asignado notificando los detalles de la nueva cita agendada.
  - Desencadenamiento automático de notificación por WhatsApp al podólogo asignado informando la anulación de una cita previamente agendada por el cliente.
  - Registro del estado de entrega/envío del evento de notificación en la bitácora del sistema (ej. enviado/fallido).
- **NO Incluye:**
  - Selección, contratación o configuración técnica del proveedor/API externa de WhatsApp Business (identificado como Punto Abierto / Bloqueante).
  - Redacción final o aprobación de plantillas de mensajes (HSM templates) de WhatsApp (Punto Abierto).
  - Notificaciones por otros canales no obligatorios (SMS, correo electrónico).
  - Envíos de recordatorios preventivos periódicos pre-cita (ej. 24 horas antes).

## 3. REGLAS DE NEGOCIO

- **RN-01:** El envío de notificaciones debe ser gatillado de forma automática e inmediata al momento de completarse el evento de confirmación de reserva o anulación de cita.
- **RN-02:** WhatsApp es el canal único y obligatorio para la comunicación y confirmación automatizada con clientes y podólogos.
- **RN-03:** Las notificaciones enviadas deben incluir la información clave de la cita (fecha, hora, servicio, profesional asignado y código/enlace de gestión).
- **RN-04:** En caso de fallas de conexión con la API externa de WhatsApp, el sistema debe registrar el error para seguimiento operativo sin revertir la transacción principal de reserva o anulación.

## 4. CRITERIOS DE ACEPTACIÓN (Gherkin BDD)

**Escenario 1: Envío exitoso de notificación por WhatsApp al cliente y podólogo tras nueva reserva (Happy Path)**
- **Dado** que un cliente ha completado exitosamente una reserva de cita con un podólogo
- **Cuando** el sistema procesa y confirma el agendamiento
- **Entonces** el sistema gatilla automáticamente el envío de un mensaje de confirmación por WhatsApp al número del cliente con los detalles de la cita
- **Y** gatilla automáticamente un mensaje por WhatsApp al podólogo asignado con el detalle del nuevo cliente y horario reservado.

**Escenario 2: Envío exitoso de notificación por WhatsApp al podólogo tras anulación de cita (Happy Path)**
- **Dado** que un cliente anula exitosamente una cita confirmada
- **Cuando** el sistema registra la anulación y libera la agenda
- **Entonces** el sistema gatilla automáticamente una notificación por WhatsApp al podólogo asignado informando la liberación del horario.

**Escenario 3: Manejo de fallos en el servicio o API externa de WhatsApp (Sad Path)**
- **Dado** que la API externa de WhatsApp se encuentra fuera de servicio o no disponible
- **Cuando** el cliente confirma una reserva exitosa en el sistema
- **Entonces** el sistema completa el bloqueo del horario y la reserva en la base de datos
- **Y** registra el evento de notificación con estado "Fallido / Pendiente" en la bitácora del sistema sin interrumpir la confirmación en pantalla al cliente.

## 5. PUNTOS ABIERTOS / DEPENDENCIAS

- **PA-01 (Proveedor y API de WhatsApp Business):** El Product Brief / PRD no define el proveedor de API de WhatsApp (ej. Twilio, Meta Cloud API, Gupshup) ni las credenciales de entorno requeridas.
- **PA-02 (Plantillas de Mensajes Aprobadas):** No se especifican en el PRD las plantillas exactas de mensaje (HSM templates) exigidas por la API de WhatsApp Business para la aprobación de notificaciones transaccionales.
- **PA-03 (Dependencia con Épicas P1 y P2):** El envío de notificaciones depende directamente de los eventos de confirmación de reserva (Épica P1) y de anulación (Épica P2).

## 6. ORDEN DE DELEGACIÓN PARA EL QA

@QA: La Historia de Usuario Envío automático de notificaciones vía WhatsApp por confirmación de reserva y anulación de cita está lista en el archivo hu_03_notificaciones_whatsapp.md. Por favor, procede con la auditoría documental contra el Product Brief para asegurar que la historia cumple con los requerimientos originales.
