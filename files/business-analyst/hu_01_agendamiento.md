## 1. HISTORIA DE USUARIO

- **Épica:** Motor Inteligente de Reservas y Gestión de Disponibilidad
- **Título de la HU:** Agendamiento de cita podológica con cálculo acumulativo de tiempo y bloqueo de disponibilidad

> **Como** cliente del spá podológico
> **Quiero** seleccionar uno o múltiples servicios podológicos y un profesional de preferencia para agendar una cita en un horario disponible considerando la duración total calculada
> **Para** asegurar mi reserva de atención sin solapamientos ni cruces de agenda con otros clientes

## 2. ALCANCE ESPECÍFICO (SCOPE)

- **Incluye:**
  - Selección de uno o más servicios podológicos disponibles en el catálogo del spa.
  - Selección de un podólogo de preferencia para la atención.
  - Cálculo acumulativo automático de la duración total esperada de la cita mediante la suma de las duraciones de los servicios seleccionados.
  - Consulta y validación en tiempo real de los bloques horarios donde el podólogo seleccionado cuenta con disponibilidad continua suficiente.
  - Bloqueo inmediato en la agenda del podólogo del rango de tiempo total al ser confirmada la reserva por el cliente.
- **NO Incluye:**
  - Formulario y captura de datos personales específicos del cliente (identificado como Punto Abierto debido a la ausencia de definición en el Product Brief / PRD).
  - Gestión y configuración de turnos de trabajo, pausas/descansos o días festivos de los podólogos (identificado como Punto Abierto por falta de especificación en el PRD).
  - Envío automatizado de mensajes/notificaciones por WhatsApp al cliente o podólogo (perteneciente a la Épica P3: Sistema de Notificaciones Automatizadas por WhatsApp).
  - Funcionalidad de anulación o modificación de citas por parte del cliente o podólogo (perteneciente a la Épica P2: Gestión de Citas y Anulaciones).
  - Procesamiento o cobro de pagos online.

## 3. REGLAS DE NEGOCIO

- **RN-01:** La duración total requerida para la reserva se calculará automáticamente mediante la suma aritmética exacta de las duraciones individuales de cada servicio seleccionado por el cliente.
- **RN-02:** El sistema únicamente presentará al cliente aquellos bloques de inicio de cita que garanticen disponibilidad continua e ininterrumpida del podólogo seleccionado durante toda la duración acumulada calculada.
- **RN-03:** Al confirmar una reserva, el sistema debe registrar el bloqueo del intervalo de tiempo en la agenda del podólogo en tiempo real, garantizando que el podólogo no esté disponible para otras reservas en ese mismo período (0% solapamientos).
- **RN-04:** No se permitirá la selección de fechas u horarios pasados ni fuera del rango operativo habilitado del spa.

## 4. CRITERIOS DE ACEPTACIÓN (Gherkin BDD)

**Escenario 1: Agendamiento exitoso con cálculo acumulativo de tiempo y bloqueo de agenda (Happy Path)**
- **Dado** que el cliente se encuentra en la pantalla de reservas del spa
- **Y** ha seleccionado 2 servicios podológicos cuya suma de duraciones equivale a 75 minutos (servicio A de 30 min y servicio B de 45 min)
- **Y** ha seleccionado a un podólogo de su preferencia
- **Cuando** el cliente solicita consultar los horarios disponibles para una fecha seleccionada
- **Entonces** el sistema calcula la duración total de 75 minutos y muestra únicamente las horas de inicio donde el podólogo elegido tiene un bloque continuo de 75 minutos libres
- **Y** cuando el cliente confirma la reserva en un horario de inicio disponible, el sistema bloquea los 75 minutos continuos en la agenda del podólogo de forma inmediata.

**Escenario 2: Descarte de horarios por tiempo continuo insuficiente (Sad Path)**
- **Dado** que el cliente ha seleccionado servicios podológicos con un tiempo acumulado de 60 minutos
- **Y** el podólogo elegido tiene una cita agendada previamente a las 10:30 AM
- **Cuando** el cliente consulta la disponibilidad para esa fecha
- **Entonces** el sistema no muestra el horario de las 10:00 AM como opción disponible por disponer únicamente de un espacio libre de 30 minutos antes del siguiente compromiso del podólogo.

**Escenario 3: Prevención de cruces por concurrencia simultánea en tiempo real (Sad Path)**
- **Dado** que dos clientes intentan reservar el mismo horario y podólogo de manera simultánea
- **Cuando** el primer cliente completa y confirma la reserva exitosamente
- **Entonces** el sistema bloquea de inmediato el bloque horario seleccionado en la agenda del podólogo
- **Y** cuando el segundo cliente intenta confirmar en ese mismo instante, el sistema rechaza la solicitud indicando que el horario ya no se encuentra disponible y solicita seleccionar un nuevo horario.

## 5. PUNTOS ABIERTOS / DEPENDENCIAS

- **PA-01 (Ambigüedad en Datos Personales Obligatorios del Cliente):** El Product Brief / PRD no define la lista exacta de campos o datos personales obligatorios que deben solicitarse y capturarse del cliente al concretar la reserva (ej. Nombre completo, Teléfono/WhatsApp, Correo electrónico, DNI, notas/afecciones médicas). Se requiere definición de negocio para proceder con el diseño del formulario de captura en fases posteriores.
- **PA-02 (Ambigüedad en Gestión de Turnos y Pausas del Podólogo):** El Product Brief / PRD no especifica el mecanismo de configuración de la jornada laboral de los profesionales (turnos, descansos, pausas de almuerzo, días libres y festivos). Esto es crítico para determinar los bloques horarios hábiles sobre los cuales el algoritmo de disponibilidad debe aplicar las reglas de bloqueo.
- **PA-03 (Dependencia de Notificaciones WhatsApp):** La confirmación final hacia el usuario depende de la integración futura con el módulo de notificaciones automatizadas por WhatsApp (Épica P3).

## 6. ORDEN DE DELEGACIÓN PARA EL QA

@QA: La Historia de Usuario Agendamiento de cita podológica con cálculo acumulativo de tiempo y bloqueo de disponibilidad está lista en el archivo hu_01_agendamiento.md. Por favor, procede con la auditoría documental contra el Product Brief para asegurar que la historia cumple con los requerimientos originales.
