## 1. HISTORIA DE USUARIO

- **Épica:** Motor de Reservas Inteligente y Validación de Disponibilidad
- **Título de la HU:** Agendamiento de Cita con Selección de Podólogo, Cálculo de Duración Total y Bloqueo de Disponibilidad en Tiempo Real

> **Como** Cliente del Spá Podológico Ámely
> **Quiero** seleccionar uno o varios servicios podológicos y al profesional podólogo de mi preferencia para reservar una cita en un rango horario disponible
> **Para** asegurar la atención podológica requerida en una fecha/hora confirmada sin riesgo de cruce o sobreposición de agenda

## 2. ALCANCE ESPECÍFICO (SCOPE)

- **Incluye:**
  - Selección autónoma de uno o múltiples servicios podológicos por parte del cliente.
  - Selección del profesional podólogo preferido para la atención.
  - Cálculo automático e inmediato del tiempo total estimado de la cita mediante la suma lineal de las duraciones promedio de los servicios seleccionados.
  - Consulta y despliegue síncrono de bloques horarios disponibles para el podólogo seleccionado.
  - Captura del formulario de reserva con los datos del cliente.
  - Bloqueo inmediato en tiempo real del bloque horario seleccionado para evitar sobreposiciones o duplicidad de citas (Cero Cruces de Agenda).
  - Ocultamiento estricto de precios durante todo el proceso de reserva.
- **NO Incluye:**
  - Visualización o desglose de precios o costos de los servicios (Restricción por estrategia comercial).
  - Envío de notificaciones automáticas por WhatsApp tras la reserva (Corresponde a la Épica [P2]).
  - Panel privado de visualización de agenda para podólogos (Corresponde a la Épica [P3]).
  - Autogestión de cancelación o reprogramación de citas creadas (Corresponde a la Épica [P3]).
  - Procesamiento de pagos, pasarelas de pago o cobros de señas online.
  - Algoritmos avanzados de optimización de tiempos muertos entre servicios.

## 3. REGLAS DE NEGOCIO

- **RN-01 (Cero Cruces de Agenda):** El sistema debe garantizar que un podólogo no pueda recibir dos o más reservas que compartan o traslapen cualquier minuto de su rango horario.
- **RN-02 (Cálculo de Duración Total):** La duración total requerida para la cita se calcula sumando la duración promedio (en minutos) de cada uno de los servicios seleccionados en el agendamiento.
- **RN-03 (Ocultamiento Estratégico de Precios):** Ninguna interfaz o respuesta del flujo de reserva debe mostrar tarifas, montos económicos o precios de los servicios.
- **RN-04 (Validación de Disponibilidad Síncrona):** Un bloque horario solo se presentará como disponible si el podólogo cuenta con un espacio continuo e ininterrumpido igual o mayor a la duración total calculada.
- **RN-05 (Bloqueo Atómico de Horario):** Al confirmar la reserva, el sistema debe bloquear el rango horario asignado de manera síncrona en la agenda del podólogo.

## 4. CRITERIOS DE ACEPTACIÓN (Gherkin BDD)

**Escenario 1: Agendamiento exitoso de cita con bloqueo de disponibilidad en tiempo real (Happy Path)**
- **Dado** que el cliente se encuentra en la plataforma de reservas y ha seleccionado uno o varios servicios podológicos
- **Y** ha elegido a un podólogo de su preferencia
- **Cuando** el sistema calcula la duración total acumulada sumando los tiempos promedio de los servicios seleccionados
- **Y** el cliente selecciona un bloque horario disponible e ingresa sus datos personales
- **Y** confirma la solicitud de reserva
- **Entonces** el sistema valida síncronamente que el horario permanezca libre
- **Y** registra la cita en estado confirmada, reservando y bloqueando de forma inmediata dicho bloque horario en la agenda del podólogo para impedir cruces
- **Y** muestra un mensaje de confirmación de reserva en pantalla sin exhibir ningún precio o costo económico.

**Escenario 2: Intento de reserva en un rango horario en proceso de bloqueo o ya ocupado (Sad Path / Concurrencia)**
- **Dado** que un cliente intenta confirmar una cita para un podólogo en un rango horario específico
- **Cuando** otro usuario ha confirmado una reserva para el mismo podólogo que se traslapa con el rango horario seleccionado
- **Entonces** el sistema impide el registro de la nueva reserva
- **Y** muestra un mensaje de advertencia indicando que el horario ya no se encuentra disponible, solicitando al cliente seleccionar un nuevo horario.

**Escenario 3: Verificación de ocultamiento estricto de precios en la interfaz de reserva**
- **Dado** que el cliente está navegando por la selección de servicios, podólogos y bloques horarios
- **Cuando** visualiza el resumen de la cita antes de confirmar
- **Entonces** el sistema exhibe detalladamente los servicios seleccionados, la duración total estimada en minutos, la fecha, el horario y el podólogo asignado
- **Pero** omite estrictamente cualquier información relacionada con precios, montos o valores monetarios.

## 5. PUNTOS ABIERTOS / DEPENDENCIAS

- **Punto Abierto 1 (Datos personales mínimos del cliente):** Ni el Product Brief ni el Plan de MVP especifican los campos de identificación personal exactos (ej. Nombre Completo, WhatsApp/Teléfono, Correo Electrónico) requeridos obligatoriamente en el formulario para registrar la cita. Se declara como Punto Abierto para definición en la fase de arquitectura/UX.
- **Punto Abierto 2 (Reglas exactas de validación de disponibilidad síncrona y cálculo de tiempos):** El PRD no especifica si la suma de duraciones promedio contempla margen de holgura (tiempos muertos/desinfección entre citas) ni la resolución mínima de bloques de agenda (ej. intervalos de 15, 30 o 60 minutos), ni cómo se administran las jornadas laborales/descansos de los podólogos en el motor.
- **Dependencia 1:** Definición del catálogo de servicios y sus duraciones promedio estándar (proporcionado por la Épica [P4] o configuración previa).

## 6. ORDEN DE DELEGACIÓN PARA EL QA

@QA: La Historia de Usuario Agendamiento de Cita con Selección de Podólogo, Cálculo de Duración Total y Bloqueo de Disponibilidad en Tiempo Real está lista en el archivo hu_01_reserva_citas.md. Por favor, procede con la auditoría documental contra el Product Brief para asegurar que la historia cumple con los requerimientos originales.
