# ESPECIFICACIÓN DE DISEÑO UX Y WIREFRAMES ESTRUCTURALES

## 1. RESUMEN DE DISEÑO

- **Historia Base:** Selección de servicios, cálculo de duración y reserva de horarios en tiempo real (`hu_01_reserva_disponibilidad.md`)
- **Enfoque de Usabilidad:** Diseño de interfaz asistida en 4 pasos para spa podológico con cálculo automático de duración acumulada para servicios multimodulares, filtrado de bloques continuos de atención, confirmación de cita en tiempo real sin requerir autenticación de usuario ni pagos en línea, y manejo exhaustivo de escenarios Sad Path (solapamientos, concurrencia simultánea, horarios pasados y errores de validación de contacto).

---

## 2. MAPA DE ESTADOS VISUALES

### Estado 1: Reserva Exitosa de Un Servicio con Podólogo Seleccionado (Happy Path)

**Escenario cubierto:** Escenario 1 y Escenario 4 (Perfilado Podológico - 30 min, Dr. Carlos Ruiz, 15 de Septiembre 10:00 - 10:30, cliente Juan Pérez +51987654321, confirmación directa sin credenciales ni pasarela de pago).

- **Stitch Project ID:** `projects/10202567855470565841`
- **Stitch Screen ID:** `projects/10202567855470565841/screens/2936b7a84da54db7a91cf1185c740c78`
- **Artefacto Visual:** Link/ID de Stitch: `2936b7a84da54db7a91cf1185c740c78`

**Nota de Interfaz:** El botón principal de confirmación valida la presencia de Nombre Completo y Teléfono. Al presionar "Confirmar Reserva", el sistema bloquea inmediatamente el turno en la agenda del profesional y despliega la tarjeta de reserva confirmada con el código de comprobante `#POD-2026-89412`, confirmando que el pago se realizará de manera presencial en la clínica.

---

### Estado 2: Reserva Multimodular con Cálculo Automático de Duración Total

**Escenario cubierto:** Escenario 2 (Tratamiento de Uñero 45 min + Masaje Podológico 15 min = 60 min totales, Dra. María López).

- **Stitch Project ID:** `projects/10202567855470565841`
- **Stitch Screen ID:** `projects/10202567855470565841/screens/5480c1f2719c44f3be933fbaaae0206c`
- **Artefacto Visual:** Link/ID de Stitch: `5480c1f2719c44f3be933fbaaae0206c`

**Nota de Interfaz:** El componente de resumen acumula automáticamente los tiempos de los servicios seleccionados (45 min + 15 min = 60 min). La grilla de horarios disponibles filtra y muestra EXCLUSIVAMENTE los bloques de tiempo continuos de 60 minutos ininterrumpidos en la agenda del profesional (ej. 10:00 - 11:00 hs), marcando como no disponibles aquellos intervalos fraccionados.

---

### Estado 3: Manejo de Solapamientos, Horarios Ocupados e Invalidez de Rango Operativo (Sad Paths & RN-01)

**Escenario cubierto:** Escenario 3 (Solapamiento en cita de Dra. María López de 11:00 a 12:00) y Escenario 5 (Bloqueo de horarios en el pasado antes de las 15:00 hs y fuera del rango de atención de 09:00 a 19:00 hs).

**Artefacto Visual:**

```text
+-----------------------------------------------------------------------------------+
| DISPONIBILIDAD DE HORARIOS - Dra. María López (Fecha: 2026-09-15)                 |
+-----------------------------------------------------------------------------------+
|  [ 08:30 - 09:00 ] ✕ Fuera de Horario Operativo (09:00 - 19:00) [DESHABILITADO]   |
|  [ 09:00 - 09:30 ] ✕ Bloque en el Pasado (< 15:00 hs actual)   [OCULTO/DESHAB.]   |
|  [ 10:00 - 10:30 ] ✓ DISPONIBLE                                [SELECCIONABLE]    |
|  [ 11:00 - 11:30 ] ✕ RESERVADO / SOLAPADO                      [BLOQUEADO - ROJO]  |
|  [ 11:30 - 12:00 ] ✕ RESERVADO / SOLAPADO                      [BLOQUEADO - ROJO]  |
|  [ 15:30 - 16:00 ] ✓ DISPONIBLE                                [SELECCIONABLE]    |
|  [ 19:30 - 20:00 ] ✕ Fuera de Horario Operativo                [DESHABILITADO]    |
+-----------------------------------------------------------------------------------+
|  ⚠ Alerta Informativa: "El rango de 11:00 a 12:00 ya no está disponible por     |
|    reserva previa. Seleccione un bloque resaltado en color verde/azul."           |
+-----------------------------------------------------------------------------------+
```

**Nota de Interfaz:** Los slots pertenecientes al pasado, fuera de la ventana operativa (09:00-19:00) o que colisionen con citas previas se deshabilitan en el DOM (`disabled: true`), imposibilitando el evento de clic o selección por parte del usuario.

---

### Estado 4: Error en Formulario de Contacto (Sad Path / Validación RN-04)

**Escenario cubierto:** Escenario 6 (Intento de confirmación con nombre vacío o número telefónico con formato inválido como "123").

**Artefacto Visual:**

```text
+-----------------------------------------------------------------------------------+
| DATOS BÁSICOS DEL PACIENTE PARA CONFIRMACIÓN                                     |
+-----------------------------------------------------------------------------------+
| Nombre Completo: [*                                                       ]       |
| ⚠ Error: "El nombre completo del paciente es obligatorio."                        |
|                                                                                   |
| Teléfono Móvil:   [123                                                    ]       |
| ⚠ Error: "Ingrese un número telefónico válido de 9 dígitos (ej. 987654321)."      |
|                                                                                   |
| [ Botón: CONFIRMAR RESERVA (Deshabilitado / Estado: Error de Validación) ]        |
+-----------------------------------------------------------------------------------+
```

**Nota de Interfaz:** Validación reactiva en tiempo real sobre los campos del formulario. Se muestran mensajes de error específicos bajo cada input y se mantiene inactivo el botón de confirmación hasta que los datos cumplan con las reglas de formato.

---

### Estado 5: Conflictos por Concurrencia Simultánea / Race Condition (Sad Path)

**Escenario cubierto:** Escenario 7 (Dos clientes intentan confirmar la reserva del slot 16:00-16:30 con el Dr. Carlos Ruiz al mismo tiempo; el segundo cliente es rechazado).

**Artefacto Visual:**

```text
+-----------------------------------------------------------------------------------+
| ⚠ MODAL DE ALERTA: HORARIO RECIENTEMENTE RESERVADO                                |
+-----------------------------------------------------------------------------------+
| El bloque de horario de 16:00 a 16:30 con el Dr. Carlos Ruiz acaba de ser         |
| reservado por otro cliente hace unos instantes.                                  |
|                                                                                   |
| Tu solicitud no pudo completarse. Por favor, selecciona una nueva hora.           |
|                                                                                   |
|                  [ SELECCIONAR OTRO HORARIO DISPONIBLE ]                          |
+-----------------------------------------------------------------------------------+
```

**Nota de Interfaz:** En caso de que el backend responda con un conflicto de concurrencia (`HTTP 409 Conflict`), la interfaz bloquea el registro, levanta un modal informativo de prioridad alta y actualiza automáticamente la disponibilidad del calendario.

---

## 3. DECISIONES DE DISEÑO Y PUNTOS PENDIENTES

- **Heurísticas aplicadas:**
  - **Visibilidad del estado:** Transparencia total en el cálculo de duración ("60 min continuos") y avance mediante stepper visual.
  - **Prevención proactiva de errores:** Bloqueo en el cliente de turnos pasados, no operativos o colisionados.
  - **Experiencia sin fricciones:** Flujo simplificado para el MVP respetando las reglas RN-04 y RN-05 (reserva directa con datos de contacto básicos y pago presencial).
- **Bloqueos o Consultas (Si aplican):**
  - No existen bloqueos UX que impidan el pase a Arquitectura. Se mantiene la nota para iteraciones futuras sobre la inclusión de verificación OTP por SMS/WhatsApp y pasarela de cobro anticipado si la tasa de inasistencia lo requiere.

---

## 4. ORDEN DE DELEGACIÓN PARA EL TRACKER

@ARQ: Los wireframes funcionales para la Historia de Usuario Selección de servicios, cálculo de duración y reserva de horarios en tiempo real están listos. Puedes encontrar la estructura de UI y los IDs de Stitch en el archivo ux_01_reserva_disponibilidad.md. El requerimiento está listo para el diseño de arquitectura y base de datos.
