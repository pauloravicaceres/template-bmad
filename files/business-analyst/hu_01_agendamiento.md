# 1. HISTORIA DE USUARIO

- **Épica:** Motor de Reservas e Integración de Agenda en Tiempo Real
- **Título de la HU:** Agendamiento de cita podológica y reserva de horario en tiempo real

> **Como** Cliente de Ámely Spá Podológico  
> **Quiero** seleccionar uno o más servicios podológicos, especialista y una fecha/hora disponible  
> **Para** agendar mi atención sin generar solapamientos de horario en la agenda del especialista  

## 2. ALCANCE ESPECÍFICO (SCOPE)

- **Incluye:**
  - Selección de uno o varios servicios podológicos.
  - Selección de especialista disponible o asignación según disponibilidad.
  - Cálculo automático de la duración total acumulada de los servicios seleccionados.
  - Consulta y despliegue de horarios disponibles en tiempo real según la duración calculada.
  - Bloqueo y reserva del rango de tiempo seleccionado en la agenda del especialista.
- **NO Incluye:**
  - Autenticación o registro de clientes mediante un mecanismo específico (ej. OTP, correo, login).
  - Envío de notificaciones por WhatsApp o correo de confirmación.
  - Procesamiento de pagos o cobranza en línea.
  - Anulación o reprogramación de la cita agendada.

## 3. REGLAS DE NEGOCIO

- **RN-01:** El sistema debe calcular la duración total de la atención sumando los tiempos promedio de cada servicio podológico seleccionado.
- **RN-02:** El sistema no debe permitir agendar ni mostrar bloques de tiempo en el pasado o que presenten solapamiento con citas previamente reservadas en la agenda del especialista.
- **RN-03:** Un bloque de horario solo se considera reservado y bloqueado una vez confirmada la acción de agendamiento.

## 4. CRITERIOS DE ACEPTACIÓN (Gherkin BDD)

**Escenario 1: Agendamiento exitoso de atención podológica sin solapamientos (Happy Path)**
- **Dado** que el cliente selecciona uno o más servicios podológicos y un especialista
- **Y** el sistema calcula la duración total acumulada de la atención
- **Cuando** el cliente selecciona una fecha y un bloque de horario continuo disponible en tiempo real
- **Entonces** el sistema reserva la cita y bloquea la totalidad del rango de tiempo en la agenda del especialista
- **Y** el horario deja de estar disponible para futuras consultas de otros clientes

**Escenario 2: Intento de reserva en horario no disponible o solapado (Sad Path)**
- **Dado** que el cliente ha seleccionado la fecha y servicios podológicos a agendar
- **Cuando** el cliente intenta seleccionar un horario que ya fue reservado o no cuenta con la duración continua requerida
- **Entonces** el sistema impide la selección del horario
- **Y** muestra un mensaje indicando que el horario no está disponible y solicita seleccionar un nuevo bloque

## 5. PUNTOS ABIERTOS / DEPENDENCIAS

- **Mecanismo de identificación/autenticación del cliente:** El PRD no especifica el mecanismo exacto mediante el cual se identifica o autentica el cliente al momento de agendar la cita (ej. ingreso de DNI, teléfono, correo o validación OTP). Se requiere definición formal previo a la fase de arquitectura/desarrollo.

## 6. ORDEN DE DELEGACIÓN PARA EL QA

@QA: La Historia de Usuario Agendamiento de cita podológica y reserva de horario en tiempo real está lista en el archivo hu_01_agendamiento.md. Por favor, procede con la auditoría documental contra el Product Brief para asegurar que la historia cumple con los requerimientos originales.
