## 1. HISTORIA DE USUARIO

- **Épica:** Dashboard de Gestión para Podólogos y Autogestión de Citas para Clientes
- **Título de la HU:** Visualización de Agenda para Podólogos y Cancelación Autónoma de Citas por Clientes

> **Como** profesional podólogo y cliente del Spá Podológico  
> **Quiero** acceder a un panel con la visualización diaria y semanal de las citas programadas (para el podólogo) y a una opción directa de anulación de reserva (para el cliente)  
> **Para** organizar eficientemente la jornada de atención del equipo podológico y permitir a los clientes liberar de forma autónoma bloques de tiempo cancelados sin mostrar información de precios.

## 2. ALCANCE ESPECÍFICO (SCOPE)

- **Incluye:**
  - Dashboard para podólogos con vistas de agenda diaria y semanal de atenciones programadas (cliente, servicios, bloque horario).
  - Módulo de autogestión de clientes para consultar el estado de su reserva mediante un identificador o enlace directo y ejecutar la cancelación directa.
  - Actualización y liberación inmediata en tiempo real del bloque de agenda cancelado para que vuelva a figurar disponible.
  - Cambio de estado de la reserva de "Confirmada" a "Cancelada".
- **NO Incluye:**
  - Reprogramación autónoma de citas (cambio de fecha/hora) por parte del cliente (excluida del MVP).
  - Exposición de precios, costos o tarifas en la agenda del podólogo o en el módulo de cancelación del cliente.
  - Edición de servicios contratados o reasignación de podólogos desde el dashboard.
  - Notificaciones por WhatsApp directamente generadas por este módulo (la emisión del aviso por WhatsApp ante cancelación se delega a la Épica P2).

## 3. REGLAS DE NEGOCIO

- **RN-01:** La vista del dashboard del podólogo debe mostrar únicamente las citas agendadas asignadas a dicho profesional en modos de vista diaria y semanal, sin incluir precios.
- **RN-02:** El cliente puede anular de forma autónoma su reserva utilizando un enlace o código único de reserva provisto al agendar.
- **RN-03:** Al ejecutarse una cancelación por parte del cliente, el bloque horario asociado debe liberarse inmediatamente en la agenda del podólogo para quedar disponible para nuevas reservas.
- **RN-04:** La interfaz no debe exponer bajo ninguna circunstancia precios o montos cobrados en ninguna de las vistas de podólogo o cliente.
- **RN-05:** El estado de una cita cancelada cambia a "Cancelada" y no puede ser revertido manualmente por el cliente.

## 4. CRITERIOS DE ACEPTACIÓN (Gherkin BDD)

**Escenario 1: Visualización de agenda diaria y semanal por parte del podólogo (Happy Path / Dashboard)**
- **Dado** que el podólogo accede a su panel de gestión
- **Cuando** selecciona la vista diaria o semanal
- **Entonces** el sistema despliega el listado cronológico de atenciones agendadas detallando el nombre del cliente, servicios requeridos y bloque horario asignado sin mostrar precios
- **Y** permite diferenciar claramente las citas confirmadas de los bloques de tiempo libres.

**Escenario 2: Cancelación exitosa de reserva por parte del cliente (Happy Path / Autogestión)**
- **Dado** que un cliente accede al módulo de autogestión con su enlace o código de reserva activa
- **Cuando** solicita la cancelación de su cita y confirma la acción
- **Entonces** el sistema actualiza el estado de la reserva a "Cancelada"
- **Y** libera de forma inmediata el bloque horario en la agenda del podólogo correspondiente
- **Y** muestra un mensaje en pantalla confirmando la anulación de la reserva.

**Escenario 3: Intento de cancelación de una cita previamente cancelada o inexistente (Sad Path / Error Lógico)**
- **Dado** que el cliente ingresa a un enlace o código de reserva que ya fue anulado o no existe
- **Cuando** el cliente intenta acceder o cancelar la reserva
- **Entonces** el sistema valida el estado actual de la cita
- **Y** no permite realizar ninguna acción, mostrando un mensaje informando que la reserva no se encuentra activa o ya fue cancelada previamente.

## 5. PUNTOS ABIERTOS / DEPENDENCIAS

- **Punto Abierto 1 (Políticas y Tiempo Mínimo de Cancelación):** En el PRD y MVP no se define si existe un tiempo límite o ventana mínima de anticipación (ej. cancelar con al menos 2 horas de anticipación) para permitir la anulación autónoma. Por el momento en el MVP la cancelación se permite en cualquier momento previo a la cita.
- **Punto Abierto 2 (Mecanismo de Autenticación / Acceso del Cliente):** Se requiere precisar si el cliente accede a la cancelación a través de un token/hash único enviado en la pantalla de confirmación/WhatsApp o mediante autenticación por número de teléfono.
- **Dependencia:** Esta historia requiere del registro previo de citas generado por el Motor de Reservas (Épica P1, hu_01_reserva_citas.md) y gatilla el evento de cancelación que escucha la Épica de Notificaciones (Épica P2, hu_02_notificaciones_whatsapp.md).

## 6. ORDEN DE DELEGACIÓN PARA EL QA

@QA: La Historia de Usuario Visualización de Agenda para Podólogos y Cancelación Autónoma de Citas por Clientes está lista en el archivo hu_03_dashboard_autogestion.md. Por favor, procede con la auditoría documental contra el Product Brief para asegurar que la historia cumple con los requerimientos originales.
