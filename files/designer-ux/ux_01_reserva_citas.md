# ESPECIFICACIÓN DE DISEÑO DE INTERFAZ Y WIREFRAMES ESTRUCTURALES

- **Historia Base:** Agendamiento de Cita Multiservicio con Selección de Podólogo y Bloqueo de Disponibilidad en Tiempo Real (`hu_01_reserva_citas.md`)
- **Enfoque de Usabilidad:** Se prioriza una experiencia limpia sin fricción financiera (0% exposición de precios), agrupando el cálculo automático de duración acumulada y filtrando únicamente los bloques de disponibilidad continua en tiempo real para evitar cualquier sobreposición de agenda.

---

## 1. RESUMEN DE DISEÑO

- **Historia Base:** Agendamiento de Cita Multiservicio con Selección de Podólogo y Bloqueo de Disponibilidad en Tiempo Real
- **Enfoque de Usabilidad:** Flujo intuitivo de 2 pasos orientado a la salud podológica. Se omite de forma estricta todo elemento de precio/tarifa y se ofrece visibilidad dinámica de la duración total acumulada de la cita con filtrado de bloques horarios continuos en tiempo real.

---

## 2. MAPA DE ESTADOS VISUALES

### Estado 1: Selección de Servicios, Podólogo y Disponibilidad Continua (Happy Path - Escenario 1)

**Escenario cubierto:** Criterio de Aceptación 1 - Agendamiento exitoso de cita multiservicio con podólogo seleccionado.

[ARTEFACTO VISUAL: Proyecto Stitch ID `18038142429351834781` - Pantalla `048b429b30c540b9b463eedd27bd5079`]

```text
+-----------------------------------------------------------------------+
|  <-  Aura Podiatry & Foot Clinic                  Paso 1 de 2: Cita  |
+-----------------------------------------------------------------------+
|  [!] DURACIÓN TOTAL ACUMULADA: 75 min (2 servicios seleccionados)      |
+-----------------------------------------------------------------------+
| SELECCIONA TUS SERVICIOS PODOLÓGICOS (Sin Precios):                  |
|                                                                       |
|  [X] Evaluación Podológica Completa & Pisada      (45 min)           |
|      Análisis biomecano-postural y escaneo 3D.                        |
|                                                                       |
|  [X] Profilaxis Podológica Integral               (30 min)           |
|      Corte clínico, profilaxis de uñas y limpieza profunda.           |
|                                                                       |
|  [ ] Tratamiento Láser para Onicomicosis          (40 min)           |
|      Sesión terapéutica láser para uñas con micosis.                  |
+-----------------------------------------------------------------------+
| SELECCIONA TU PODÓLOGO DE PREFERENCIA:                                |
|                                                                       |
|  (o) Dra. Elena Vance - Podóloga Senior (Disp. Hoy) [SELECCIONADO]     |
|  ( ) Dr. Marcus Thorne - Especialista en Pie Diabético                |
|  ( ) Cualquier Profesional Disponible (Asignación rápida)              |
+-----------------------------------------------------------------------+
| DISPONIBILIDAD DE HORARIOS CONTINUOS (Mínimo 75 min continuos):       |
| Fecha: [ 15 Sep 2026 v ]                                              |
| Lapsos disponibles para Dra. Elena Vance (75 min seguidos libres):    |
|   [ 09:00 AM - 10:15 AM ]      [ 11:30 AM - 12:45 PM ]                |
|   [ 03:00 PM - 04:15 PM ]                                             |
+-----------------------------------------------------------------------+
| DATOS DE LA RESERVA:                                                  |
| Nombre Completo: [ Juan Pérez                         ]               |
| WhatsApp / Tel.: [ +51 987654321                      ]               |
| Email:           [ juan.perez@email.com               ]               |
+-----------------------------------------------------------------------+
|                              [ CONFIRMAR Y AGENDAR RESERVA (75 min) ] |
+-----------------------------------------------------------------------+
```

**Nota de Interfaz:** El botón principal se mantiene deshabilitado hasta que la suma de tiempo del servicio seleccionado encuentre un rango consecutivo válido y los datos requeridos (Nombre, WhatsApp, Email) estén completados. No se muestra ningún costo o tarifa.

---

### Estado 2: Intento de Agendamiento en Fecha/Podólogo sin Disponibilidad Continua (Sad Path - Escenario 2)

**Escenario cubierto:** Criterio de Aceptación 2 - Lapsos discontinuos o menores a la duración total acumulada.

```text
+-----------------------------------------------------------------------+
|  <-  Aura Podiatry & Foot Clinic                                      |
+-----------------------------------------------------------------------+
|  Duración Acumulada Seleccionada: 60 min                              |
|  Podólogo Seleccionado: Dr. Marcus Thorne                             |
|  Fecha Seleccionada: 16 Sep 2026                                      |
+-----------------------------------------------------------------------+
|                                                                       |
|    +-------------------------------------------------------------+    |
|    | (i) NO HAY DISPONIBILIDAD CONTINUA SUFICIENTE               |    |
|    |                                                             |    |
|    | El Dr. Marcus Thorne no dispone de un bloque continuo de    |    |
|    | 60 minutos libres en la fecha seleccionada (16 Sep 2026).   |    |
|    |                                                             |    |
|    | Sugerencias para continuar tu reserva:                      |    |
|    |  1. Seleccionar otra fecha en el calendario.               |    |
|    |  2. Elegir la opción "Cualquier Profesional Disponible".    |    |
|    |  3. Reajustar los servicios seleccionados.                  |    |
|    |                                                             |    |
|    | [ CAMBIAR FECHA ]       [ CAMBIAR DE PODÓLOGO / CUALQUIERA ]|    |
|    +-------------------------------------------------------------+    |
|                                                                       |
+-----------------------------------------------------------------------+
```

**Nota de Interfaz:** El sistema oculta automáticamente los huecos de agenda que no cumplan con el requisito de tiempo continuo `T_total <= T_disponible_continuo` y despliega la tarjeta de aviso informativo impidiendo la selección de bloques parciales.

---

### Estado 3: Colisión de Reserva en Tiempo Real / Horario Ocupado Simultáneamente (Sad Path - Escenario 3)

**Escenario cubierto:** Criterio de Aceptación 3 - Ocupación simultánea por otro usuario antes de la confirmación.

```text
+-----------------------------------------------------------------------+
|                                                                       |
|  +-----------------------------------------------------------------+  |
|  | [!] HORARIO YA NO DISPONIBLE (COLISIÓN EN TIEMPO REAL)          |  |
|  |                                                                 |  |
|  | El bloque horario [09:00 AM - 10:15 AM] para la Dra. Elena Vance|  |
|  | acaba de ser reservado por otro paciente hace unos momentos.    |  |
|  |                                                                 |  |
|  | Para evitar sobreposiciones de cita, por favor selecciona un    |  |
|  | nuevo horario disponible actualizado en tiempo real:           |  |
|  |                                                                 |  |
|  |  Horarios libres actualizados para el 15 Sep 2026:            |  |
|  |   [ 11:30 AM - 12:45 PM ]      [ 03:00 PM - 04:15 PM ]          |  |
|  |                                                                 |  |
|  |                              [ SELECCIONAR NUEVO HORARIO ]      |  |
|  +-----------------------------------------------------------------+  |
|                                                                       |
+-----------------------------------------------------------------------+
```

**Nota de Interfaz:** Modal o alerta bloqueante que se dispara al enviar la solicitud si el backend rechaza el lock por concurrencia. Limpia la selección previa y fuerza al cliente a seleccionar un nuevo slot libre sin perder sus servicios elegidos ni sus datos personales.

---

## 3. DECISIONES DE DISEÑO Y PUNTOS PENDIENTES

- **Heurísticas aplicadas:**
  1. *Visibilidad del Estado del Sistema:* Muestra de forma destacada en la parte superior el tiempo total acumulado de la cita (ej. `75 min`) a medida que se marcan/desmarcan servicios.
  2. *Prevención de Errores:* Filtrado estricto en UI de los botones de horario; solo se renderizan como activos los intervalos que cuentan con la duración contigua requerida.
  3. *Restricción de Negocio Cumplida (RN-02):* Absoluta ausencia de etiquetas de precio, divisas, costos o subtotales en todas las pantallas y modales.
- **Bloqueos o Consultas (Puntos Abiertos de la HU):**
  - **Datos Personales Obligatorios:** Se diseñó el formulario base solicitando: *Nombre Completo*, *Teléfono/WhatsApp* y *Email*. Se requiere confirmación final del BA para validar si se requiere algún campo adicional (ej. DNI o Documento de Identidad).
  - **Mecanismo de Lock Temporal:** Se recomienda implementar un lock temporal en backend (ej. 5 minutos) en cuanto el usuario selecciona el horario para reducir la tasa de colisión observada en el Escenario 3.

---

## 4. ORDEN DE DELEGACIÓN PARA EL TRACKER

@HUMANO: Los wireframes funcionales para la Historia de Usuario Agendamiento de Cita Multiservicio con Selección de Podólogo y Bloqueo de Disponibilidad en Tiempo Real están listos. Puedes encontrar la estructura de UI y los IDs de Stitch en el archivo ux_01_reserva_citas.md. El requerimiento está listo para el diseño de arquitectura y base de datos.
