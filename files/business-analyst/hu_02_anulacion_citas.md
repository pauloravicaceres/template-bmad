## 1. HISTORIA DE USUARIO

- **Épica:** Gestión de Citas y Anulaciones para Clientes y Podólogos
- **Título de la HU:** Anulación autónoma de cita por el cliente mediante código o enlace y liberación inmediata de agenda

> **Como** cliente con una cita agendada en el spa podológico
> **Quiero** solicitar la anulación de mi cita ingresando mi código único de reserva o a través de un enlace directo
> **Para** cancelar mi atención de manera autónoma y liberar inmediatamente el horario en la agenda del podólogo asignado

## 2. ALCANCE ESPECÍFICO (SCOPE)

- **Incluye:**
  - Ingreso del código único de reserva o acceso directo mediante enlace de cancelación asignado al cliente.
  - Validación del estado de la cita antes de procesar la anulación (verificar que la cita exista y esté en estado confirmada/activa).
  - Actualización del estado de la cita a "Anulada/Cancelada" en el sistema.
  - Liberación e independización inmediata del bloque de tiempo ocupado en el calendario/agenda del podólogo asignado.
  - Visualización de mensaje de confirmación de anulación exitosa para el cliente.
- **NO Incluye:**
  - Políticas ni restricciones de tiempo límite previo a la cita para permitir anulaciones (identificado como Punto Abierto por falta de especificación en el PRD).
  - Envío automático de notificaciones de anulación por WhatsApp al profesional podólogo (perteneciente a la Épica P3: Sistema de Notificaciones Automatizadas por WhatsApp).
  - Panel de consulta diaria de agenda por parte del podólogo (alcance complementario o de historias posteriores dentro del módulo de gestión).
  - Reagendamiento o reprogramación automática de la cita cancelada.

## 3. REGLAS DE NEGOCIO

- **RN-01:** La solicitud de anulación debe ser validada contra el código de reserva o token de enlace único generado durante el agendamiento inicial.
- **RN-02:** Una cita solo puede ser anulada si su estado actual en el sistema es "Confirmada" o "Activa". No se pueden anular citas previamente canceladas o completadas.
- **RN-03:** Al procesar la anulación, la liberación del bloque de tiempo en la agenda del podólogo debe ejecutarse de forma inmediata en tiempo real, dejando dicho espacio 100% disponible para nuevos agendamientos.
- **RN-04:** El sistema debe registrar la fecha y hora de la anulación para auditoría del historial de la cita.

## 4. CRITERIOS DE ACEPTACIÓN (Gherkin BDD)

**Escenario 1: Anulación exitosa de cita mediante código de reserva y liberación de agenda (Happy Path)**
- **Dado** que el cliente cuenta con un código único de reserva válido para una cita en estado "Confirmada"
- **Cuando** el cliente ingresa su código de reserva en el módulo de anulación y confirma la cancelación
- **Entonces** el sistema cambia el estado de la cita a "Anulada"
- **Y** libera inmediatamente el bloque de tiempo de la agenda del podólogo correspondiente a la cita cancelada
- **Y** muestra un mensaje en pantalla confirmando que la cita ha sido anulada exitosamente.

**Escenario 2: Intento de anulación con un código de reserva inexistente o inválido (Sad Path)**
- **Dado** que el cliente ingresa un código de reserva que no existe en el sistema
- **Cuando** el cliente solicita la anulación de la cita
- **Entonces** el sistema no modifica ningún registro en las agendas
- **Y** muestra un mensaje de error notificando que el código ingresado es inválido o no corresponde a ninguna reserva activa.

**Escenario 3: Intento de anulación de una cita ya cancelada previamente (Sad Path)**
- **Dado** que el cliente accede mediante el enlace de cancelación de una cita cuyo estado ya figura como "Anulada"
- **Cuando** el cliente intenta procesar nuevamente la anulación
- **Entonces** el sistema impide la transacción
- **Y** notifica al cliente que la cita ya se encuentra anulada previamente.

## 5. PUNTOS ABIERTOS / DEPENDENCIAS

- **PA-01 (Política y Tiempo Límite de Cancelación):** El Product Brief / PRD no especifica si existe un tiempo límite o margen mínimo antes de la hora de la cita (ej. 2 horas o 24 horas antes) para permitir la anulación sin penalización por parte del cliente.
- **PA-02 (Estructura del Código/Enlace Único):** No se especifica en el PRD la longitud, formato o mecanismo de generación segura del código único ni la estructura del enlace directo de cancelación.
- **PA-03 (Dependencia con Épica P3 - Notificación al Podólogo):** Al completar la anulación, se requiere gatillar el envío de una notificación automática vía WhatsApp al podólogo asignado para informarle la liberación del horario (perteneciente a la Épica P3).

## 6. ORDEN DE DELEGACIÓN PARA EL QA

@QA: La Historia de Usuario Anulación autónoma de cita por el cliente mediante código o enlace y liberación inmediata de agenda está lista en el archivo hu_02_anulacion_citas.md. Por favor, procede con la auditoría documental contra el Product Brief para asegurar que la historia cumple con los requerimientos originales.
