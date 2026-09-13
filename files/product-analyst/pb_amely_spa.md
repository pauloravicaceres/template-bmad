# PRODUCT BRIEF: Ámely - Spá Podológico

## 1. PROBLEMA
¿Qué dolor o necesidad específica se intenta resolver?

- **Hechos comprobables (mencionados explícitamente):**
  - Ineficiencias operativas causadas por la gestión manual de citas.
  - Ocurrencia de solapamientos en las agendas de los profesionales podólogos.
  - Imprecisiones al calcular la duración de atenciones combinadas (múltiples servicios).
  - Atención al cliente lenta.
- **Inferencias lógicas:**
  - La lentitud en la atención y los errores en la agenda generan fricción y posible insatisfacción en la experiencia del cliente.
  - La desorganización manual incrementa la carga administrativa del personal del spá.

## 2. USUARIOS
¿Quiénes experimentan este problema y quiénes interactuarán directamente con la solución?

- **Clientes del Spá Podológico:** Personas que buscan agendar, consultar servicios/especialistas y anular citas de manera autónoma, rápida y sencilla desde cualquier dispositivo (móvil, tablet, laptop, PC).
- **Profesionales Podólogos:** Especialistas de la clínica que consultan su agenda individual, revisan los servicios requeridos por cliente y realizan el seguimiento de sus atenciones programadas.
- **Administradores / Personal de Recepción:** Información no proporcionada (el requerimiento inicial no menciona funciones de administración o recepción general).

## 3. OBJETIVO (OUTCOME)
¿Qué resultado de negocio o cambio de comportamiento se quiere conseguir con esta solución?

- Automatizar íntegramente la reserva e integración de agendas para erradicar solapamientos y reducir los tiempos de atención al cliente.
- Ofrecer una experiencia web de usuario moderna, elegante y ligera adaptable a cualquier dispositivo.
- Garantizar una comunicación fluida e inmediata mediante notificaciones automáticas por WhatsApp para confirmaciones y cancelaciones de citas.
- Proveer a cada podólogo un mecanismo claro y accesible para el seguimiento de sus atenciones asignadas.

## 4. ALCANCE INICIAL
¿Qué límites abarca la solución en esta primera iteración (MVP)?

1. **Catálogo Digital de Servicios y Especialistas:** Muestra del equipo de podólogos y de la oferta de servicios podológicos incluyendo su tiempo promedio de atención (excluyendo precios).
2. **Motor de Reservas e Integración de Agenda:** Selección flexible de uno o varios servicios y profesional de preferencia; cálculo dinámico y automático del tiempo total de atención; reserva del bloque horario exacto y validación de disponibilidad en tiempo real para evitar reservas duplicadas o cruzadas.
3. **Notificaciones por WhatsApp:** Envío inmediato de confirmación de cita (al cliente y podólogo) y de cancelación de cita (al podólogo).
4. **Módulo de Anulación de Citas:** Funcionalidad para que el cliente anule una cita previamente programada desde la web.
5. **Panel de Gestión de Atenciones para Podólogos:** Dashboard individual por profesional para consultar su agenda, revisar servicios solicitados por cliente y dar seguimiento a sus atenciones programadas.

## 5. RESTRICCIONES
¿Qué condiciones, limitaciones de negocio, regulaciones operativas o reglas inquebrantables deben respetarse?

- **Ocultamiento de Precios:** Por políticas estrictas de negocio, NO se deben mostrar los precios de los servicios en el catálogo ni durante la reserva.
- **Multiplataforma:** La aplicación web debe ser ligera, moderna y totalmente adaptativa a cualquier pantalla (PCs, laptops, tablets y móviles).
- **Integridad de Agendas:** La validación en tiempo real debe impedir totalmente reservas duplicadas o cruzadas entre podólogos.

## 6. CRITERIOS DE ÉXITO
¿Qué métricas, indicadores o evidencias (cuantitativas/cualitativas) nos permitirán determinar que la solución logró su objetivo?

- Reducción al 0% de solapamientos o citas duplicadas en las agendas de los podólogos.
- Eliminación total de imprecisiones en el cálculo de duración para reservas de servicios combinados.
- Disminución del tiempo de espera de los clientes al agendar y recibir confirmaciones.
- 100% de efectividad en la entrega inmediata de notificaciones de confirmación y anulación vía WhatsApp.

## 7. SUPUESTOS
¿Qué afirmaciones estamos asumiendo como verdaderas para que esta idea tenga sentido, pero que aún no han sido validadas?

- Los clientes disponen de un dispositivo con conexión a internet y cuentan con una cuenta de WhatsApp activa para recibir sus notificaciones.
- Los podólogos cuentan con dispositivos (personales o de la clínica) para revisar su dashboard individual durante la jornada laboral.
- Los tiempos promedios definidos para cada servicio podológico son precisos y suficientes para atender adecuadamente al cliente.

## 8. PREGUNTAS ABIERTAS
Listado de preguntas críticas que requieren aclaración antes de continuar con la metodología BMAD:

1. **Gestión de Reprogramaciones:** ¿El cliente o la clínica podrán reprogramar (cambiar fecha/hora) una cita existente o deberá anularse y crearse una nueva?
2. **Políticas de Anulación:** ¿Existe un límite de tiempo previo (ej. máximo 2 horas antes de la cita) para que el cliente pueda anular su reserva?
3. **Autenticación e Identificación:** ¿Cómo se identifica o autentica el cliente al momento de agendar y anular una cita (ej. número celular, correo, DNI, código enviado por WhatsApp)?
4. **Administración General:** ¿Se requiere un módulo o rol de Administrador para gestionar el alta/baja de especialistas, servicios, horarios de atención generales y descansos?
5. **Proveedor de WhatsApp:** ¿Existe alguna preferencia o proveedor seleccionado para la API/servicio de envío de notificaciones de WhatsApp?
