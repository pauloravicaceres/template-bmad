## 1. HISTORIA DE USUARIO

- **Épica:** Motor Inteligente de Reservas y Disponibilidad
- **Título de la HU:** Selección de servicios, cálculo de duración y reserva de horarios en tiempo real

> **Como** Cliente del spá podológico
> **Quiero** seleccionar uno o varios servicios podológicos, elegir mi podólogo de preferencia y reservar un bloque de horario disponible
> **Para** asegurar mi atención podológica sin sufrir cruces o solapamientos de horario con otros clientes

## 2. ALCANCE ESPECÍFICO (SCOPE)

- **Incluye:**
  - Selección de uno o múltiples servicios podológicos para una misma cita.
  - Elección opcional o obligatoria de un podólogo de preferencia para la atención.
  - Cálculo automático de la duración total requerida sumando las duraciones estimadas de los servicios seleccionados.
  - Consulta y despliegue de bloques de horarios disponibles del podólogo en tiempo real.
  - Validación de disponibilidad para prevenir el solapamiento o reserva doble en un mismo bloque de tiempo.
  - Captura de datos básicos de identificación del cliente (ej. nombre completo y número telefónico) para registrar la cita.
  - Confirmación del registro exitoso de la reserva en el sistema.

- **NO Incluye:**
  - Procesamiento o cobro de pagos en línea (anticipos, señas o reglas de cobro).
  - Aplicación de políticas de cancelación o tiempos límites de anulación.
  - Creación de cuentas de usuario con contraseña o flujos de autenticación complejos (OAuth/JWT).
  - Envío automático de notificaciones por WhatsApp (pertenece a la Épica de Notificaciones Automatizadas).
  - Muestra del catálogo detallado con fotos/reseñas de podólogos (pertenece a la Épica de Vitrina Digital).
  - Gestión o cambio de estados de cita por parte del podólogo (pertenece a la Épica de Panel de Gestión).

## 3. REGLAS DE NEGOCIO

- **RN-01:** El sistema no puede agendar ni permitir la selección de bloques de tiempo en el pasado o fuera del horario operativo.
- **RN-02:** Integridad de Agenda: Bajo ninguna circunstancia el sistema debe permitir el solapamiento o reserva doble en un mismo bloque de tiempo para un profesional podólogo.
- **RN-03:** Acumulación de Duración: La duración total de la reserva se calcula automáticamente sumando el tiempo estimado promedio de cada uno de los servicios seleccionados.
- **RN-04:** Identificación del Cliente: La reserva se asocia a los datos básicos del cliente (nombre y número telefónico) proporcionados en el flujo, sin exigir creación previa de cuenta ni autenticación por contraseña.
- **RN-05:** Neutralidad de Pagos y Políticas: El sistema confirmará la reserva directamente al completar la validación de horario sin requerir pagos en línea ni aplicar retenciones por cancelación.

## 4. CRITERIOS DE ACEPTACIÓN (Gherkin BDD)

**Escenario 1: Reserva exitosa de un solo servicio con podólogo seleccionado (Happy Path)**
- **Dado** que el cliente se encuentra en el flujo de reserva
- **Y** selecciona el servicio "Perfilado Podológico" con una duración estimada de 30 minutos
- **Y** selecciona al podólogo "Dr. Carlos Ruiz"
- **Cuando** solicita ver la disponibilidad y selecciona el bloque de horario del día "2026-09-15" de "10:00 a 10:30"
- **Y** proporciona su nombre "Juan Pérez" y teléfono "+51987654321" para confirmar la reserva
- **Entonces** el sistema valida que el horario de "10:00 a 10:30" está libre para el "Dr. Carlos Ruiz"
- **Y** bloquea el horario en la agenda del profesional
- **Y** confirma el registro exitoso de la reserva en el sistema

**Escenario 2: Reserva multimodular con cálculo automático de duración total**
- **Dado** que el cliente selecciona los servicios "Tratamiento de Uñero" (duración: 45 min) y "Masaje Podológico" (duración: 15 min)
- **Y** selecciona a la podóloga "Dra. María López"
- **Cuando** el cliente consulta la disponibilidad
- **Entonces** el sistema calcula automáticamente una duración total de 60 minutos
- **Y** despliega únicamente los bloques continuos de 60 minutos disponibles en la agenda de la "Dra. María López"

**Escenario 3: Intento de reserva en horario con cruce/solapamiento (Sad Path)**
- **Dado** que la podóloga "Dra. María López" ya tiene una cita reservada de "11:00 a 12:00" el día "2026-09-15"
- **Cuando** otro cliente intenta seleccionar la "Dra. María López" para una cita de 30 minutos en el rango de "11:30 a 12:00" del mismo día
- **Entonces** el sistema no muestra dicho horario como disponible para la selección
- **Y** si se intenta forzar la confirmación, el sistema rechaza la solicitud indicando que el horario ya no se encuentra disponible

**Escenario 4: Confirmación sin pago en línea ni autenticación de cuenta previa**
- **Dado** que el cliente ha completado la selección de servicios, podólogo y horario disponible
- **Cuando** el cliente ingresa su nombre y número de contacto y presiona confirmar
- **Entonces** el sistema registra la reserva como confirmada inmediatamente sin solicitar credenciales de inicio de sesión ni solicitar un pago en línea

## 5. PUNTOS ABIERTOS / DEPENDENCIAS

- **Mecanismo de Autenticación / Identificación Definitivo:** En esta historia se asume la identificación mediante datos básicos (nombre y teléfono) sin credenciales/contraseña para priorizar el MVP. Se requiere que Arquitectura/Producto validen si en iteraciones futuras se requerirá verificación por OTP (código SMS/WhatsApp) para confirmar la titularidad del teléfono.
- **Políticas de Pago e Inasistencia:** No existen reglas de cobro ni señas en el MVP. Si la tasa de *no-show* persiste, Producto deberá definir si se integrará una pasarela de pago o política de retención en futuras versiones.
- **Reglas y Ventanas de Cancelación:** El tiempo límite de anulación queda pendiente de definición para el Módulo de Auto-Gestión y Cancelación (Épica P5).
- **Dependencia de Catálogo (P2):** Requiere de la definición formal de la lista de servicios con sus duraciones estimadas estándar.

## 6. ORDEN DE DELEGACIÓN PARA EL QA

@QA: La Historia de Usuario Selección de servicios, cálculo de duración y reserva de horarios en tiempo real está lista en el archivo hu_01_reserva_disponibilidad.md. Por favor, procede con la auditoría documental contra el Product Brief para asegurar que la historia cumple con los requerimientos originales.
