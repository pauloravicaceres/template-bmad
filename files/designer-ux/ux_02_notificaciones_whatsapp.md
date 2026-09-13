## 1. RESUMEN DE DISEÑO

- **Historia Base:** Envío automático e inmediato de notificaciones y alertas por WhatsApp (`hu_02_notificaciones_whatsapp.md`)
- **Enfoque de Usabilidad:** Se diseñaron las plantillas de mensaje y los estados visuales para las notificaciones transaccionales vía WhatsApp (cliente y podólogo), asegurando la inclusión de los datos clave (fecha, hora, servicio, podólogo/cliente) y la omisión estricta de valores monetarios (RN-03). Asimismo, se diseñó la interfaz del registro de fallos en el historial de despachos sin bloquear las operaciones de agenda (Sad Path).

---

## 2. MAPA DE ESTADOS VISUALES

### Estado 1: Confirmación de Cita al Cliente (Happy Path)

**Escenario cubierto:** Escenario 1: Envío exitoso de confirmación al cliente tras reserva

```text
+-------------------------------------------------------------+
| [<-] Clínica Podológica - WhatsApp          [ (:) ] [ [⋮] ] |
+-------------------------------------------------------------+
|                                                             |
|  [ HOY ]                                                    |
|                                                             |
|  +-------------------------------------------------------+  |
|  | 🩺 ¡Cita Confirmada!                                  |  |
|  |                                                       |  |
|  | Hola Maria Lopez, tu cita ha sido reservada con éxito.|  |
|  |                                                       |  |
|  | 📅 Fecha: 15/09/2026                                  |  |
|  | ⏰ Hora: 10:30 AM                                     |  |
|  | 👨‍⚕️ Podólogo: Dr. Carlos Ruiz                       |  |
|  | 📋 Servicio(s): Profilaxis Podológica Completa        |  |
|  |                                                       |  |
|  | 📌 Por favor llega 10 minutos antes.                   |  |
|  |                                                       |  |
|  | 10:31 AM ✓✓                                           |  |
|  +-------------------------------------------------------+  |
|                                                             |
+-------------------------------------------------------------+
```

**Nota de Interfaz:** El mensaje es generado y despachado de forma automática (< 1 min) una vez confirmada la reserva. No incluye precios ni desgloses de costos (RN-03, RN-04).

---

### Estado 2: Alerta de Nueva Cita al Podólogo (Happy Path)

**Escenario cubierto:** Escenario 2: Envío exitoso de alerta al podólogo tras nueva reserva

```text
+-------------------------------------------------------------+
| [<-] Sistema de Alertas Podología - WhatsApp [ (:) ] [ [⋮] ] |
+-------------------------------------------------------------+
|                                                             |
|  [ HOY ]                                                    |
|                                                             |
|  +-------------------------------------------------------+  |
|  | 🔔 NUEVA CITA AGENDADA                                |  |
|  |                                                       |  |
|  | Estimado(a) Dr. Carlos Ruiz, se ha agendado una       |  |
|  | nueva consulta en tu agenda.                          |  |
|  |                                                       |  |
|  | 👤 Cliente: Maria Lopez                               |  |
|  | 📅 Fecha: 15/09/2026                                  |  |
|  | ⏰ Hora: 10:30 AM                                     |  |
|  | 📋 Servicios: Profilaxis Podológica Completa          |  |
|  |                                                       |  |
|  | 10:31 AM ✓✓                                           |  |
|  +-------------------------------------------------------+  |
|                                                             |
+-------------------------------------------------------------+
```

**Nota de Interfaz:** Alerta enviada al profesional asignado para mantenerlo informado instantáneamente. Cumple con RN-03 y RN-05.

---

### Estado 3: Alerta de Cancelación de Cita al Podólogo (Happy Path)

**Escenario cubierto:** Escenario 3: Envío exitoso de alerta al podólogo tras cancelación de cita

```text
+-------------------------------------------------------------+
| [<-] Sistema de Alertas Podología - WhatsApp [ (:) ] [ [⋮] ] |
+-------------------------------------------------------------+
|                                                             |
|  [ HOY ]                                                    |
|                                                             |
|  +-------------------------------------------------------+  |
|  | ⚠️ CITA CANCELADA - FRANJA LIBERADA                    |  |
|  |                                                       |  |
|  | Estimado(a) Dr. Carlos Ruiz, la siguiente cita ha     |  |
|  | sido cancelada:                                       |  |
|  |                                                       |  |
|  | 👤 Cliente: Maria Lopez                               |  |
|  | 📅 Fecha: 15/09/2026                                  |  |
|  | ⏰ Hora: 10:30 AM                                     |  |
|  | 📋 Estado franja: Disponible para agendamiento        |  |
|  |                                                       |  |
|  | 11:15 AM ✓✓                                           |  |
|  +-------------------------------------------------------+  |
|                                                             |
+-------------------------------------------------------------+
```

**Nota de Interfaz:** Notificación inmediata al podólogo ante la anulación de una reserva para notificar la liberación de la franja horaria (RN-05).

---

### Estado 4: Historial de Envíos y Registro de Fallos (Sad Path)

**Escenario cubierto:** Escenario 4: Manejo de error por número de WhatsApp no válido o fallo de canal

```text
+---------------------------------------------------------------------------------------------------------+
| Panel Administrativo > Historial de Despacho de Notificaciones                                         |
+---------------------------------------------------------------------------------------------------------+
| [ Buscar por cliente/teléfono... ]   Filtro Estado: [ Todos ⬑ ]   [ Filtrar ]                           |
+--------------+------------------+---------------+---------------------+-------------------+-------------+
| ID Reserva   | Destinatario     | Teléfono      | Tipo Notificación   | Estado Despacho   | Detalle     |
+--------------+------------------+---------------+---------------------+-------------------+-------------+
| #RES-98231   | Maria Lopez      | +51999888777  | Confirmación Cita   | [ ENVIADO ]       | OK (10:31)  |
| #RES-98232   | Juan Perez       | +51900000000  | Confirmación Cita   | [ ERROR CANAL ]   | Nro Inválido|
| #RES-98233   | Dr. Carlos Ruiz  | +51911223344  | Alerta Nueva Cita   | [ ENVIADO ]       | OK (10:31)  |
+--------------+------------------+---------------+---------------------+-------------------+-------------+
|                                                                                                         |
| ⚠️ Nota del sistema: La reserva #RES-98232 permance CONFIRMADA en la agenda. El fallo de envío no     |
| interrumpió ni revirtió la transacción en el sistema.                                                   |
+---------------------------------------------------------------------------------------------------------+
```

**Nota de Interfaz:** El fallo en la API o número inválido queda registrado en la bitácora/historial sin afectar o revertir el estado de la reserva en el sistema (Escenario 4).

---

## 3. DECISIONES DE DISEÑO Y PUNTOS PENDIENTES

- **Heurísticas aplicadas:**
  1. Uso de iconografía clara (📅, ⏰, 👨‍⚕️, 📋, ⚠️) dentro de los mensajes de WhatsApp para facilitar la rápida lectura tanto del cliente como del podólogo.
  2. Visibilidad del estado del sistema en el panel administrativo para auditar entregas sin bloquear el flujo principal de agenda.
- **Bloqueos o Consultas (Si aplican):**
  1. Definición exacta del proveedor de WhatsApp (API oficial / BSP) y plantillas aprobadas por Meta/WhatsApp.
  2. Implementación de política de reintentos automáticos para notificaciones fallidas por cortes temporales.

---

## 4. ORDEN DE DELEGACIÓN PARA EL TRACKER

@HUMANO: Los wireframes funcionales para la Historia de Usuario Envío automático e inmediato de notificaciones y alertas por WhatsApp están listos. Puedes encontrar la estructura de UI y los IDs de Stitch en el archivo ux_02_notificaciones_whatsapp.md. El requerimiento está listo para el diseño de arquitectura y base de datos.
