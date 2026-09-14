## 1. RESUMEN DE DISEÑO

- **Historia Base:** Envío Automático de Confirmaciones y Alertas de Cita por WhatsApp (`hu_02_notificaciones_whatsapp.md`)
- **Enfoque de Usabilidad:** Se diseñó una experiencia de mensajería nativa institucional emulando WhatsApp Business oficial con formato estructurado, rápido acceso a acciones mediante botones interactivos (Quick Replies) y vistas duales (paciente y especialista podólogo). El flujo garantiza notificaciones automáticas inmediatas tras eventos de reserva o cancelación, respetando estrictamente la regla inquebrantable de 0 precios visibles.

## 2. MAPA DE ESTADOS VISUALES

### Estado 1: Notificación de Confirmación de Cita al Cliente y Alerta al Podólogo (Happy Path)

**Escenario cubierto:** Escenario 1: Envío exitoso de notificaciones de confirmación de reserva (Happy Path)

- **ID de Pantalla en Stitch:** `projects/13539032631391197448/screens/533d43425e254284b65f8ddad37ac4ed`
- **Proyecto Stitch:** `projects/13539032631391197448` (Motor de Reservas Spa Amely)

**Nota de Interfaz:** Al completarse la reserva, el sistema dispara automáticamente el mensaje de confirmación al cliente conteniendo el detalle estructurado de tratamientos, duración combinada (75 min), especialista colegiado, gabinete y recomendaciones higiénicas previas. Paralelamente, emite la alerta interna en la vista del podólogo indicando la preparación del kit de autoclave en gabinete.

### Estado 2: Notificación de Anulación de Cita al Podólogo (Sad Path / Cancelación)

**Escenario cubierto:** Escenario 2: Envío de notificación de anulación al profesional podólogo

- **ID de Pantalla en Stitch:** `projects/13539032631391197448/screens/90542fd9da054f1f809543b90545395a`
- **Proyecto Stitch:** `projects/13539032631391197448` (Motor de Reservas Spa Amely)

**Nota de Interfaz:** Cuando un cliente cancela su reserva previa, el sistema envía una alerta inmediata al WhatsApp de la podóloga asignada con la insignia «Alerta de Agenda - Cita Anulada», indicando el paciente que canceló, el gabinete liberado (Gabinete 2) y destacando el bloque horario liberado (75 min) junto al botón interactivo `[ Ver Agenda Actualizada ]` para reasignación prioritaria.

### Estado 3: Verificación de Restricción Inquebrantable (No Precios)

**Escenario cubierto:** Escenario 3: Verificación de Prohibición de Precios en Mensajes de WhatsApp

- **ID de Pantalla en Stitch:** `projects/13539032631391197448/screens/533d43425e254284b65f8ddad37ac4ed`

**Nota de Interfaz:** Las plantillas de mensajería automatizada omiten por completo divisas, montos numéricos de costos o tarifas. El mensaje enfoca la comunicación exclusivamente en aspectos clínicos, tiempos de atención y preparación preventiva del paciente.

## 3. DECISIONES DE DISEÑO Y PUNTOS PENDIENTES

- **Heurísticas aplicadas:**
  - *Visibilidad del estado del sistema (Heurística 1):* Doble check de entrega, timestamps claros y badges de estado del gabinete ("Gabinete Listo", "75 min liberados") en WhatsApp.
  - *Flexibilidad y eficiencia de uso (Heurística 7):* Botones de respuesta rápida (Quick Reply Buttons de WhatsApp) como `[ Confirmar Asistencia ]` y `[ Ver Agenda Actualizada ]` para reducir la fricción interactiva al mínimo de clics.
  - *Consistencia y Estándares (Heurística 4):* Adaptación estética del branding *Serene Podiatric Sanctuary* dentro de los contenedores de mensaje WhatsApp Business.
- **Bloqueos o Consultas:**
  - *Consulta Técnica para el BA / Dev:* Se debe validar el manejo de reintentos con el proveedor de la API de WhatsApp en caso de fallos temporales en el número celular del cliente (Punto Abierto 2 de la HU).

# 4. ORDEN DE DELEGACIÓN PARA EL TRACKER

@PM: Los wireframes para la HU Envío Automático de Confirmaciones y Alertas de Cita por WhatsApp están listos en D:\Paulo\Cursos\DMC\template-bmad\files\designer-ux\ux_02_notificaciones_whatsapp.md. Por favor, lee el historial, identifica la siguiente Épica pendiente en el backlog y asígnala al BA.
