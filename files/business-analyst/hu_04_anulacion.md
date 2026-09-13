## 1. HISTORIA DE USUARIO

- **Épica:** Módulo de Anulación de Citas por el Cliente
- **Título de la HU:** Anulación autónoma de cita por parte del cliente

> **Como** Cliente del Spa Podológico
> **Quiero** poder anular de forma autónoma una reserva agendada previamente a través de la interfaz web
> **Para** liberar la disponibilidad en la agenda del podólogo cuando no me sea posible asistir a mi atención

## 2. ALCANCE ESPECÍFICO (SCOPE)

- **Incluye:**
  - Opción desde la interfaz web para que el cliente solicite la anulación de su cita previa.
  - Confirmación explícita antes de ejecutar la acción de anulación para evitar cancelaciones accidentales.
  - Actualización automática e inmediata del estado de la cita a "Anulada" / "Cancelada" en el sistema.
  - Liberación inmediata del rango de tiempo reservado en la agenda del podólogo correspondiente para que quede disponible para otros clientes.

- **NO Incluye:**
  - Envío de notificaciones por WhatsApp (disparado automáticamente por la Épica [P3] de Notificaciones Automáticas por WhatsApp).
  - Políticas o restricciones de tiempo límite de cancelación (declarado como punto abierto al no estar especificado en el PRD).
  - Reprogramación directa de la cita en el mismo flujo (el cliente debe anular y agendar un nuevo horario de forma separada).
  - Cobros por penalización o reembolso de dinero (los precios están ocultos y no hay pasarela de pago en el MVP).

## 3. REGLAS DE NEGOCIO

- **RN-01:** Confirmación del usuario: La acción de anulación requiere obligatoriamente una confirmación explícita por parte del cliente antes de procesarse.
- **RN-02:** Liberación inmediata de disponibilidad: Al anularse la cita, el bloque de horario del podólogo debe quedar disponible al instante en el motor de agendamiento.
- **RN-03:** Irreversibilidad: Una vez confirmada la anulación de una cita, su estado no puede ser revertido manualmente a activa por el cliente.

## 4. CRITERIOS DE ACEPTACIÓN (Gherkin BDD)

**Escenario 1: Anulación exitosa de reserva por parte del cliente (Happy Path)**
- **Dado** que un cliente tiene una cita podológica agendada en estado confirmada
- **Cuando** solicita la anulación de su reserva desde la interfaz web y confirma la acción en la ventana de verificación
- **Entonces** el sistema actualiza el estado de la cita a "Anulada"
- **Y** libera el bloque de horario asignado en la agenda del podólogo dejándolo disponible en tiempo real

**Escenario 2: Cancelación del flujo de anulación (Sad Path / Arrepentimiento)**
- **Dado** que el cliente inicia el flujo para anular su reserva
- **Cuando** el sistema solicita la confirmación de la anulación y el usuario decide rechazar o cancelar el cuadro de diálogo
- **Entonces** el sistema no modifica el estado de la cita
- **Y** mantiene la reserva activa en la agenda del podólogo

**Escenario 3: Intentar anular una cita previamente anulada (Sad Path)**
- **Dado** que una cita podológica ya ha sido anulada anteriormente
- **Cuando** se intenta acceder a la opción de anulación para esa misma cita
- **Entonces** el sistema no permite ejecutar la acción e informa que la cita ya se encuentra anulada

## 5. PUNTOS ABIERTOS / DEPENDENCIAS

- **Políticas y Tiempos Límite de Cancelación:** El PRD/Product Brief no especifica si existe un margen o límite de tiempo mínimo antes de la cita (ej. máximo 2 horas antes) para permitir la anulación autónoma desde la web. Se declara formalmente como Punto Abierto.
- **Mecanismo de Identificación para Acceder a la Anulación:** Al no existir un módulo de inicio de sesión/autenticación de cliente definido en el PRD, el mecanismo para que el cliente identifique y consulte su cita a anular (ej. código de reserva, enlace único o teléfono) queda sujeto a definición funcional/técnica.

## 6. ORDEN DE DELEGACIÓN PARA EL QA

@QA: La Historia de Usuario Anulación autónoma de cita por parte del cliente está lista en el archivo hu_04_anulacion.md. Por favor, procede con la auditoría documental contra el Product Brief para asegurar que la historia cumple con los requerimientos originales.
