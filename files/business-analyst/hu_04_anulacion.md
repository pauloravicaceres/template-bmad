# 1. HISTORIA DE USUARIO

- **Épica:** Módulo de Anulación de Citas por el Cliente
- **Título de la HU:** Anulación autónoma de cita por parte del cliente

> **Como** Cliente de Ámely Spá Podológico  
> **Quiero** anular una cita agendada previamente desde la plataforma web  
> **Para** liberar mi horario reservado en la agenda del especialista cuando no pueda asistir  

## 2. ALCANCE ESPECÍFICO (SCOPE)

- **Incluye:**
  - Consulta y localización de la cita activa agendada por el cliente.
  - Confirmación de la solicitud de anulación de la cita por parte del cliente.
  - Cambio de estado de la cita a "Anulada" / "Cancelada" en el sistema.
  - Liberación inmediata del rango de tiempo en la agenda del especialista podólogo asignado.
- **NO Incluye:**
  - Reprogramación directa de la cita (cambiar fecha/hora en la misma transacción).
  - Devolución o reembolso de dinero (el MVP no incluye pagos online).
  - Anulación manual por parte del podólogo o administración (solo abarca autogestión del cliente).

## 3. REGLAS DE NEGOCIO

- **RN-01:** La anulación debe liberar automáticamente el bloque horario completo en la agenda del especialista podólogo en tiempo real.
- **RN-02:** Una cita con estado "Anulada" no puede ser reactivada ni modificada posteriormente.

## 4. CRITERIOS DE ACEPTACIÓN (Gherkin BDD)

**Escenario 1: Anulación exitosa de cita agendada (Happy Path)**
- **Dado** que el cliente cuenta con una cita previamente agendada y activa en el sistema
- **Cuando** solicita la anulación de la cita y confirma la acción
- **Entonces** el sistema actualiza el estado de la cita a anulada
- **Y** libera de inmediato el bloque de horario en la agenda del especialista podólogo en tiempo real.

**Escenario 2: Intento de anulación de cita inexistente o ya anulada (Sad Path)**
- **Dado** que el cliente intenta acceder a la anulación de una cita
- **Cuando** el identificador de la cita no existe o ya presenta un estado anulado
- **Entonces** el sistema rechaza la solicitud de anulación
- **Y** muestra un mensaje claro indicando que la cita no se encuentra activa o no fue localizada.

## 5. PUNTOS ABIERTOS / DEPENDENCIAS

- **Mecanismo de localización e identificación:** El PRD no especifica el mecanismo exacto mediante el cual el cliente localiza o valida la propiedad de la cita a anular (ej. código de reserva, número de teléfono, DNI o enlace directo).
- **Política de ventana de tiempo previa para anulación:** No se especifica en el PRD si existe una política de restricción de tiempo mínimo previo a la cita (ej. permitir anulación hasta 2 horas antes de la atención) para procesar la cancelación.

## 6. ORDEN DE DELEGACIÓN PARA EL QA

@QA: La Historia de Usuario Anulación autónoma de cita por parte del cliente está lista en el archivo hu_04_anulacion.md. Por favor, procede con la auditoría documental contra el Product Brief para asegurar que la historia cumple con los requerimientos originales.
