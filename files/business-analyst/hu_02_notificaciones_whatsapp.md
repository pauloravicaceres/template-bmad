## 1. HISTORIA DE USUARIO

- **Épica:** Sistema Integrado de Notificaciones vía WhatsApp
- **Título de la HU:** Envío automático e inmediato de notificaciones y alertas por WhatsApp

> **Como** sistema automatizado de notificaciones
> **Quiero** enviar un mensaje instantáneo de confirmación al cliente y una alerta al podólogo a través de WhatsApp tras la confirmación o cancelación de una reserva
> **Para** mitigar inasistencias (no-shows) y mantener informado al personal de forma inmediata sin intervención manual

## 2. ALCANCE ESPECÍFICO (SCOPE)

- **Incluye:**
  - Despacho automático e inmediato (< 1 minuto) de mensaje de confirmación por WhatsApp al cliente una vez concretada la reserva.
  - Despacho automático e inmediato (< 1 minuto) de alerta por WhatsApp al podólogo asignado ante una nueva reserva o anulación de cita.
  - Formato estandarizado de mensaje que incluye datos clave de la cita (fecha, hora, servicios seleccionados, podólogo asignado) sin incluir información de precios.
  - Registro de fallos en el historial de despacho si ocurre un problema en el canal de envío.
- **NO Incluye:**
  - El motor de reservas y cálculo de disponibilidad (corresponde a la Épica P1).
  - El flujo de anulación manual de citas por el cliente desde la web (corresponde a la Épica P4).
  - El panel del profesional para visualizar la agenda o cambiar estados (corresponde a la Épica P3).
  - Notificaciones por otros canales no especificados (SMS, correo electrónico).

## 3. REGLAS DE NEGOCIO

- **RN-01:** (Canal Exclusivo de Notificación) Toda notificación o alerta enviada por el sistema debe realizarse de forma estricta a través del canal WhatsApp.
- **RN-02:** (Tiempo Máximo de Despacho) Las notificaciones automáticas deben emitirse e iniciarse dentro de una ventana máxima de 1 minuto (< 1 minuto) tras el evento detonante (reserva o anulación).
- **RN-03:** (Estrategia Comercial de Precios) Las notificaciones de WhatsApp enviadas al cliente o podólogo no deben contener precios, valores monetarios ni desgloses de costos.
- **RN-04:** (Contenido Mínimo de Confirmación al Cliente) El mensaje de confirmación al cliente debe incluir nombre del cliente, fecha y hora de la cita, servicios a realizar y podólogo asignado.
- **RN-05:** (Contenido Mínimo de Alerta al Podólogo) La alerta enviada al podólogo debe incluir el tipo de evento (nueva reserva o anulación), nombre del cliente, fecha, hora y servicios asociados.

## 4. CRITERIOS DE ACEPTACIÓN (Gherkin BDD)

**Escenario 1: Envío exitoso de confirmación al cliente tras reserva (Happy Path)**
- **Dado** que un cliente ha concretado exitosamente la reserva de una cita podológica
- **Cuando** la transacción de agendamiento se confirma en el sistema
- **Entonces** el sistema despacha automáticamente un mensaje de confirmación por WhatsApp al número del cliente en un tiempo menor a 1 minuto
- **Y** el mensaje contiene el resumen de la cita (fecha, hora, servicios, podólogo asignado) omitiendo todo dato de precios.

**Escenario 2: Envío exitoso de alerta al podólogo tras nueva reserva (Happy Path)**
- **Dado** que se ha registrado una nueva cita en la agenda de un podólogo
- **Cuando** el agendamiento queda confirmado en el sistema
- **Entonces** el sistema envía inmediatamente (< 1 minuto) una alerta por WhatsApp al podólogo asignado
- **Y** la alerta notifica la nueva cita agendada indicando el nombre del cliente, fecha, hora y lista de servicios.

**Escenario 3: Envío exitoso de alerta al podólogo tras cancelación de cita (Happy Path)**
- **Dado** que una cita agendada ha sido cancelada
- **Cuando** el evento de anulación se registra en el sistema
- **Entonces** el sistema despacha una alerta inmediata (< 1 minuto) por WhatsApp al podólogo asignado informando la liberación de la franja horaria.

**Escenario 4: Manejo de error por número de WhatsApp no válido o fallo de canal (Sad Path)**
- **Dado** que se confirma una reserva o cancelación en el sistema
- **Cuando** el servicio de envío de WhatsApp falla por problemas de conectividad o un número inválido
- **Entonces** el sistema registra el fallo en el historial de envíos
- **Y** no interrumpe ni revierte la reserva o cancelación ya realizada en la agenda.

## 5. PUNTOS ABIERTOS / DEPENDENCIAS

- **Punto Abierto 1 (Proveedor / API de WhatsApp):** El Product Brief y PRD no especifican la solución tecnológica ni el proveedor para la integración con WhatsApp (ej. WhatsApp Business API), lo cual representa una dependencia técnica externa.
- **Punto Abierto 2 (Políticas de Reintento):** No se encuentran definidas las políticas de reintento automático en caso de fallas temporales en la plataforma de notificaciones.
- **Punto Abierto 3 (Plantillas Específicas de Mensaje):** Falta la definición exacta por parte del equipo de negocio sobre la plantilla y texto final autorizado para las notificaciones.
