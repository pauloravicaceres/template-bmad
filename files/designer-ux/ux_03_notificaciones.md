# ESPECIFICACIÓN UX DE INTERFAZ Y ESTADOS VISUALES

## 1. RESUMEN DE DISEÑO

- **Historia Base:** Envío automático de notificaciones de confirmación y anulación de cita vía WhatsApp
- **Enfoque de Usabilidad:** Se diseñaron las interfaces de notificaciones automáticas y trazabilidad para el canal exclusivo de WhatsApp. Para las confirmaciones de reserva (Cliente) y alertas de anulación (Podólogo), se especificaron plantillas de mensajes interactivos en mockups nativos de WhatsApp Business con formato legible (*negritas*, emojis claros, botones de respuesta rápida `Quick Replies`) omitiendo precios según la regla RN-03. Para el escenario de fallos de red en la API de WhatsApp, se diseñó la consola de auditoría del sistema donde se demuestra visualmente la resiliencia transaccional: la reserva o anulación se mantiene guardada y confirmada en la base de datos sin revertir la cita.

---

## 2. MAPA DE ESTADOS VISUALES

### Estado 1: Envío exitoso de notificación de confirmación de reserva (Happy Path)

**Escenario cubierto:** Escenario 1: Envío exitoso de notificación de confirmación de reserva (Happy Path)

[ARTEFACTO VISUAL: Stitch Screen ID: `0e522189d65e4439b7518a0f2348f695` | Project ID: `3827566166421569955`]

```text
+-----------------------------------------------------------------------+
|  [<-] PodoCare Clínica (✓ Business Account)        [Llamar] [:]       |
+-----------------------------------------------------------------------+
|                                                                       |
|  +-----------------------------------------------------------------+  |
|  |  ¡Cita Confirmada! 🩺✨                                         |  |
|  |                                                                 |  |
|  |  Hola *Camila*, tu cita ha sido reservada con éxito en          |  |
|  |  *PodoCare Clínica*.                                            |  |
|  |                                                                 |  |
|  |  📋 *Detalles del Tratamiento:*                                 |  |
|  |  • Quiropodia Clínica Integral                                  |  |
|  |  • Tratamiento de Onicocriptosis                                |  |
|  |  • Duración estimada: 75 min                                   |  |
|  |                                                                 |  |
|  |  👩‍⚕️ *Especialista:* Dra. Elena Valenzuela                       |  |
|  |  📅 *Fecha y Hora:* Mañana Viernes 25 de Octubre, 10:30 hrs       |  |
|  |  📍 *Ubicación:* Av. Vitacura 4280, Piso 3, Consulta 304           |  |
|  |                                                                 |  |
|  |  10:32 AM  [✓✓]                                                 |  |
|  |-----------------------------------------------------------------|  |
|  |  [ 🗓️ Ver mi cita / Modificar ]  [ 💬 Contactar al Spa ]        |  |
|  +-----------------------------------------------------------------+  |
|                                                                       |
+-----------------------------------------------------------------------+
```

**Nota de Interfaz:** Disparo automático inmediato post-reserva. El mensaje contiene la concatenación de servicios (75 min total) sin incluir valores monetarios. Incluye dos botones interactivos Quick Reply de WhatsApp para autogestión directa.

---

### Estado 2: Notificación inmediata al podólogo por anulación de reserva (Happy Path / Anulación)

**Escenario cubierto:** Escenario 2: Notificación inmediata al podólogo por anulación de reserva (Happy Path / Anulación)

[ARTEFACTO VISUAL: Stitch Screen ID: `f67c08ed9e6343e7a94c2b218d44f714` | Project ID: `3827566166421569955`]

```text
+-----------------------------------------------------------------------+
|  [<-] PodoCare Bot -> Dra. Elena Valenzuela         [Oficial] [:]     |
+-----------------------------------------------------------------------+
|                                                                       |
|  +-----------------------------------------------------------------+  |
|  |  Cita Anulada - Horario Liberado ⚠️ [ URGENTE ]                  |  |
|  |                                                                 |  |
|  |  Estimada Dra. Elena Valenzuela,                                |  |
|  |  La cita agendada por *Camila Torres* para el                   |  |
|  |  *Viernes 25 de Octubre a las 10:30 AM* ha sido ANULADA.         |  |
|  |                                                                 |  |
|  |  📋 *Detalles liberados:*                                        |  |
|  |  • Servicios: Quiropodia + Onicocriptosis (75 min)              |  |
|  |  • Bloque 10:30 - 11:45 AM liberado en tiempo real.             |  |
|  |                                                                 |  |
|  |  10:34 AM  [✓✓]                                                 |  |
|  |-----------------------------------------------------------------|  |
|  |  [ 📅 Ver mi agenda actualizada ]                               |  |
|  +-----------------------------------------------------------------+  |
|                                                                       |
+-----------------------------------------------------------------------+
```

**Nota de Interfaz:** Notificación inmediata saliente enviada a la cuenta de WhatsApp del especialista asignado al momento en que el cliente cancela la reserva, permitiendo al podólogo ver la liberación del bloque de 75 minutos en su agenda en tiempo real.

---

### Estado 3: Fallo en el envío de la notificación por problema de integración/red (Sad Path)

**Escenario cubierto:** Escenario 3: Fallo en el envío de la notificación por problema de integración/red (Sad Path)

[ARTEFACTO VISUAL: Stitch Screen ID: `c8a1076f14594de4a61f9d5711e77445` | Project ID: `3827566166421569955`]

```text
+-----------------------------------------------------------------------+
|  PODOCARE ADMIN | Auditoría IT > Logs de Sistema & Webhooks           |
+-----------------------------------------------------------------------+
|  [ BANNER DE INTEGRIDAD DE NEGOCIO - VERDE / ÁMBAR ]                  |
|  "Transacción guardada exitosamente: La reserva #POD-8492 se mantiene |
|   CONFIRMADA en la agenda del podólogo. El fallo en la API de         |
|   WhatsApp no afectó la integridad de la cita. Reintento programado." |
|   [ Botón: Reintentar envío ahora ]  [ Botón: Ver Reserva #POD-8492 ] |
+-----------------------------------------------------------------------+
|  TABLA DE LOGS DE AUDITORÍA:                                          |
|  Timestamp | Event ID  | Evento                 | Estado              |
|  10:32:14  | EVT-98213 | WHATSAPP_FAILED        | [ 503 Gateway Err ] |
|  10:32:02  | EVT-98212 | APPOINTMENT_CONFIRMED  | [ 200 OK (DB) ]     |
|                                                                       |
|  PANEL DE REINTENTOS (Backoff):                                       |
|  - Estado Reserva: CONFIRMADA (Inmutable)                             |
|  - Cola de Mensajería: Reintento 1/3 programado en 45 segundos        |
+-----------------------------------------------------------------------+
```

**Nota de Interfaz:** Ante una caída o timeout (HTTP 503) del proveedor de WhatsApp, la plataforma registra el error de salida en los logs de auditoría sin hacer rollback ni afectar la reserva en base de datos. La UI de administración muestra que la cita sigue 100% agendada e inicia la cola de reintentos automáticos.

---

## 3. DECISIONES DE DISEÑO Y PUNTOS PENDIENTES

- **Heurísticas aplicadas:**
  1. *Visibilidad del Estado del Sistema (Heurística 1):* Las notificaciones salientes usan patrones estándar de mensajería (marcas de tiempo, confirmación con doble check y botones interactivos) para mantener informado tanto al paciente como al podólogo sobre los eventos de su cita.
  2. *Prevención de Errores y Resiliencia (Heurística 5):* Garantía visual en consola administrativa de que un fallo de red en la notificación saliente jamás invalidará o revertirá el registro de una atención podológica.
  3. *Reconocimiento antes que recuerdo (Heurística 6):* Los mensajes de WhatsApp estructuran la información completa del agendamiento en bloques de texto formateado (*Servicios*, *Podólogo*, *Duración*, *Fecha/Hora*, *Dirección*) para evitar dudas en el paciente.
- **Bloqueos o Consultas (Puntos Abiertos de UX / Negocio):**
  1. *Proveedor de API WhatsApp (Punto Abierto HU):* Se requiere definición de Arquitectura sobre el proveedor (Twilio vs Meta WhatsApp Cloud API) para homologar los nombres exactos de los webhooks y payloads en la consola de auditoría.
  2. *Plantillas Homologadas de WhatsApp:* Las plantillas del prototipo deben someterse a la aprobación de plantillas comerciales de Meta antes del paso a producción.

---

## 4. ORDEN DE DELEGACIÓN PARA EL TRACKER

@HUMANO: Los wireframes funcionales para la Historia de Usuario Envío automático de notificaciones de confirmación y anulación de cita vía WhatsApp están listos. Puedes encontrar la estructura de UI y los IDs de Stitch en el archivo ux_03_notificaciones.md. El requerimiento está listo para el diseño de arquitectura y base de datos.
