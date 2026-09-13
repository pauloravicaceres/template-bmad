# ESPECIFICACIÓN UX DE INTERFAZ Y ESTADOS VISUALES

## 1. RESUMEN DE DISEÑO

- **Historia Base:** Agendamiento de cita podológica y reserva de horario en tiempo real
- **Enfoque de Usabilidad:** Se diseñó un flujo asistido de 3 pasos (Servicios -> Podólogo -> Fecha/Hora) centrado en la usabilidad móvil y claridad clínica. La interfaz calcula dinámicamente la duración total acumulada sumando la duración en minutos de los servicios seleccionados (sin mostrar precios por regla de negocio RN-04). Con esta duración, la agenda filtra en tiempo real únicamente aquellos bloques continuos de disponibilidad del podólogo seleccionado dentro de su jornada laboral, previniendo solapamientos al 100% e integrando recuperación inmediata en los escenarios alternativos.

---

## 2. MAPA DE ESTADOS VISUALES

### Estado 1: Agendamiento exitoso de cita podológica continua (Happy Path)

**Escenario cubierto:** Escenario 1: Agendamiento exitoso de cita podológica continua (Happy Path)

[ARTEFACTO VISUAL: Stitch Screen ID: `030a6d1c62cd4b77a51488bfc2a2ac72` | Project ID: `3827566166421569955`]

```text
+-----------------------------------------------------------------------+
|  <- Agendar Cita Podológica                              [ Ayuda ]    |
|  [ 1. Servicios (✓) ] === [ 2. Podólogo (✓) ] === [ 3. Fecha/Hora (●) ]|
+-----------------------------------------------------------------------+
|  PASO 1: SELECCIÓN DE SERVICIOS (Sin precios visuales)                |
|  [x] Quiropodia Clínica Integral               | Duración: 45 min      |
|  [x] Tratamiento de Onicocriptosis             | Duración: 30 min      |
|  [ ] Estudio Biomecánico de la Marcha          | Duración: 40 min      |
|  -------------------------------------------------------------------  |
|  Badge: 2 servicios seleccionados • 75 min acumulados                 |
+-----------------------------------------------------------------------+
|  PASO 2: SELECCIÓN DE PODÓLOGO                                        |
|  (x) Dra. Elena Valenzuela (★ 4.9) [ Seleccionado ]                    |
|  ( ) Dr. Marcos Sotomayor (★ 4.8)                                     |
+-----------------------------------------------------------------------+
|  PASO 3: SELECCIÓN DE HORARIO (Tiempo Real)                           |
|  [ Hoy 24 Oct ]  [*Mañ 25 Oct*]  [ Sáb 26 Oct ]                       |
|  Turnos disponibles para 75 min continuos:                            |
|  [ 09:00 ] [ 09:45 ] [*10:30* (Tu turno: 10:30 - 11:45)] [ 12:00 ]     |
|  Nota: Horario reservado en tiempo real durante 10 minutos.           |
+-----------------------------------------------------------------------+
|  [ BARRA FLOTANTE INFERIOR ]                                          |
|  Resumen: 75 min • 2 servicios • Dra. Elena Valenzuela                |
|  [ BOTÓN: Confirmar Reserva (Habilitado) ]                            |
+-----------------------------------------------------------------------+
```

**Nota de Interfaz:** El botón "Confirmar Reserva" se mantiene deshabilitado hasta seleccionar al menos 1 servicio, 1 podólogo y 1 bloque continuo válido. Los slots calculan el bloque exacto concatenado (10:30 a 11:45 para 75 min).

---

### Estado 2: Intentar reservar un horario no disponible o en solapamiento (Sad Path / Conflicto de Disponibilidad)

**Escenario cubierto:** Escenario 2: Intentar reservar un horario no disponible o en solapamiento (Sad Path / Conflicto de Disponibilidad)

[ARTEFACTO VISUAL: Stitch Screen ID: `bce5336de0c04f5eb05c22d436943ce1` | Project ID: `3827566166421569955`]

```text
+-----------------------------------------------------------------------+
|                       [ OVERLAY SEMI-TRANSPARENTE ]                   |
|  +-----------------------------------------------------------------+  |
|  |  [!] HORARIO NO DISPONIBLE                                      |  |
|  |  El horario seleccionado (10:30 - 11:45) acaba de ser reservado |  |
|  |  por otro usuario.                                              |  |
|  |                                                                 |  |
|  |  La disponibilidad se actualiza en tiempo real para evitar      |  |
|  |  solapamientos.                                                 |  |
|  |                                                                 |  |
|  |  [ BOTÓN CTA: Ver otros horarios disponibles ]                   |  |
|  |  [ Enlace: Cambiar de profesional o fecha ]                     |  |
|  +-----------------------------------------------------------------+  |
|  Fondo: Slot 10:30 deshabilitado/marcado como ocupado en la grilla.    |
+-----------------------------------------------------------------------+
```

**Nota de Interfaz:** Pop-up modal que bloquea la confirmación al detectar un solapamiento en el check de backend previo a guardar. Al presionar "Ver otros horarios disponibles", se refresca la grilla y el horario en conflicto cambia a estado "Ocupado".

---

### Estado 3: Duración requerida excede la disponibilidad continua disponible (Sad Path / Tiempo Insuficiente)

**Escenario cubierto:** Escenario 3: Duración requerida excede la disponibilidad continua disponible (Sad Path / Tiempo Insuficiente)

[ARTEFACTO VISUAL: Stitch Screen ID: `ffe886901089443baacebfe4745d1774` | Project ID: `3827566166421569955`]

```text
+-----------------------------------------------------------------------+
|  PASO 1: SERVICIOS: 2 seleccionados (75 min acumulados)               |
|  PASO 2: PODÓLOGO: Dra. Claudia Benítez (Seleccionada)                |
+-----------------------------------------------------------------------+
|  PASO 3: FECHA Y HORARIO                                              |
|  [ BANNER DE ADVERTENCIA / INFORMATIVO ]                              |
|  "Para la duración seleccionada (75 min), no hay bloques continuos    |
|   disponibles antes del fin de jornada de este profesional. Te        |
|   sugerimos cambiar de fecha o seleccionar otro especialista."        |
|                                                                       |
|  Acciones Rápidas:                                                    |
|  [ Ver próxima fecha con 75 min libres ]  [ Cambiar especialista ]    |
|                                                                       |
|  Grilla de Horarios (Inhabilitados):                                  |
|  [ 09:00 (< 75 min) ] [ 09:45 (< 75 min) ] [ 15:30 (Jornada final) ]   |
+-----------------------------------------------------------------------+
|  [ BARRA FLOTANTE INFERIOR ]                                          |
|  Resumen: Dra. Claudia Benítez • Sin horarios compatibles (75 min)    |
|  [ BOTÓN: Ver Especialista Alternativo Hoy (Acción Asistida) ]        |
+-----------------------------------------------------------------------+
```

**Nota de Interfaz:** Ningún slot con ventana de tiempo libre menor a N minutos (75 min) se muestra como elegible/activo. El sistema inhabilita la selección de dichos slots y deshabilita la confirmación directa, guiando al usuario con alternativas de especialista o fecha.

---

## 3. DECISIONES DE DISEÑO Y PUNTOS PENDIENTES

- **Heurísticas aplicadas:**
  1. *Visibilidad del Estado del Sistema (Heurística 1):* Se añade un micro-badge de duración continua visible en todo momento ("75 min acumulados") y un resumen fijo en la barra inferior para que el paciente entienda cómo se calcula su cita.
  2. *Prevención de Errores (Heurística 5):* Ocultamiento/inhabilitación proactiva de bloques horarios insuficientes para evitar que el usuario seleccione horas donde el podólogo no pueda atender la cita completa.
  3. *Control y Libertad del Usuario (Heurística 3):* En caso de conflicto de último segundo (Sad Path 2), el modal proporciona salidas claras e inmediatas sin perder la selección previa de servicios.
- **Bloqueos o Consultas (Puntos Abiertos de UX / Negocio):**
  1. *Autenticación del Cliente (Punto Abierto HU):* Al presionar "Confirmar Reserva", el prototipo asume la apertura de un modal/sheet de ingreso de Datos Básicos (Nombre, DNI, Teléfono). Se requiere definición del BA sobre si requiere inicio de sesión.
  2. *Buffer / Margen de Desinfección (Punto Abierto HU):* El cálculo actual es suma directa ($N_1 + N_2$). Si el negocio aprueba un buffer (ej. +15 min), el filtro de slots en la UI se actualizará automáticamente a $N_{total} + Buffer$.

---

## 4. ORDEN DE DELEGACIÓN PARA EL TRACKER

@HUMANO: Los wireframes funcionales para la Historia de Usuario Agendamiento de cita podológica y reserva de horario en tiempo real están listos. Puedes encontrar la estructura de UI y los IDs de Stitch en el archivo ux_01_agendamiento.md. El requerimiento está listo para el diseño de arquitectura y base de datos.
