## 1. HISTORIA DE USUARIO

- **Épica:** Motor de Reservas e Integración de Agenda en Tiempo Real
- **Título de la HU:** Agendamiento de cita podológica y reserva de horario en tiempo real

> **Como** Cliente del Spa Podológico
> **Quiero** seleccionar el servicio podológico o combinación de servicios, el podólogo de mi preferencia y un horario disponible en tiempo real
> **Para** asegurar la reserva continua de mi atención sin sufrir cruces o solapamientos con otras citas

## 2. ALCANCE ESPECÍFICO (SCOPE)

- **Incluye:**
  - Selección de uno o más servicios podológicos de la oferta del spa.
  - Selección del podólogo de preferencia.
  - Cálculo de la duración total continua mediante la suma simple de los tiempos promedio de cada servicio seleccionado.
  - Consulta y despliegue de slots de horarios continuos disponibles en la agenda del podólogo seleccionado dentro de su jornada laboral.
  - Bloqueo y reserva del rango de tiempo seleccionado para evitar solapamientos (0% cruces de agenda).
  - Confirmación de la reserva del horario elegido en el sistema.

- **NO Incluye:**
  - Creación de cuenta, inicio de sesión o mecanismo específico de autenticación del cliente (declarado como punto abierto).
  - Envío automático de notificaciones vía WhatsApp (corresponde a la Épica [P3] de Notificaciones Automáticas por WhatsApp).
  - Procesamiento o cobro de pagos en línea (por restricción del negocio los precios están ocultos al público).
  - Lógica de anulación o cancelación de la cita por parte del cliente (corresponde a la Épica [P4] Módulo de Anulación de Citas por el Cliente).
  - Configuración o edición de horarios de podólogos y catálogo de servicios (módulo administrativo no incluido en este alcance).

## 3. REGLAS DE NEGOCIO

- **RN-01:** La duración total de la cita se calcula sumando de forma continua los tiempos promedio de cada servicio individual seleccionado.
- **RN-02:** El sistema no debe permitir la reserva ni superposición de citas en horarios previamente ocupados por el mismo podólogo (0% solapamientos).
- **RN-03:** Los bloques de horarios disponibles generados deben acomodar de manera estricta y continua la duración total calculada dentro de la jornada laboral del podólogo seleccionado.
- **RN-04:** La reserva debe omitir cualquier visualización de precio o tarifa, mostrando únicamente la duración total estimada de la atención.

## 4. CRITERIOS DE ACEPTACIÓN (Gherkin BDD)

**Escenario 1: Agendamiento exitoso de cita podológica continua (Happy Path)**
- **Dado** que el cliente ha seleccionado uno o más servicios podológicos y un podólogo de su preferencia
- **Y** la suma de los tiempos promedio de los servicios da una duración total N minutos
- **Cuando** el cliente consulta la disponibilidad y selecciona un bloque continuo de N minutos libre en la agenda del podólogo
- **Entonces** el sistema valida en tiempo real que no existen solapamientos y bloquea el horario seleccionado
- **Y** el sistema confirma el registro de la reserva registrando la cita en la agenda del podólogo

**Escenario 2: Intentar reservar un horario no disponible o en solapamiento (Sad Path / Conflicto de Disponibilidad)**
- **Dado** que un podólogo ya tiene una cita agendada en un rango de tiempo determinado
- **Cuando** otro cliente intenta confirmar una reserva que coincide total o parcialmente con dicho rango de tiempo para el mismo podólogo
- **Entonces** el sistema rechaza la reserva indicando que el horario ya no se encuentra disponible
- **Y** el sistema solicita al cliente seleccionar un nuevo horario disponible

**Escenario 3: Duración requerida excede la disponibilidad continua disponible (Sad Path / Tiempo Insuficiente)**
- **Dado** que la duración total calculada de los servicios seleccionados es de N minutos
- **Cuando** el cliente busca un horario para un podólogo cuya ventana de tiempo libre disponible antes del fin de su jornada es menor a N minutos
- **Entonces** el sistema no muestra dicho bloque como disponible para selección

## 5. PUNTOS ABIERTOS / DEPENDENCIAS

- **Mecanismo de Identificación y Autenticación del Cliente:** El PRD/Product Brief no define la forma ni las reglas para identificar al cliente al momento de agendar la cita (ej. si requiere registro previa con usuario y contraseña, o solo el ingreso de datos básicos como Nombre, Teléfono y DNI). Se declara como Punto Abierto para definición estratégica y de arquitectura.
- **Margen de Desinfección / Descanso entre Citas:** El PRD no especifica si se debe adicionar un tiempo de buffer automático (ej. 10 u 15 minutos) entre citas consecutivas para desinfección de instrumental o descanso del podólogo.
- **Límite de Anticipación para Reservas:** No se especifica con cuánta anticipación mínima o máxima un cliente puede agendar una cita.

## 6. ORDEN DE DELEGACIÓN PARA EL QA

@QA: La Historia de Usuario Agendamiento de cita podológica y reserva de horario en tiempo real está lista en el archivo hu_01_agendamiento.md. Por favor, procede con la auditoría documental contra el Product Brief para asegurar que la historia cumple con los requerimientos originales.
