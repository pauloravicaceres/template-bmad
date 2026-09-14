## 1. HISTORIA DE USUARIO

- **Épica:** Sistema de Notificaciones Automáticas por WhatsApp
- **Título de la HU:** Envío Automático de Confirmaciones y Alertas de Cita por WhatsApp

> **Como** Cliente y Profesional Podólogo del Spa Ámely  
> **Quiero** recibir un mensaje automático e inmediato por WhatsApp cuando se confirma o anula una cita podológica  
> **Para** estar informados en tiempo real sobre los detalles del agendamiento sin mostrar precios y mantener la coordinación operativa del negocio

## 2. ALCANCE ESPECÍFICO (SCOPE)

- **Incluye:**
  - Envío automático de notificación de confirmación de reserva vía WhatsApp al cliente tras finalizar el agendamiento.
  - Envío automático de notificación de confirmación de cita vía WhatsApp al profesional podólogo asignado.
  - Envío automático de notificación por WhatsApp al profesional podólogo cuando un cliente anula una cita.
  - Formateo estricto del mensaje de notificación excluyendo cualquier información monetaria, tarifa o precio.
  - Inclusión de detalles operativos básicos en el mensaje: fecha, hora, profesional (para cliente), cliente (para profesional) y servicio(s) reservado(s).
- **NO Incluye:**
  - Envío de notificaciones a través de otros canales (ej. SMS, correo electrónico, notificaciones push).
  - Lógica del motor de disponibilidad y bloqueo de agendas (abarcado en Épica P1).
  - Interfaz del flujo de anulación por parte del cliente (abarcado en Épica P4).
  - Confirmación manual o respuesta interactiva dentro del chat de WhatsApp (chatbot conversacional).
  - Recordatorios automáticos previos a la cita (ej. 24 horas antes).

## 3. REGLAS DE NEGOCIO

- **RN-01 (Canal Exclusivo):** WhatsApp es el único canal oficial autorizado para el envío automático de notificaciones de confirmación y cancelación en el MVP.
- **RN-02 (Regla Inquebrantable - Sin Precios):** Las plantillas y contenidos de los mensajes enviados por WhatsApp no deben contener bajo ninguna circunstancia importes monetarios, costos de servicios ni precios totales.
- **RN-03 (Instantaneidad):** El disparo de la notificación a WhatsApp debe ejecutarse inmediatamente después de que se concrete el evento de reserva exitosa o anulación en la plataforma.
- **RN-04 (Destinatarios Duales en Reserva):** Cada reserva confirmada genera dos notificaciones automáticas independientes: una para el cliente y otra para el profesional podólogo asignado.

## 4. CRITERIOS DE ACEPTACIÓN (Gherkin BDD)

**Escenario 1: Envío exitoso de notificaciones de confirmación de reserva (Happy Path)**
- **Dado** que un cliente completa exitosamente la reserva de una cita en el motor de reservas
- **Cuando** el sistema procesa y confirma la reserva
- **Entonces** el sistema envía automáticamente un mensaje de confirmación por WhatsApp al número del cliente con el detalle de la cita (servicio, fecha, hora, profesional) sin mostrar precios
- **Y** envía automáticamente un mensaje de notificación por WhatsApp al profesional podólogo asignado informando la nueva cita reservada

**Escenario 2: Envío de notificación de anulación al profesional podólogo**
- **Dado** que un cliente solicita la anulación de una cita previamente agendada
- **Cuando** la anulación es procesada y el horario es liberado
- **Entonces** el sistema dispara inmediatamente un mensaje por WhatsApp al profesional podólogo asignado notificando la cancelación de dicha atención

**Escenario 3: Verificación de Prohibición de Precios en Mensajes de WhatsApp**
- **Dado** que el sistema genera el contenido de una notificación de WhatsApp (confirmación o cancelación)
- **Cuando** se construye la plantilla del mensaje a enviar
- **Entonces** se verifica que la plantilla omita de forma estricta cualquier valor numérico con formato de moneda, costos por servicio o totales

## 5. PUNTOS ABIERTOS / DEPENDENCIAS

- **Punto Abierto 1 (Formato de Identificación de WhatsApp):** Dado que la forma de identificación del cliente no está definida en el PRD, se asume provisionalmente que se requiere un número de teléfono celular válido durante la reserva para canalizar el WhatsApp.
- **Punto Abierto 2 (Manejo de Fallos de Entrega):** El PRD exige un 100% de notificaciones entregadas, pero no especifica la política de reintentos o alertas operativas en caso de fallos técnicos de la API externa de WhatsApp.
- **Dependencia:** Requiere la integración con la API del proveedor de servicio de WhatsApp y la recepción de eventos gatillo provenientes del Motor de Reservas (Épica P1) y del Módulo de Anulación (Épica P4).

## 6. ORDEN DE DELEGACIÓN PARA EL QA

@QA: La Historia de Usuario Envío Automático de Confirmaciones y Alertas de Cita por WhatsApp está lista en el archivo hu_02_notificaciones_whatsapp.md. Por favor, procede con la auditoría documental contra el Product Brief para asegurar que la historia cumple con los requerimientos originales.
