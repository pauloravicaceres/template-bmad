# ESPECIFICACIÓN DE DISEÑO UX Y WIREFRAMES ESTRUCTURALES

## 1. RESUMEN DE DISEÑO

- **Historia Base:** Agendamiento de Cita y Control de Disponibilidad Inteligente (`hu_01_agendamiento.md`)
- **Enfoque de Usabilidad:** Flujo guiado de reserva podológica sin fricción comercial (ocultación estricta de tarifas). Se prioriza la selección modular de servicios, cálculo dinámico acumulativo de duración total en minutos/horas, filtrado automático e inhabilitación en tiempo real de bloques horarios sin tiempo continuo suficiente, y manejo resiliente frente a colisiones por reservas en paralelo.

---

## 2. MAPA DE ESTADOS VISUALES

### Estado 1: Selección de Servicios y Podólogo con Cálculo Acumulativo (Happy Path - Escenarios 1 y 2)

**Escenario cubierto:** Escenario 1 y Escenario 2 (Selección de servicio único o múltiple con cálculo dinámico de duración y habilitación de franjas continuas correspondientes).

```text
+-----------------------------------------------------------------------+
|  Spá Podológico Ámely | Reserva de Cita Podológica                   |
+-----------------------------------------------------------------------+
|  PASO 1: SELECCIÓN DE SERVICIOS Y PROFESIONAL                         |
+-----------------------------------------------------------------------+
|  [x] Servicio A: Profilaxis Podológica Integral        (Duración: 45m)|
|  [x] Servicio B: Tratamiento de Onicomicosis Laser    (Duración: 30m)|
|  [ ] Servicio C: Eval. Biomecánica y Plantillas       (Duración: 60m)|
|                                                                       |
|  -------------------------------------------------------------------  |
|  RESUMEN DE DURACIÓN CALCULADA:                                       |
|  [i] Tiempo Total Estimado: 75 min (1h 15min) [RN-01]                 |
|  -------------------------------------------------------------------  |
|                                                                       |
|  SELECCIONE SU PODÓLOGO DE PREFERENCIA:                               |
|  (o) Dra. Valeria Mendoza (Podóloga Specialist)                       |
|  ( ) Lic. Carlos Ramírez (Podólogo Clínico)                           |
|                                                                       |
|  SELECCIONE FECHA: [ 15 / 10 / 2026 ] [📅]                            |
|                                                                       |
|  HORARIOS DISPONIBLES (Bloques contiguos libres >= 75 min):           |
|  +-------------------+  +-------------------+  +-------------------+  |
|  |  09:00 AM - 10:15 |  |  11:30 AM - 12:45 |  |  04:00 PM - 05:15 |  |
|  |     [SELECCIONAR] |  |     [SELECCIONAR] |  |     [SELECCIONAR] |  |
|  +-------------------+  +-------------------+  +-------------------+  |
|                                                                       |
|                                            [ CONFIRMAR AGENDAMIENTO ] |
+-----------------------------------------------------------------------+
```

**Nota de Interfaz:** El botón principal `[ CONFIRMAR AGENDAMIENTO ]` permanece deshabilitado hasta que el usuario seleccione al menos 1 servicio, 1 podólogo y 1 bloque horario válido libre. De acuerdo con RN-04, no se despliega ninguna información de precio ni tarifa.

---

### Estado 2: Restricción e Inhabilitación de Bloques Incalculables o Insuficientes (Sad Path - Escenario 3)

**Escenario cubierto:** Escenario 3 (Duración total requerida supera el tiempo continuo disponible entre citas previas del podólogo).

```text
+-----------------------------------------------------------------------+
|  Spá Podológico Ámely | Reserva de Cita Podológica                   |
+-----------------------------------------------------------------------+
|  RESUMEN DE DURACIÓN CALCULADA:                                       |
|  [i] Tiempo Total Requerido: 60 min (1 hora)                          |
+-----------------------------------------------------------------------+
|  DISPONIBILIDAD PARA EL PODÓLOGO SELECCIONADO (15/10/2026):           |
|                                                                       |
|  [ 09:00 AM - 10:00 AM ] -> [ SELECCIONAR ] (Disponible 60m)          |
|                                                                       |
|  +-----------------------------------------------------------------+  |
|  |  10:30 AM - 11:00 AM (Ventana de 30 min)                          |  |
|  |  [X] NO DISPONIBLE - Tiempo continuo insuficiente (Requiere 60m) |  |
|  |  (Inhabilitado por superposición de agenda previa) [RN-02]       |  |
|  +-----------------------------------------------------------------+  |
|                                                                       |
|  [ 11:30 AM - 12:30 PM ] -> [ SELECCIONAR ] (Disponible 60m)          |
+-----------------------------------------------------------------------+
```

**Nota de Interfaz:** Las franjas horarias con disponibilidad contigua menor al tiempo total calculado se muestran con un estilo grisaceo/deshabilitado y un icono descriptivo indicando que el tiempo libre es insuficiente, sugiriendo únicamente bloques con capacidad completa continuada.

---

### Estado 3: Modal de Conflicto por Reserva Simultánea en Paralelo (Sad Path - Escenario 4)

**Escenario cubierto:** Escenario 4 (Intento de confirmación de reserva en un horario ocupado un instante antes por otro usuario).

```text
+-----------------------------------------------------------------------+
|  Spá Podológico Ámely | Reserva de Cita Podológica                   |
+-----------------------------------------------------------------------+
|  +-----------------------------------------------------------------+  |
|  |  [!] ATENCIÓN: HORARIO NO DISPONIBLE                            |  |
|  |-----------------------------------------------------------------|  |
|  |  Lo sentimos, el bloque horario seleccionado (10:00 AM - 11:00 AM)|  |
|  |  acaba de ser reservado por otro cliente hace un instante.      |  |
|  |                                                                 |  |
|  |  La lista de horarios disponibles ha sido actualizada. Por      |  |
|  |  favor, seleccione una nueva franja horaria para continuar.     |  |
|  |                                                                 |  |
|  |                                      [ ACTUALIZAR Y REINTENTAR ]|  |
|  +-----------------------------------------------------------------+  |
+-----------------------------------------------------------------------+
```

**Nota de Interfaz:** Modal bloqueante que intercepta el intento de confirmación rechazado por la base de datos (RN-03). Al presionar el botón `[ ACTUALIZAR Y REINTENTAR ]`, se vuelve a cargar la matriz de disponibilidad contigua en tiempo real sin perder los servicios previamente seleccionados.

---

## 3. DECISIONES DE DISEÑO Y PUNTOS PENDIENTES

- **Heurísticas aplicadas:**
  - *Visibilidad del estado del sistema:* Muestra de forma destacada el contador dinámico de tiempo acumulado (`Total: 75 min`) al marcar/desmarcar checkboxes de servicios.
  - *Prevención de errores:* Deshabilitación explícita visual de franjas horarias fragmentadas o de menor duración a la requerida.
- **Bloqueos o Consultas (Puntos Abiertos):**
  - **PA-01:** Se requiere definir el método de autenticación/identificación del cliente previo a la confirmación de la cita.
  - **PA-02 & PA-03:** Pendiente la definición de horarios de atención institucionales y ventanas mínimas de anticipación para agendamiento.

---

## 4. ORDEN DE DELEGACIÓN PARA EL TRACKER

@HUMANO: Los wireframes funcionales para la Historia de Usuario Agendamiento de Cita y Control de Disponibilidad Inteligente están listos. Puedes encontrar la estructura de UI y los IDs de Stitch en el archivo ux_01_agendamiento.md. El requerimiento está listo para el diseño de arquitectura y base de datos.
