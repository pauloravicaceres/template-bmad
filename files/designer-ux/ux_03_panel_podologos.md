# ESPECIFICACIÓN DE DISEÑO UX Y WIREFRAMES ESTRUCTURALES

## 1. RESUMEN DE DISEÑO

- **Historia Base:** Dashboard de Gestión de Citas y Estado de Atención para Podólogos (`hu_03_panel_podologos.md`)
- **Enfoque de Usabilidad:** Panel de control operacional limpio, adaptado a dispositivos móviles o tablets en cabina de atención. Permite la supervisión cronológica del día, filtrado rápido por fecha, actualización de estados de atención en tiempo real (Programada -> En Atención -> Atendida / No Asistió) con aislamiento por podólogo autenticado (RN-01) y ocultación de tarifas (RN-04).

---

## 2. MAPA DE ESTADOS VISUALES

### Estado 1: Dashboard Principal Diario del Podólogo (Happy Path - Escenario 1)

**Escenario cubierto:** Escenario 1 (Visualización de la agenda del día asignada al podólogo autenticado).

```text
+-----------------------------------------------------------------------+
|  Spá Podológico Ámely | Panel Operativo de Podología                  |
+-----------------------------------------------------------------------+
|  Bienvenido, Dra. Valeria Mendoza  [ Mi Perfil ] [ Cerrar Sesión ]   |
|  FECHA SELECCIONADA: [<] Hoy, 15 de Octubre 2026 [>] [📅]             |
+-----------------------------------------------------------------------+
|  RESUMEN DEL DÍA: (4 Citas total | 2 Programadas | 1 En Atención | 1 Atendida)
+-----------------------------------------------------------------------+
|                                                                       |
|  [ 09:00 AM - 10:15 AM ] (75 min)                                     |
|  • Cliente: Maria Teresa Flores                                       |
|  • Servicios: Profilaxis Podológica Integral + Láser                  |
|  • Estado: [ EN ATENCIÓN  v]                                          |
|                                                                       |
|  -------------------------------------------------------------------  |
|                                                                       |
|  [ 11:30 AM - 12:15 PM ] (45 min)                                     |
|  • Cliente: Jorge Luis Benítez                                        |
|  • Servicios: Tratamiento de Uñero / Onicocriptosis                   |
|  • Estado: [ PROGRAMADA   v]                                          |
|                                                                       |
|  -------------------------------------------------------------------  |
|                                                                       |
|  [ 03:00 PM - 04:00 PM ] (60 min)                                     |
|  • Cliente: Ana Lucía Gómez                                           |
|  • Servicios: Evaluación Biomecánica y Plantillas                      |
|  • Estado: [ ATENDIDA     v]                                          |
|                                                                       |
+-----------------------------------------------------------------------+
```

**Nota de Interfaz:** Ocultación completa de montos facturados (RN-04). Filtro rápido por fecha en la barra superior.

---

### Estado 2: Actualización de Estado de Cita en Tiempo Real (Happy Path - Escenario 2)

**Escenario cubierto:** Escenario 2 (El podólogo cambia manualmente el estado de la cita de 'Programada' a 'En Atención' o 'Atendida').

```text
+-----------------------------------------------------------------------+
|  [ 11:30 AM - 12:15 PM ] (45 min)                                     |
|  • Cliente: Jorge Luis Benítez                                        |
|  • Servicios: Tratamiento de Uñero / Onicocriptosis                   |
|                                                                       |
|  SELECCIONAR NUEVO ESTADO:                                            |
|  +-----------------------------------------------------------------+  |
|  |  ( ) Programada                                                 |  |
|  |  (*) En Atención   <-- Estado Seleccionado                       |  |
|  |  ( ) Atendida                                                   |  |
|  |  ( ) No Asistió                                                 |  |
|  |                                                                 |  |
|  |                                  [ GUARDAR CAMBIO DE ESTADO ]   |  |
|  +-----------------------------------------------------------------+  |
|                                                                       |
|  REACCIÓN VISUAL EN TIEMPO REAL:                                      |
|  [✓] Cita actualizada a "En Atención" instantáneamente sin recarga.   |
+-----------------------------------------------------------------------+
```

**Nota de Interfaz:** Dropdown o selector de estado directo en la tarjeta de la cita (RN-02). La actualización visual ocurre mediante WebSocket/Sincronización en tiempo real sin refrescar la página.

---

### Estado 3: Reflejo Automático por Anulación Externa (Happy Path - Escenario 3)

**Escenario cubierto:** Escenario 3 (Sincronización instantánea cuando un cliente cancela su cita desde WhatsApp/Web).

```text
+-----------------------------------------------------------------------+
|  [ 04:00 PM - 05:00 PM ] (60 min)                                     |
|  • Cliente: Pedro Pablo Morales                                       |
|  • Servicios: Profilaxis Podológica Integral                          |
|                                                                       |
|  +-----------------------------------------------------------------+  |
|  |  [!] CITA ANULADA POR EL CLIENTE                                |  |
|  |  Estado: ANULADA (Actualizado a las 10:42 AM) [RN-03]            |  |
|  |                                                                 |  |
|  |  Este bloque horario ha sido liberado automáticamente en tu     |  |
|  |  agenda de atención pública.                                    |  |
|  +-----------------------------------------------------------------+  |
+-----------------------------------------------------------------------+
```

**Nota de Interfaz:** La tarjeta cambia de color a un estilo deshabilitado con un badge de notificación destacado informando que el bloque ha sido liberado en la agenda pública (RN-03).

---

### Estado 4: Vista de Agenda Vacía sin Citas Programadas (Sad Path / Flujo Alternativo - Escenario 4)

**Escenario cubierto:** Escenario 4 (El podólogo ingresa a un día sin reservas agendadas).

```text
+-----------------------------------------------------------------------+
|  Spá Podológico Ámely | Panel Operativo de Podología                  |
+-----------------------------------------------------------------------+
|  FECHA SELECCIONADA: [<] Domingo, 18 de Octubre 2026 [>] [📅]         |
+-----------------------------------------------------------------------+
|                                                                       |
|                  +---------------------------------+                  |
|                  |            [📅 ☕]             |                  |
|                  |                                 |                  |
|                  |   NO TIENES CITAS PROGRAMADAS   |                  |
|                  |        PARA ESTA FECHA          |                  |
|                  |                                 |                  |
|                  |  Disfruta de tu tiempo libre o  |                  |
|                  |  consulta otra fecha en el      |                  |
|                  |  calendario superior.           |                  |
|                  +---------------------------------+                  |
|                                                                       |
|                          [ IR A LA AGENDA DE HOY ]                    |
+-----------------------------------------------------------------------+
```

**Nota de Interfaz:** Pantalla con estado vacío (*Empty State*) claro y amigable que orienta al usuario y le permite navegar hacia fechas previas o futuras.

---

## 3. DECISIONES DE DISEÑO Y PUNTOS PENDIENTES

- **Heurísticas aplicadas:**
  - *Sincronización con el mundo real:* Terminología clara de estados acorde al flujo operativo en cabina.
  - *Diseño adaptable:* Layout diseñado priorizando tablets/dispositivos móviles usados por los profesionales podólogos.
- **Bloqueos o Consultas (Puntos Abiertos):**
  - **PA-01:** Definición del método de autenticación del personal médico.
  - **PA-02:** Confirmación de la matriz de estados y reglas de edición retroactiva.
  - **PA-03:** Definición de permisos de consulta entre colegas de la clínica.

---

## 4. ORDEN DE DELEGACIÓN PARA EL TRACKER

@HUMANO: Los wireframes funcionales para la Historia de Usuario Dashboard de Gestión de Citas y Estado de Atención para Podólogos están listos. Puedes encontrar la estructura de UI y los IDs de Stitch en el archivo ux_03_panel_podologos.md. El requerimiento está listo para el diseño de arquitectura y base de datos.
