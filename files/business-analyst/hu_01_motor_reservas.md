## 1. HISTORIA DE USUARIO

- **Épica:** Motor Inteligente de Reservas y Disponibilidad en Tiempo Real
- **Título de la HU:** Reserva e Integración de Citas Podológicas en Tiempo Real

> **Como** Cliente del Spa Podológico Ámely  
> **Quiero** seleccionar uno o varios servicios podológicos junto a mi profesional preferido y reservar un bloque de tiempo disponible  
> **Para** agendar mi atención de manera autónoma, inmediata y garantizando que no existan cruces de horario con otros clientes

## 2. ALCANCE ESPECÍFICO (SCOPE)

- **Incluye:**
  - Selección de uno o múltiples servicios podológicos en el flujo de reserva.
  - Selección opcional o asignada de un profesional podólogo.
  - Cálculo automático del tiempo total acumulado sumando la duración promedio de cada servicio seleccionado.
  - Consulta y visualización de bloques de horarios disponibles en tiempo real según la agenda del profesional seleccionado y el tiempo total calculado.
  - Bloqueo y reserva del bloque de tiempo seleccionado para evitar solapamientos o duplicidad de citas.
  - Ocultamiento estricto de valores monetarios o precios durante todo el proceso de reserva.
- **NO Incluye:**
  - Mantenimiento, creación o edición de catálogo de servicios ni perfiles de podólogos (corresponde a administración/configuración).
  - Envío y entrega de notificaciones por WhatsApp (abarcado en Épica P2).
  - Flujo autónomo de consulta o anulación de citas existentes por parte del cliente (abarcado en Épica P4).
  - Visualización del panel de agenda desde la perspectiva del profesional podólogo (abarcado en Épica P5).
  - Procesamiento o cobro de pagos en línea o presenciales.

## 3. REGLAS DE NEGOCIO

- **RN-01 (Sin Precios):** El sistema no debe mostrar ni solicitar información de precios, tarifas o costos acumulados en ningún paso de la selección, consulta de disponibilidad ni confirmación de la reserva.
- **RN-02 (Duración Acumulada):** La duración total de la cita se calcula sumando la duración promedio estimada de cada servicio podológico seleccionado.
- **RN-03 (Bloqueo en Tiempo Real y Cero Cruces):** Al confirmar una reserva, el sistema debe bloquear inmediatamente el bloque de tiempo continuo seleccionado en la agenda del profesional. Ningún otro cliente podrá reservar un horario que se cruce o traslape, total o parcialmente, con una cita ya confirmada.
- **RN-04 (Validación de Disponibilidad):** Un bloque de tiempo solo se presenta como disponible si el profesional cuenta con suficiente tiempo continuo sin interrupciones ni reservas previas para cubrir la duración total acumulada.

## 4. CRITERIOS DE ACEPTACIÓN (Gherkin BDD)

**Escenario 1: Reserva exitosa de cita con profesional y múltiples servicios (Happy Path)**
- **Dado** que el cliente se encuentra en la interfaz del motor de reservas
- **Y** ha seleccionado uno o varios servicios podológicos que suman una duración total calculada
- **Y** ha seleccionado a un profesional podólogo
- **Cuando** solicita consultar los horarios disponibles y selecciona un bloque de tiempo continuo adecuado sin precios visibles
- **Entonces** el sistema valida que el profesional no tenga cruces en ese rango de tiempo
- **Y** registra la reserva bloqueando el bloque horario seleccionado en la agenda en tiempo real

**Escenario 2: Intento de reserva en un horario con cruce o solapamiento (Sad Path)**
- **Dado** que un profesional podólogo ya tiene una cita reservada en el rango de 10:00 a 11:00
- **Cuando** otro cliente intenta seleccionar un rango que se solapa con dicho horario (ej. 10:30 a 11:30) para el mismo profesional
- **Entonces** el sistema no muestra dicho bloque como disponible o rechaza la selección por solapamiento en tiempo real
- **Y** requiere que el cliente seleccione un horario alternativo disponible

**Escenario 3: Verificación de Restricción Inquebrantable de No Precios**
- **Dado** que el cliente realiza la selección de servicios, cálculo de tiempo y confirmación de reserva
- **Cuando** revisa cualquier pantalla o resumen generado dentro del flujo del motor de reservas
- **Entonces** el sistema garantiza que no se despliegue ninguna cifra de precio, costo total ni moneda

## 5. PUNTOS ABIERTOS / DEPENDENCIAS

- **Punto Abierto 1 (Mecanismo de Identificación/Autenticación de Clientes):** El PRD no especifica la forma de identificación del cliente para asociar, consultar o posteriormente gestionar/anular la reserva realizada (ej. número telefónico, documento de identidad, correo electrónico o código de reserva).
- **Punto Abierto 2 (Políticas de Anticipación):** El PRD no define las reglas de tiempo mínimo de anticipación requerido para realizar una reserva (ej. margen mínimo de horas/minutos previos a la cita).
- **Punto Abierto 3 (Horarios Oficiales y Turnos):** Pendiente definir la configuración de horarios de atención del spa y los días/horas de descanso de cada profesional podólogo.
- **Dependencia:** Requiere la integración posterior con la Épica de Notificaciones por WhatsApp (P2) para el envío de alertas de confirmación al cliente y profesional.

## 6. ORDEN DE DELEGACIÓN PARA EL QA

@QA: La Historia de Usuario Reserva e Integración de Citas Podológicas en Tiempo Real está lista en el archivo hu_01_motor_reservas.md. Por favor, procede con la auditoría documental contra el Product Brief para asegurar que la historia cumple con los requerimientos originales.
