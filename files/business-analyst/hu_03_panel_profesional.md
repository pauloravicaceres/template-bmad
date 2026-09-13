## 1. HISTORIA DE USUARIO

- **Épica:** Panel de Gestión de Citas (Portal del Profesional)
- **Título de la HU:** Visualización de agenda diaria y gestión del estado de citas por el podólogo

> **Como** profesional podólogo del spá
> **Quiero** consultar mi agenda diaria en tiempo real, ver el historial de citas de los clientes y actualizar el estado de cada atención
> **Para** gestionar eficientemente mi jornada de trabajo y mantener actualizado el registro de atenciones sin visualizar precios

## 2. ALCANCE ESPECÍFICO (SCOPE)

- **Incluye:**
  - Visualización ordenada de la agenda diaria del podólogo autenticado con el detalle de las citas agendadas (cliente, horario, servicios a realizar).
  - Actualización del estado operacional de la cita por parte del podólogo (estados permitidos: Confirmada, Atendida, Cancelada).
  - Consulta del historial de citas previas del cliente asociado a la atención.
  - Actualización de la disponibilidad de la franja horaria en tiempo real según el cambio de estado de la cita.
  - Ocultamiento estricto de valores monetarios o tarifas en todo el portal del profesional.
- **NO Incluye:**
  - El motor público de reservas multilista por el cliente final (corresponde a la Épica P1).
  - El envío automático de notificaciones por WhatsApp (corresponde a la Épica P2).
  - La cancelación autónoma solicitada por el cliente vía web (corresponde a la Épica P4).
  - Administración de la vitrina digital de servicios o alta/baja de podólogos (corresponde a la Épica P5).

## 3. REGLAS DE NEGOCIO

- **RN-01:** (Privacidad de Agenda) El podólogo únicamente puede acceder a visualizar y gestionar las citas asignadas a su propia agenda.
- **RN-02:** (Estados Operacionales Permitidos) Los únicos estados operacionales seleccionables para una cita son: "Confirmada", "Atendida" y "Cancelada".
- **RN-03:** (Liberación por Cancelación) Si el podólogo cambia el estado de una cita a "Cancelada", la franja horaria correspondiente se libera inmediatamente en la agenda para quedar disponible a nuevas reservas.
- **RN-04:** (Estrategia Comercial de Precios) Ninguna vista del portal del profesional debe mostrar precios, costos ni valores monetarios de los servicios.
- **RN-05:** (Trazabilidad del Historial) El sistema debe mostrar el registro de atenciones anteriores finalizadas ("Atendidas") del cliente al consultar sus datos de cita.

## 4. CRITERIOS DE ACEPTACIÓN (Gherkin BDD)

**Escenario 1: Consulta de agenda diaria actualizada (Happy Path)**
- **Dado** que el podólogo se encuentra autenticado en su portal privado
- **Cuando** ingresa a la vista de su agenda diaria para una fecha seleccionada
- **Entonces** el sistema lista ordenadamente las citas agendadas para esa jornada especificando horario, nombre del cliente y lista de servicios
- **Y** no muestra ningún dato relativo a precios o cobros.

**Escenario 2: Cambio exitoso de estado de cita a "Atendida" (Happy Path)**
- **Dado** que el podólogo está atendiendo una cita agendada en estado "Confirmada"
- **Cuando** selecciona la cita y cambia su estado a "Atendida"
- **Entonces** el sistema actualiza el registro del estado a "Atendida"
- **Y** la cita se añade al historial de atenciones del cliente.

**Escenario 3: Cambio de estado a "Cancelada" y liberación de horario (Happy Path / Liberación)**
- **Dado** que una cita se encuentra registrada como "Confirmada" en la agenda del podólogo
- **Cuando** el podólogo marca la cita con el estado "Cancelada"
- **Entonces** el sistema registra el cambio de estado
- **Y** libera de inmediato el bloque de tiempo correspondiente en la agenda para ser reservado nuevamente.

**Escenario 4: Intento de acceso sin autenticación o a agenda ajena (Sad Path / Seguridad)**
- **Dado** que un usuario no autenticado o un podólogo intenta acceder a la agenda de otro profesional
- **Cuando** solicita la consulta de citas de dicha agenda
- **Entonces** el sistema deniega el acceso
- **Y** muestra un mensaje de restricción de permisos sin desplegar la información de las citas.

## 5. PUNTOS ABIERTOS / DEPENDENCIAS

- **Punto Abierto 1 (Mecanismo de Autenticación de Podólogos):** El PRD no especifica la tecnología ni el método de inicio de sesión para los profesionales (ej. usuario/contraseña, autenticación federada o PIN).
- **Punto Abierto 2 (Edición de Notas o Ficha Clínica):** No se detalla si el podólogo debe poder ingresar notas breves u observaciones técnicas de la atención al marcarla como "Atendida".
