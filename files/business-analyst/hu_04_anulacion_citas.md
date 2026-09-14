## 1. HISTORIA DE USUARIO

- **Épica:** Módulo de Anulación de Citas por el Cliente
- **Título de la HU:** Anulación Autónoma de Citas Previas por el Cliente

> **Como** Cliente del Spa Podológico Ámely  
> **Quiero** consultar mi cita previamente agendada e ingresar la solicitud de anulación  
> **Para** cancelar mi atención de forma autónoma, liberar el bloque de tiempo en la agenda del profesional y disparar la alerta correspondiente sin visualizar precios

## 2. ALCANCE ESPECÍFICO (SCOPE)

- **Incluye:**
  - Búsqueda / consulta de la cita agendada por el cliente (asumiendo de forma provisional el uso de número telefónico o código de reserva como mecanismo de consulta).
  - Visualización del resumen de la cita activa (servicios, fecha, hora y profesional) sin mostrar importes ni tarifas.
  - Confirmación explícita de anulación por parte del cliente.
  - Liberación inmediata del bloque horario en la agenda del profesional podólogo.
  - Desencadenamiento del evento de anulación para el envío de notificación por WhatsApp al profesional podólogo.
- **NO Incluye:**
  - Reprogramación o cambio directo de horario en la misma transacción (requiere anular y volver a agendar en P1).
  - Lógica de notificaciones por WhatsApp (abarcado en Épica P2).
  - Anulación o cancelación de citas por parte del profesional o administrador desde el panel interno (abarcado en Épica P5).
  - Gestión de penalizaciones financieras o reembolsos.

## 3. REGLAS DE NEGOCIO

- **RN-01 (Liberación Instantánea):** Al confirmar la anulación, el bloque horario asociado a la cita debe quedar inmediatamente disponible en el motor de reservas para otros clientes.
- **RN-02 (Sin Precios):** La pantalla de consulta y confirmación de anulación no debe mostrar ningún dato de costo, tarifa ni importe abonado.
- **RN-03 (Confirmación del Usuario):** Toda anulación requiere un paso de confirmación explícito para evitar cancelaciones accidentales por parte del cliente.

## 4. CRITERIOS DE ACEPTACIÓN (Gherkin BDD)

**Escenario 1: Anulación exitosa de cita por parte del cliente (Happy Path)**
- **Dado** que el cliente ingresa al módulo de anulación y ubica su cita previamente agendada
- **Cuando** solicita anular la cita y confirma la acción en el diálogo de verificación
- **Entonces** el sistema marca la cita como cancelada y libera el bloque horario del profesional podólogo en la agenda en tiempo real
- **Y** dispara la notificación de anulación por WhatsApp dirigida al profesional podólogo

**Escenario 2: Intento de consulta de cita inexistente o ya anulada (Sad Path)**
- **Dado** que el cliente ingresa un identificador o número de cita que no existe o ya fue anulada previamente
- **Cuando** ejecuta la búsqueda de la cita
- **Entonces** el sistema muestra un mensaje informativo indicando que no se encontraron citas activas asociadas
- **Y** no permite realizar ninguna acción de cancelación

**Escenario 3: Verificación de Prohibición de Precios en el Módulo de Anulación**
- **Dado** que el cliente visualiza el detalle de su cita para confirmar la anulación
- **Cuando** revisa los datos presentados en pantalla
- **Entonces** se verifica que la interfaz no exhiba precios, costos de atención ni importes monetarios

## 5. PUNTOS ABIERTOS / DEPENDENCIAS

- **Punto Abierto 1 (Mecanismo de Identificación/Autenticación para Anular):** El PRD no especifica la forma de identificación del cliente para consultar y validar la propiedad de la cita a anular (ej. número telefónico cel, código único de reserva enviado por WhatsApp).
- **Punto Abierto 2 (Política de Anticipación de Cancelación):** El PRD no define un límite de tiempo mínimo previo a la cita para permitir la anulación (ej. cancelar con al menos 2 horas de anticipación).
- **Dependencia:** Requiere la integración con la Épica P2 para disparar la notificación por WhatsApp al profesional podólogo ante una anulación exitosa.

## 6. ORDEN DE DELEGACIÓN PARA EL QA

@QA: La Historia de Usuario Anulación Autónoma de Citas Previas por el Cliente está lista en el archivo hu_04_anulacion_citas.md. Por favor, procede con la auditoría documental contra el Product Brief para asegurar que la historia cumple con los requerimientos originales.
