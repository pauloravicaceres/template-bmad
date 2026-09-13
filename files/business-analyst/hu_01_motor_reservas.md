## 1. HISTORIA DE USUARIO

- **Épica:** Motor Inteligente de Reservas y Agenda Dinámica
- **Título de la HU:** Agendamiento dinámico de citas podológicas multilista

> **Como** cliente final del spá podológico
> **Quiero** seleccionar uno o varios servicios y agendar una cita consultando la disponibilidad en tiempo real
> **Para** asegurar un bloque continuo de atención con un podólogo sin generar cruces de agenda y sin visualizar precios

## 2. ALCANCE ESPECÍFICO (SCOPE)

- **Incluye:**
  - Selección multilista de uno o varios servicios podológicos ofrecidos en el catálogo digital.
  - Cálculo automático de la duración total acumulada sumando los tiempos promedio de atención de los servicios seleccionados.
  - Opción de seleccionar un podólogo de preferencia o continuar sin selección explícita.
  - Consulta y validación de disponibilidad en tiempo real en la agenda del podólogo (individual o consolidada).
  - Bloqueo inmediato e ininterrumpido del intervalo de tiempo continuo acumulado correspondiente a la duración total calculada.
  - Manejo de concurrencia para evitar solapamientos simultáneos en la misma franja horaria.
  - Ocultamiento estricto de precios y montos monetarios en todo el flujo de agendamiento.
- **NO Incluye:**
  - Visualización, desglose o cálculo de precios o tarifas de servicios.
  - Envío automático de notificaciones por WhatsApp a clientes o podólogos (corresponde a la Épica P2).
  - Interfaz del Portal del Profesional para consulta o actualización del estado de citas (corresponde a la Épica P3).
  - Solicitud de anulación o reprogramación de citas agendadas por parte del cliente (corresponde a la Épica P4).
  - Administración o edición del catálogo de servicios y perfiles del staff (corresponde a la Épica P5).

## 3. REGLAS DE NEGOCIO

- **RN-01:** (Estrategia Comercial de Precios) Los precios de los servicios no deben ser visibles para el cliente en ninguna fase de la selección o agendamiento.
- **RN-02:** (Duración Acumulada Continuada) La duración total requerida para la cita es equivalente a la suma de las duraciones estándar de cada servicio seleccionado en la modalidad multilista.
- **RN-03:** (Bloque Ininterrumpido de Agenda) El sistema exige y valida un intervalo continuo de tiempo libre en la agenda que cubra íntegramente la duración total acumulada.
- **RN-04:** (Prevención de Solapamiento y Concurrencia) Queda estrictamente prohibido permitir reservas en intervalos de tiempo que se solapen con citas previamente confirmadas o en proceso de reserva simultánea en la agenda del podólogo.
- **RN-05:** (Preferencia de Profesional) El sistema permite al cliente seleccionar un podólogo específico o no seleccionar ninguno.
- **RN-06:** (Selección Mínima Obligatoria) Todo agendamiento requiere la selección previa de al menos un servicio del catálogo para poder calcular la duración total e iniciar la consulta de disponibilidad.

## 4. CRITERIOS DE ACEPTACIÓN (Gherkin BDD)

**Escenario 1: Agendamiento exitoso multilista con podólogo seleccionado (Happy Path)**
- **Dado** que el cliente ha seleccionado uno o varios servicios podológicos del catálogo (que muestran únicamente su tiempo promedio de atención)
- **Y** ha elegido explícitamente un podólogo de su preferencia
- **Cuando** el cliente consulta y selecciona una fecha y un horario disponible en tiempo real
- **Entonces** el sistema valida que el podólogo seleccionado cuenta con disponibilidad continua para la duración total acumulada
- **Y** el sistema reserva la cita bloqueando el intervalo completo en la agenda del podólogo sin mostrar precios en pantalla.

**Escenario 2: Agendamiento exitoso multilista sin podólogo de preferencia seleccionado (Happy Path / Cobertura RN-05)**
- **Dado** que el cliente ha seleccionado uno o varios servicios podológicos del catálogo
- **Y** ha optado por no elegir un podólogo de preferencia ("Cualquier podólogo disponible")
- **Cuando** el cliente consulta y selecciona una fecha y horario disponible en tiempo real
- **Entonces** el sistema evalúa la disponibilidad de bloques continuos entre el staff de podólogos
- **Y** el sistema reserva la cita asignando el intervalo continuo al podólogo disponible y bloqueando la agenda sin mostrar precios en pantalla.

**Escenario 3: Intento de agendamiento en horario sin disponibilidad continua (Sad Path)**
- **Dado** que el cliente ha seleccionado un conjunto de servicios con una duración total acumulada determinada
- **Y** ha seleccionado un podólogo de preferencia
- **Cuando** el cliente intenta reservar en un horario donde el podólogo presenta un cruce de agenda o el bloque libre continuo es menor al tiempo total acumulado
- **Entonces** el sistema rechaza la reserva para esa franja horaria
- **Y** el sistema notifica que el horario no está disponible sin realizar modificaciones en la agenda.

**Escenario 4: Intento de agendamiento sin seleccionar servicios / Selección nula (Sad Path / Cobertura RN-06)**
- **Dado** que el cliente se encuentra en el módulo de agendamiento de citas
- **Y** no ha seleccionado ningún servicio podológico del catálogo (lista vacía)
- **Cuando** el cliente intenta avanzar hacia la selección de fecha, hora o confirmación
- **Entonces** el sistema impide el avance en el flujo
- **Y** muestra un aviso requerir la selección de al menos un servicio para determinar la duración de la cita.

**Escenario 5: Reserva concurrente simultánea de la misma franja horaria (Sad Path / Concurrencia)**
- **Dado** que dos clientes intentan reservar simultáneamente la misma franja horaria continua de un podólogo
- **Cuando** ambos clientes envían la confirmación de reserva al mismo instante
- **Entonces** el sistema confirma exitosamente la primera solicitud recibida bloqueando la agenda del podólogo
- **Y** rechaza de inmediato la segunda solicitud informando al usuario que la franja horaria ha dejado de estar disponible, garantizando el 0% de solapamiento.

**Escenario 6: Verificación de no visualización de precios durante la transacción (Regla de Negocio / Happy Path)**
- **Dado** que el cliente se encuentra en el flujo de selección multilista y confirmación de la cita
- **Cuando** revisa el resumen de los servicios seleccionados y la fecha/hora elegida
- **Entonces** el sistema muestra únicamente los nombres de los servicios, el tiempo total de atención estimado y los detalles del agendamiento
- **Y** en ninguna parte de la pantalla o resumen se muestra ningún costo, tarifa o monto monetario.

## 5. PUNTOS ABIERTOS / DEPENDENCIAS

- **Punto Abierto 1 (Mecanismo de Asignación por Defecto del Podólogo):** El Product Brief y PRD no establecen el criterio o regla de negocio para asignar automáticamente un podólogo cuando el cliente no selecciona uno de preferencia (ej. asignación automática por primer podólogo disponible en la franja horaria o distribución equitativa por rotación del staff). Se declara explícitamente como ambigüedad abierta a definir por el negocio antes de la fase de arquitectura/construcción.
- **Punto Abierto 2 (Mecanismo de Validación en Tiempo Real del Bloque Continuo sin Precios):** No se detalla la lógica exacta de presentación y consolidación de franjas horarias disponibles multilista cuando no se selecciona un podólogo (si se deben consolidar y mostrar todos los bloques continuos libres entre todo el staff disponible sin mostrar tarifas ni precios).
- **Punto Abierto 3 (Identificación / Autenticación del Cliente):** El PRD no define si la confirmación de la reserva requiere inicio de sesión con cuenta/contraseña o la captura de datos mínimos de contacto (nombre y número de WhatsApp) para el despacho de notificaciones.
