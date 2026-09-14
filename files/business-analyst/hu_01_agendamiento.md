# ESPECIFICACIÓN DE HISTORIA DE USUARIO

## 1. HISTORIA DE USUARIO

- **Épica:** Motor de Reservas Inteligente y Control de Disponibilidad
- **Título de la HU:** Agendamiento de Cita y Control de Disponibilidad Inteligente

> **Como** Cliente del Spá Podológico Ámely  
> **Quiero** seleccionar uno o varios servicios y a mi podólogo de preferencia para agendar una cita en un bloque horario libre  
> **Para** asegurar mi atención podológica personalizada en tiempo real sin riesgo de cruces ni superposiciones de horario.

## 2. ALCANCE ESPECÍFICO (SCOPE)

- **Incluye:**
  - Selección de uno o varios servicios podológicos para una misma reserva.
  - Selección del profesional podólogo de preferencia dentro de la plantilla disponible.
  - Cálculo automático en tiempo real del tiempo total estimado de atención mediante la suma acumulativa de las duraciones de los servicios elegidos.
  - Despliegue dinámico de bloques horarios libres en la agenda del podólogo seleccionado acorde a la duración total calculada.
  - Bloqueo y registro de la reserva en el bloque horario continuo elegido por el cliente, garantizando la prevención de superposiciones.
  - Confirmación en pantalla del registro exitoso de la cita con resumen del agendamiento.

- **NO Incluye:**
  - Envío automático de notificaciones de confirmación por WhatsApp (pertenece a la Épica P2: Sistema de Notificaciones Instantáneas y Anulación por WhatsApp).
  - Proceso de cancelación o anulación de citas por parte del cliente o podólogo (pertenece a la Épica P2).
  - Despliegue de precios, tarifas o costos de los servicios (restringido por la Restricción Comercial de Precios).
  - Gestión o visualización de la agenda operativa desde el perfil del podólogo (pertenece a la Épica P3: Panel de Gestión de Citas para Profesionales).
  - Navegación e interfaz institucional del catálogo comercial o vitrina (pertenece a la Épica P4: Vitrina Digital).

## 3. REGLAS DE NEGOCIO

- **RN-01 (Cálculo Acumulativo de Duración):** El tiempo total requerido para la reserva se calculará sumando exactamente la duración en minutos de todos los servicios seleccionados.
- **RN-02 (Validación de Disponibilidad Contigua):** Un bloque horario solo se mostrará habilitado si el podólogo seleccionado cuenta con disponibilidad continua e ininterrumpida equivalente o superior a la duración total calculada.
- **RN-03 (Bloqueo Exclusivo y Anti-superposición):** Al confirmar el agendamiento, el sistema debe bloquear de inmediato el rango de tiempo completo en la agenda del podólogo, impidiendo que ese mismo intervalo sea seleccionado para otra cita.
- **RN-04 (Ocultación Estricta de Tarifas):** Ninguna pantalla ni flujo del proceso de reserva expondrá valores monetarios o costos asociados a los tratamientos.
- **RN-05 (Indivisibilidad de la Atención):** Todos los servicios de una reserva combinada se programan en una sesión única y continua con el mismo podólogo seleccionado.

## 4. CRITERIOS DE ACEPTACIÓN (Gherkin BDD)

**Escenario 1: Agendamiento de servicio único en bloque horario disponible (Happy Path)**
- **Dado** que el cliente se encuentra en el motor de reservas y ha seleccionado un servicio de duración 45 minutos
- **Y** ha elegido al podólogo de su preferencia
- **Cuando** consulta la agenda del podólogo para una fecha determinada
- **Entonces** el sistema calcula una duración total de 45 minutos y despliega únicamente los bloques horarios con al menos 45 minutos continuos libres
- **Y** al seleccionar un bloque libre y confirmar, el sistema registra la cita y bloquea el rango horario en la agenda del podólogo impidiendo superposiciones.

**Escenario 2: Agendamiento de múltiples servicios combinados con cálculo acumulativo (Happy Path)**
- **Dado** que el cliente selecciona dos servicios podológicos (Servicio A de 30 min y Servicio B de 45 min)
- **Y** selecciona un podólogo específico
- **Cuando** avanza a la selección de horario
- **Entonces** el sistema calcula automáticamente la duración total acumulada de 75 minutos (1 hora y 15 minutos)
- **Y** muestra únicamente los bloques de disponibilidad contigua de 75 minutos libres en la agenda del podólogo para la fecha seleccionada.

**Escenario 3: Bloqueo de horarios con tiempo insuficiente o superposición (Sad Path)**
- **Dado** que el cliente ha seleccionado servicios que suman una duración total de 60 minutos
- **Y** el podólogo seleccionado solo tiene una ventana disponible de 30 minutos entre dos citas previamente agendadas
- **Cuando** el cliente visualiza la disponibilidad para esa fecha
- **Entonces** el sistema inhabilita y no permite seleccionar dicho bloque de 30 minutos por no cumplir con el tiempo continuo requerido
- **Y** sugiere únicamente los intervalos donde existan 60 minutos contiguos disponibles.

**Escenario 4: Intento de reserva simultánea en horario previamente bloqueado (Sad Path)**
- **Dado** que un cliente X inicia el proceso para agendar a las 10:00 AM con un podólogo específico
- **Y** otro cliente Y confirma una reserva con el mismo podólogo para el rango de 10:00 AM a 11:00 AM un instante antes
- **Cuando** el cliente X intenta confirmar su reserva en el mismo horario
- **Entonces** el sistema rechaza la confirmación, notifica que el horario ya no se encuentra disponible y actualiza la lista de horarios libres.

## 5. PUNTOS ABIERTOS / DEPENDENCIAS

- **PA-01 (Modelo de Acceso del Cliente):** No se especifica en el PRD si la gestión o anulación requerirá creación/autenticación de cuenta de usuario o si la gestión posterior se basará en un enlace/token único enviado vía WhatsApp.
- **PA-02 (Horarios de Atención y Turnos Podológicos):** No se han definido los horarios generales de operación del spá ni las franjas horarias, turnos o descansos individuales de cada podólogo para configurar las reglas del motor de disponibilidad.
- **PA-03 (Ventanas de Anticipación para Reservas):** El PRD no establece el tiempo mínimo de anticipación (ej. agendar con al menos 2 horas de previdencia) ni la ventana máxima futura (ej. hasta 30 días antes) para permitir una reserva.
- **DEP-01 (Catálogo de Servicios y Duraciones):** Dependencia directa de la entrega parametrizada de la lista oficial de servicios podológicos con sus duraciones estándar asignadas.
