## 1. HISTORIA DE USUARIO

- **Épica:** Motor de Reservas Inteligente y Control de Disponibilidad
- **Título de la HU:** Agendamiento de Cita Multiservicio con Selección de Podólogo y Bloqueo de Disponibilidad en Tiempo Real

> **Como** cliente del Spá Podológico  
> **Quiero** seleccionar uno o varios servicios y al podólogo de mi preferencia para consultar la disponibilidad de agenda en tiempo real y registrar mi reserva  
> **Para** asegurar la atención requerida en un bloque de tiempo continuo sin cruces ni sobreposiciones de agenda.

## 2. ALCANCE ESPECÍFICO (SCOPE)

- **Incluye:**
  - Selección autónoma de uno o múltiples servicios podológicos del catálogo.
  - Selección del profesional podólogo preferido para la atención.
  - Cálculo automático y dinámico de la duración total acumulada sumando la duración estimada de cada servicio seleccionado.
  - Consulta y despliegue de horarios disponibles en tiempo real para el podólogo seleccionado considerando la duración total acumulada.
  - Registro de la reserva con bloqueo automático del bloque horario consecutivo asignado en la agenda del podólogo.
  - Presentación de confirmación del agendamiento exitoso en pantalla.
- **NO Incluye:**
  - Exposición o cálculo de precios, tarifas o costos de los servicios (restricción estricta de ocultación de precios).
  - Envío automático de notificaciones por WhatsApp (corresponde a la Épica P2).
  - Visualización del dashboard de agenda diaria/semanal por parte del podólogo (corresponde a la Épica P3).
  - Cancelación o reprogramación de citas existentes por parte del cliente (corresponde a la Épica P3).
  - Configuración o administración de horarios de trabajo, turnos o ausencias de los podólogos.

## 3. REGLAS DE NEGOCIO

- **RN-01:** El sistema debe calcular dinámicamente la duración total acumulada de la cita sumando los tiempos promedio estimados de cada servicio seleccionado antes de solicitar la fecha y hora de reserva.
- **RN-02:** El sistema no debe exponer ni mostrar precios, costos o tarifas en ninguna etapa del flujo de selección o confirmación de la reserva.
- **RN-03:** El sistema debe permitir seleccionar únicamente bloques de tiempo donde el podólogo elegido cuente con disponibilidad continua igual o mayor a la duración total acumulada calculada.
- **RN-04:** El sistema no debe permitir agendar citas en fechas u horas pasadas, ni en bloques de tiempo previamente reservados o bloqueados (0% de sobreposiciones/cruces).
- **RN-05:** Al confirmarse el agendamiento, el bloque horario total debe quedar reservado e indisponible de forma inmediata en tiempo real para futuras consultas.

## 4. CRITERIOS DE ACEPTACIÓN (Gherkin BDD)

**Escenario 1: Agendamiento exitoso de cita multiservicio con podólogo seleccionado (Happy Path)**
- **Dado** que el cliente se encuentra en el motor de reservas
- **Y** selecciona dos o más servicios podológicos con sus respectivos tiempos estimados de atención
- **Y** selecciona al podólogo de su preferencia
- **Cuando** el cliente solicita ver la disponibilidad de agenda
- **Entonces** el sistema calcula automáticamente la duración acumulada total de los servicios
- **Y** presenta únicamente los bloques de fecha y hora en los que el podólogo tiene disponibilidad continua suficiente sin mostrar precios
- **Cuando** el cliente selecciona un bloque horario disponible e ingresa sus datos requeridos de reserva y confirma la acción
- **Entonces** el sistema registra la reserva y bloquea de inmediato ese rango de tiempo en la agenda del podólogo evitando cruces de citas
- **Y** muestra un mensaje de confirmación del agendamiento en pantalla con el resumen de la cita.

**Escenario 2: Intento de agendamiento en bloque horario sin disponibilidad suficiente (Sad Path / Flujo Alternativo)**
- **Dado** que el cliente ha seleccionado servicios con una duración total acumulada de 60 minutos y a un podólogo específico
- **Cuando** consulta los horarios para una fecha determinada en la que el podólogo solo cuenta con lapsos libres discontinuos o menores a 60 minutos
- **Entonces** el sistema no muestra dichos lapsos como disponibles para selección
- **Y** notifica al cliente que no existe disponibilidad continua suficiente para el podólogo seleccionado en la fecha elegida, sugiriendo seleccionar otro rango u otro profesional.

**Escenario 3: Intento de reserva en un bloque horario seleccionado simultáneamente por otro usuario (Sad Path / Colisión en Tiempo Real)**
- **Dado** que un cliente ha seleccionado un bloque horario para un podólogo
- **Y** antes de confirmar, dicho bloque horario es reservado y bloqueado por otro proceso en tiempo real
- **Cuando** el cliente intenta confirmar la reserva
- **Entonces** el sistema valida nuevamente la disponibilidad en tiempo real y detecta que el bloque ya no está libre
- **Y** no permite registrar la cita, mostrando un mensaje informando que el horario ya fue ocupado y solicitando elegir un nuevo horario disponible.

## 5. PUNTOS ABIERTOS / DEPENDENCIAS

- **Punto Abierto 1 (Datos Personales Obligatorios):** En el Product Brief y en el Plan del MVP no se definen explícitamente cuáles son los datos personales obligatorios que se le deben solicitar al cliente al momento de agendar (ej. Nombres, Apellidos, Teléfono de WhatsApp, Correo Electrónico, DNI). Es indispensable precisar este conjunto de datos antes de pasar a la fase de diseño de arquitectura y bases de datos.
- **Punto Abierto 2 (Mecanismo de Validación de Disponibilidad en Tiempo Real):** Se requiere definir el mecanismo técnico exacto para verificar y bloquear la disponibilidad en tiempo real (manejo de concurrencia/locks temporales mientras el cliente completa sus datos) asegurando la restricción estricta de no exponer precios ni permitir cruces de agenda en escenarios de alta demanda simultánea.
- **Dependencia:** Esta historia es la base sobre la cual se construirán los eventos de disparo para el envío de Notificaciones por WhatsApp (Épica P2) y la consulta en el Dashboard del Podólogo (Épica P3).

## 6. ORDEN DE DELEGACIÓN PARA EL QA

@QA: La Historia de Usuario Agendamiento de Cita Multiservicio con Selección de Podólogo y Bloqueo de Disponibilidad en Tiempo Real está lista en el archivo hu_01_reserva_citas.md. Por favor, procede con la auditoría documental contra el Product Brief para asegurar que la historia cumple con los requerimientos originales.
