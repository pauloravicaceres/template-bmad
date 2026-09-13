# ESPECIFICACIÓN DE DISEÑO UX

## 1. RESUMEN DE DISEÑO

- **Historia Base:** Envío automático de notificaciones vía WhatsApp por confirmación de reserva y anulación de cita
- **Enfoque de Usabilidad:** Se diseñaron las plantillas de mensajes interactivos de WhatsApp (HSM transaccionales) para cliente y podólogo, así como la vista del estado en pantalla y el registro en bitácora operativa ante fallos de la API externa. Garantiza comunicación instantánea sin fricción y resiliencia ante errores de conexión.

## 2. MAPA DE ESTADOS VISUALES

### Estado 1: Notificación por WhatsApp de Confirmación de Reserva (Happy Path)

**Escenario cubierto:** Escenario 1 - Notificación automática instantánea enviada al cliente y al podólogo al confirmarse la cita.

```text
=====================================================
  WHATSAPP BUSINESS - ÁMELY SPÁ PODOLÓGICO
=====================================================
[Foto Spa] Ámely Spá Podológico (Cuenta Oficial V)

[Mensaje al Cliente]
-----------------------------------------------------
¡Hola, Carlos! 🦶✨ Tu cita ha sido reservada con éxito.

📌 Detalle de tu Reserva:
• Servicio(s): Profilaxis Podológica + Masaje Descontracturante (75 min)
• Podólogo: Dr. Roberto Gómez
• Fecha: 18 de Septiembre, 2026
• Hora: 10:00 AM - 11:15 AM
• Código de Cita: #POD-8842

🔗 Gestiona o anula tu cita aquí:
https://amelyspa.com/cita/POD-8842

¡Te esperamos en Av. Benavides 1450, Miraflores!
-----------------------------------------------------

[Mensaje al Podólogo]
-----------------------------------------------------
🔔 NUEVA CITA AGENDADA

• Cliente: Carlos Mendoza
• Servicio: Profilaxis + Masaje (75 min)
• Fecha: 18 de Septiembre, 2026
• Horario: 10:00 AM - 11:15 AM
• Estado: Confirmado / Agenda Bloqueada
-----------------------------------------------------
```

**Nota de Interfaz:** El mensaje incluye botones/enlaces directos de gestión sin requerir inicio de sesión. Para el podólogo, la notificación actualiza en tiempo real su cronograma de atenciones.

---

### Estado 2: Notificación por WhatsApp de Anulación de Cita al Podólogo (Happy Path)

**Escenario cubierto:** Escenario 2 - Notificación automática al podólogo informando la cancelación de una cita previamente agendada por el cliente y la liberación de su bloque horario.

```text
=====================================================
  WHATSAPP BUSINESS - NOTIFICACIÓN DE PODÓLOGO
=====================================================

[Mensaje al Podólogo]
-----------------------------------------------------
⚠️ CITA ANULADA Y HORARIO LIBERADO

• Cliente: Carlos Mendoza
• Cita ID: #POD-8842
• Fecha: 18 de Septiembre, 2026
• Horario liberado: 10:00 AM - 11:15 AM

ℹ️ Tu agenda ha sido actualizada automáticamente. El bloque horario vuelve a estar disponible para reservas de otros clientes.
-----------------------------------------------------
```

**Nota de Interfaz:** Formato conciso de alta visibilidad para que el profesional identifique inmediatamente la liberación de su tiempo y evite tiempos muertos no planificados.

---

### Estado 3: Manejo de Fallos en API Externa y Bitácora del Sistema (Sad Path)

**Escenario cubierto:** Escenario 3 - La API de WhatsApp está fuera de servicio. La reserva/anulación se completa exitosamente en el sistema y se registra el fallo en la bitácora operativa sin bloquear al usuario en pantalla.

```text
=====================================================
  PANTALLA CLIENTE (CONFIRMACIÓN EN SITO WEB/APP)
=====================================================
 [✓] ¡RESERVA CONFIRMADA CON ÉXITO!
 Tu cita #POD-8842 ha sido agendada para el 18 Sept, 10:00 AM.
 
 ⚠️ Nota: El envío de tu comprobante por WhatsApp está
 temporalmente demorado. Guarda tu código de cita: #POD-8842.

=====================================================
  VISTA BITÁCORA DEL SISTEMA (LOGS OPERATIVOS / ADMIN)
=====================================================
 [LOG-2026-09-18T10:01:05Z] 
 • Evento: NOTIFICACION_RESERVA_WHATSAPP
 • Cita_ID: POD-8842
 • Destinatario: +51999888777 (Cliente)
 • Estado: FALLIDO / REINTENTO_PENDIENTE
 • Error_API: "503 Service Unavailable - WhatsApp Business API Gateway"
 • Acción: Transacción de reserva COMPLETADA. Notificación encolada para reintento.
```

**Nota de Interfaz:** Resiliencia de UX: La falla del canal de comunicación no interrumpe la transacción del negocio. Se le muestra al cliente la confirmación en pantalla con su código de cita y se genera un registro auditable en bitácora para el equipo técnico.

---

## 3. DECISIONES DE DISEÑO Y PUNTOS PENDIENTES

- **Heurísticas aplicadas:**
  - **Tolerancia a fallos:** Desacoplamiento entre la confirmación del servicio y el canal de mensajería (la caída de la API externa no bloquea la reserva).
  - **Consistencia visual y de tono:** Formato estandarizado con emojis informativos para fácil lectura en dispositivos móviles.
- **Bloqueos o Consultas (Puntos Abiertos):**
  - **PA-01:** Elección del proveedor de API WhatsApp Business (Twilio / Meta Cloud API) para definir el formato JSON final del webhook.
  - **PA-02:** Aprobación formal de las plantillas HSM por parte del equipo de Marketing/Negocio.

---

## 4. ORDEN DE DELEGACIÓN PARA EL TRACKER

@HUMANO: Los wireframes funcionales para la Historia de Usuario Envío automático de notificaciones vía WhatsApp por confirmación de reserva y anulación de cita están listos. Puedes encontrar la estructura de UI y las plantillas de mensajes en el archivo ux_03_notificaciones_whatsapp.md. El requerimiento está listo para el diseño de arquitectura y base de datos.
