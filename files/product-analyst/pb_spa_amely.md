# PRODUCT BRIEF: Ámely - Spá Podológico

## 1. PROBLEMA
¿Qué dolor o necesidad específica se intenta resolver?

* **Hechos (datos comprobables mencionados en la idea):**
  * Ineficiencias operativas y pérdida de tiempo causadas por la gestión manual de citas a través de canales informales en Ámely - Spá Podológico.
  * Ocurrencia recurrente de cruces de horarios entre los profesionales podólogos.
  * Estimaciones imprecisas respecto a la duración promedio de atención de los tratamientos.
  * Alta tasa de inasistencias (no-shows) y cancelaciones de citas que no son notificadas con el tiempo suficiente.

* **Inferencias (deducciones lógicas):**
  * La falta de notificación oportuna de cancelaciones deja huecos vacíos en las agendas, reduciendo el aprovechamiento de la capacidad instalada y la rentabilidad del spá.
  * La gestión informal desorganiza la atención diaria y genera frustración tanto en los clientes como en el equipo de podólogos.

---

## 2. USUARIOS
¿Quiénes experimentan este problema y quiénes interactuarán directamente con la solución?

* **Clientes (Pacientes):** Personas que requieren tratamientos podológicos, consultan los servicios disponibles, seleccionan profesionales de su preferencia, realizan reservas y gestionan o anulan sus citas.
* **Podólogos / Profesionales:** Personal especializado del spá podológico que necesita visualizar su agenda en tiempo real, administrar sus citas programadas y llevar el seguimiento del estado de sus atenciones.

---

## 3. OBJETIVO (OUTCOME)
¿Qué resultado de negocio o cambio de comportamiento se quiere conseguir con esta solución?

* Optimizar operativamente el proceso de agendamiento y mejorar la experiencia global de los clientes y del equipo médico de Ámely - Spá Podológico mediante un aplicativo web moderno, elegante, ligero y 100% responsivo.
* Eliminar por completo los cruces de horarios entre profesionales, automatizar la estimación de tiempos de atención y reducir la tasa de inasistencias mediante notificaciones automáticas por WhatsApp y la autogestión de cancelaciones.

---

## 4. ALCANCE INICIAL
¿Qué límites abarca la solución en esta primera iteración (MVP)?

1. **Vitrina Digital de Podólogos y Servicios:**
   * Presentación visual y detallada del equipo de profesionales podólogos.
   * Catálogo de servicios podológicos con sus respectivos precios explícitos y tiempo promedio estimado de atención.

2. **Motor Inteligente de Reservas y Disponibilidad:**
   * Selección multimodular de servicios en una misma reserva y elección del podólogo de preferencia.
   * Cálculo automático de la duración total requerida sumando los tiempos promedio de los servicios seleccionados.
   * Validación de agenda en tiempo real para bloquear el horario en la agenda del profesional y evitar cruces.

3. **Notificaciones Automatizadas por WhatsApp:**
   * Confirmación automática de reserva enviada por WhatsApp al cliente y al podólogo asignado.
   * Notificación inmediata por WhatsApp al podólogo en caso de anulación o cancelación por parte del cliente.

4. **Panel de Gestión para Podólogos:**
   * Interfaz privada donde el profesional puede visualizar, administrar y dar seguimiento en tiempo real a sus citas y estados de atención.

5. **Módulo de Auto-Gestión y Cancelación para Clientes:**
   * Funcionalidad rápida e intuitiva para que el cliente anule una cita agendada previamente.

---

## 5. RESTRICCIONES
¿Qué condiciones, limitaciones de negocio, regulaciones operativas o reglas inquebrantables deben respetarse?

* **Multiplataforma y Responsividad:** El aplicativo debe ser 100% responsivo y funcional en smartphones, tablets, laptops y PCs.
* **Integridad de Agenda:** No se debe permitir bajo ninguna circunstancia el solapamiento o reserva doble en un mismo bloque de tiempo para un podólogo.
* **Canal de Notificación Mandatorio:** El envío de notificaciones automáticas (confirmación y cancelación) debe ser vía WhatsApp.
* **Límite de Alcance:** El MVP debe ceñirse estrictamente a las funcionalidades descritas, evitando incluir módulos adicionales de negocio no justificados en esta fase inicial.

---

## 6. CRITERIOS DE ÉXITO
¿Qué métricas, indicadores o evidencias (cuantitativas/cualitativas) nos permitirán determinar que la solución logró su objetivo?

* **Cero cruces de agenda:** 0% de solapamiento de citas registradas en los horarios de atención de los podólogos.
* **Reducción de carga operativa manual:** Disminución drástica del tiempo invertido por el personal en agendar y confirmar citas por canales informales.
* **Reducción de Inasistencias:** Disminución en el porcentaje de citas perdidas sin aviso (no-shows) gracias a los recordatorios/confirmaciones por WhatsApp.
* **Eficiencia en la Reasignación:** Incremento de agendas reaprovechadas a partir de notificaciones inmediatas de cancelación al profesional.

---

## 7. SUPUESTOS
¿Qué afirmaciones estamos asumiendo como verdaderas (sobre el mercado, los usuarios o la viabilidad) para que esta idea tenga sentido, pero que aún no han sido validadas?

* Se asume que los clientes de Ámely utilizan WhatsApp activamente y prefieren este medio para recibir confirmaciones de sus reservas.
* Se asume que los podólogos tendrán la disciplina operativa de consultar y actualizar su panel privado para hacer seguimiento a sus atenciones.
* Se asume que las estimaciones de duración promedio por servicio son precisas para la mayoría de los casos típicos de tratamiento podológico.
* Se asume que ofrecer una opción simple de cancelación en línea incentivará a los clientes a anular sus citas con antelación en lugar de simplemente no asistir.

---

## 8. PREGUNTAS ABIERTAS
Listado de preguntas críticas. Incluye aquí cualquier información esencial que falte en la <idea_usuario> y que necesitemos resolver antes de avanzar en la metodología BMAD.

1. **Política de Cancelación:** ¿Existe un tiempo límite mínimo de anticipación (ej. 2, 12 o 24 horas antes) para que un cliente pueda cancelar una cita desde el sistema?
2. **Modelo de Pago:** ¿Las reservas requieren un pago en línea (anticipo/seña) o el cobro se realiza 100% de manera presencial al finalizar la atención?
3. **Autenticación del Cliente:** ¿El cliente necesitará crear una cuenta con contraseña para agendar/cancelar, o el agendamiento y la anulación se realizarán mediante identificadores únicos (ej. número telefónico o código de reserva)?
4. **Proveedor de Servicio WhatsApp:** ¿Se cuenta con un proveedor de API empresarial de WhatsApp definido (ej. Twilio, Meta Business API) o se requiere definir esta factibilidad operativa?
5. **Estados de la Atención:** ¿Qué estados específicos debe registrar el podólogo durante su jornada en el panel privado (ej. *Pendiente*, *En Atención*, *Completado*, *No Asistió*) y si se requiere registrar notas médicas/observaciones en la cita?
