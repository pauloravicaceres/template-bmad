# ESPECIFICACIÓN DE DISEÑO UX Y WIREFRAMES ESTRUCTURALES

## 1. RESUMEN DE DISEÑO

- **Historia Base:** Notificaciones Automáticas de Reserva y Anulación de Citas por WhatsApp (`hu_02_notificaciones_anulacion.md`)
- **Enfoque de Usabilidad:** Comunicación multicanal e interactividad asíncrona de confirmación y anulación. Se prioriza la legibilidad visual de los mensajes en interfaz móvil de WhatsApp (omitidos los datos de precios/costos por regla de negocio) y una experiencia web sencilla de anulación directa en un solo clic con confirmación modal e indicaciones claras en caso de fallos de red en la API externa.

---

## 2. MAPA DE ESTADOS VISUALES

### Estado 1: Mensaje de Confirmación de Reserva vía WhatsApp (Happy Path - Escenario 1)

**Escenario cubierto:** Escenario 1 (Notificación instantánea dual enviada al cliente y al podólogo tras agendamiento).

```text
+-----------------------------------------------------------------------+
|  < WhatsApp Chat (Spá Podológico Ámely)                               |
+-----------------------------------------------------------------------+
|  [ Ámely Bot - 10:30 AM ]                                             |
|  ¡Hola, Maria! 👋 Tu cita en Spá Podológico Ámely ha sido CONFIRMADA. |
|                                                                       |
|  📌 DETALLES DE LA RESERVA:                                          |
|  • Servicio(s): Profilaxis Podológica Integral + Láser                |
|  • Profesional: Dra. Valeria Mendoza                                  |
|  • Fecha: Jueves, 15 de Octubre 2026                                  |
|  • Horario: 09:00 AM - 10:15 AM (75 min)                              |
|                                                                       |
|  ⚠️ Si necesitas anular tu cita, haz clic en el siguiente enlace:     |
|  https://amely.pe/anular?token=xyz123456                              |
|                                                                       |
|  ¡Te esperamos con los mejores cuidados para tus pies! 🦶✨           |
+-----------------------------------------------------------------------+
```

**Nota de Interfaz:** Ocultación estricta de precios (RN-05). Se provee el enlace tokenizado único para anulación directa en un solo clic sin necesidad de inicio de sesión complejo.

---

### Estado 2: Flujo Web y Modal de Anulación de Cita Exitoso (Happy Path - Escenario 2)

**Escenario cubierto:** Escenario 2 (Anulación por parte del cliente, cambio a estado 'Anulada', liberación inmediata de agenda y notificaciones).

```text
+-----------------------------------------------------------------------+
|  Spá Podológico Ámely | Gestión de Reserva                           |
+-----------------------------------------------------------------------+
|  DETALLE DE TU CITA RESERVADA:                                        |
|  • Fecha y Hora: 15/10/2026 - 09:00 AM                                |
|  • Profesional: Dra. Valeria Mendoza                                  |
|  • Estado Actual: CONFIRMADA                                          |
|                                                                       |
|  [ ANULAR MI CITA ]  <-- Botón de Acción Principal                    |
|                                                                       |
|  ===================================================================  |
|  MODAL DE CONFIRMACIÓN (Al hacer clic en Anular):                     |
|  +-----------------------------------------------------------------+  |
|  |  ¿Está seguro de que desea anular esta cita?                    |  |
|  |  Esta acción es irreversible y liberará la agenda. [RN-04]       |  |
|  |                                                                 |  |
|  |             [ CANCELAR ]    [ SÍ, CONFIRMAR ANULACIÓN ]         |  |
|  +-----------------------------------------------------------------+  |
|                                                                       |
|  ===================================================================  |
|  ESTADO FINAL EN PANTALLA TRAS CONFIRMAR:                             |
|  [✓] TU CITA HA SIDO ANULADA EXITOSAMENTE.                            |
|  Se ha enviado una notificación de confirmación a tu WhatsApp.        |
+-----------------------------------------------------------------------+
```

**Nota de Interfaz:** La anulación actualiza el estado inmediatamente a "Anulada" y gatilla el despacho de notificaciones a cliente y podólogo (RN-02 y RN-03).

---

### Estado 3: Vista de Intento de Anulación sobre Cita Previamente Anulada (Sad Path - Escenario 3)

**Escenario cubierto:** Escenario 3 (El cliente intenta acceder al enlace de anulación de una cita que ya fue anulada previamente).

```text
+-----------------------------------------------------------------------+
|  Spá Podológico Ámely | Estado de Reserva                             |
+-----------------------------------------------------------------------+
|  +-----------------------------------------------------------------+  |
|  |  [i] ESTA CITA YA SE ENCUENTRA ANULADA                          |  |
|  |-----------------------------------------------------------------|  |
|  |  La cita agendada para el 15/10/2026 a las 09:00 AM fue cancelada |  |
|  |  previamente. No es posible realizar cambios ni reanudarla.      |  |
|  |                                                                 |  |
|  |  Si deseas agendar una nueva atención, por favor ingresa a:     |  |
|  |  [ AGENDAR NUEVA CITA ]                                         |  |
|  +-----------------------------------------------------------------+  |
+-----------------------------------------------------------------------+
```

**Nota de Interfaz:** Interfaz informativa bloqueante que previene la reactivación o duplicación de notificaciones según la regla de irreversibilidad (RN-04).

---

### Estado 4: Pantalla con Aviso de Fallo en API de WhatsApp (Sad Path - Escenario 4)

**Escenario cubierto:** Escenario 4 (Reserva o anulación procesada exitosamente en la base de datos, pero la API de WhatsApp falla).

```text
+-----------------------------------------------------------------------+
|  Spá Podológico Ámely | Confirmación de Operación                     |
+-----------------------------------------------------------------------+
|  [✓] ¡OPERACIÓN REGISTRADA EXITOSAMENTE!                              |
|                                                                       |
|  +-----------------------------------------------------------------+  |
|  |  ⚠️ NOTA SOBRE NOTIFICACIÓN POR WHATSAPP:                       |  |
|  |  Tu reserva/anulación fue procesada correctamente en nuestro      |  |
|  |  sistema. Sin embargo, no pudimos enviar el mensaje automático a  |  |
|  |  tu WhatsApp debido a una interrupción temporal del servicio.    |  |
|  |                                                                 |  |
|  |  Por favor guarda este comprobante o captura de pantalla.        |  |
|  +-----------------------------------------------------------------+  |
|                                                                       |
|  [ FINALIZAR ]                                                        |
+-----------------------------------------------------------------------+
```

**Nota de Interfaz:** Garantiza la transparencia y confianza del cliente sin revertir la transacción de negocio principal de reserva o liberación de horario.

---

## 3. DECISIONES DE DISEÑO Y PUNTOS PENDIENTES

- **Heurísticas aplicadas:**
  - *Reconocimiento antes que recuerdo:* Presentación clara de los datos completos de la cita en el flujo de anulación web.
  - *Manejo claro de errores:* Avisos no bloqueantes cuando falla el canal secundario de comunicación (WhatsApp).
- **Bloqueos o Consultas (Puntos Abiertos):**
  - **PA-01:** Confirmar token de seguridad en la URL para omitir login.
  - **PA-02 & PA-03:** Parametrización de plantillas finales de mensajería comercial y tiempos límites para anular.

---

## 4. ORDEN DE DELEGACIÓN PARA EL TRACKER

@HUMANO: Los wireframes funcionales para la Historia de Usuario Notificaciones Automáticas de Reserva y Anulación de Citas por WhatsApp están listos. Puedes encontrar la estructura de UI y los IDs de Stitch en el archivo ux_02_notificaciones_anulacion.md. El requerimiento está listo para el diseño de arquitectura y base de datos.
