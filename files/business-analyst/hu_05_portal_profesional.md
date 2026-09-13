## 1. HISTORIA DE USUARIO

- **Épica:** Panel de Gestión de Atenciones (Portal Profesional)
- **Título de la HU:** Visualización y seguimiento de citas agendadas en el Portal Profesional

> **Como** Podólogo / Profesional de la salud podológica
> **Quiero** acceder a un panel digital simplificado donde pueda visualizar mis citas agendadas y dar seguimiento a su estado en tiempo real
> **Para** organizar mi jornada laboral diaria y mantener la agenda de atención actualizada en el spa

## 2. ALCANCE ESPECÍFICO (SCOPE)

- **Incluye:**
  - Vista dedicada en tiempo real de las citas agendadas correspondientes al podólogo autenticado o seleccionado.
  - Despliegue de información clave por cita: Servicio(s), duración total, hora de inicio/fin, y datos de contacto del cliente.
  - Capacidad para consultar y actualizar el estado de la atención (ej. Pendiente / En Atención / Atendida / Anulada).
  - Interfaz simplificada y optimizada bajo diseño responsivo (mobile-first / tablet / PC).

- **NO Incluye:**
  - Registro, edición o baja de podólogos, servicios o bloques de horarios de trabajo (corresponde a un módulo de administración fuera del alcance del MVP).
  - Envío manual de notificaciones (las alertas por WhatsApp son automáticas e integradas en la Épica [P3]).
  - Gestión de cobros, facturación o registro de montos pagados.
  - Visualización o acceso a agendas de otros podólogos (cada profesional accede a su propia agenda asignada).

## 3. REGLAS DE NEGOCIO

- **RN-01:** Filtrado por Especialista: El panel profesional debe mostrar de forma estricta únicamente las citas pertenecientes al podólogo en sesión.
- **RN-02:** Actualización en Tiempo Real: El panel debe refrescar o reflejar de forma inmediata los cambios en la agenda (nuevas reservas o anulaciones por parte del cliente).
- **RN-03:** Transición de Estados de Atención: El podólogo solo puede actualizar el estado de una cita dentro del flujo operativo permitido (ej. de Pendiente a En Atención o Atendida).

## 4. CRITERIOS DE ACEPTACIÓN (Gherkin BDD)

**Escenario 1: Visualización exitosa de la agenda del día (Happy Path)**
- **Dado** que un podólogo accede al Portal Profesional
- **Cuando** consulta su panel de atenciones para una fecha determinada
- **Entonces** el sistema despliega la lista cronológica de citas agendadas con los detalles del cliente, servicios requeridos y rango de horario reservado

**Escenario 2: Actualización del estado de una atención (Happy Path / Seguimiento)**
- **Dado** que el podólogo está atendiendo a un cliente agendado en su panel
- **Cuando** cambia el estado de la cita a "Atendida" o "En Atención"
- **Entonces** el sistema actualiza el registro en tiempo real
- **Y** refleja el nuevo estado en el historial de atenciones del profesional

**Escenario 3: Recepción de actualización en tiempo real por anulación (Happy Path / Sincronización)**
- **Dado** que el podólogo tiene el portal abierto consultando sus citas
- **Cuando** un cliente anula una reserva asignada a dicho podólogo desde la web
- **Entonces** el sistema actualiza el panel del profesional de forma inmediata marcando la cita como "Anulada" y liberando el bloque en su visualizador

## 5. PUNTOS ABIERTOS / DEPENDENCIAS

- **Mecanismo de Autenticación de Podólogos:** El PRD/Product Brief no detalla las credenciales o el método exacto mediante el cual cada podólogo inicia sesión en su Portal Profesional (ej. usuario/contraseña, PIN o enlace directo). Se declara como Punto Abierto.
- **Estados Operativos Finales de la Cita:** Se requiere confirmar los estados exactos permitidos dentro del flujo del spa (ej. "¿Se incluye el estado 'No asistió / Inasistencia'?").

## 6. ORDEN DE DELEGACIÓN PARA EL QA

@QA: La Historia de Usuario Visualización y seguimiento de citas agendadas en el Portal Profesional está lista en el archivo hu_05_portal_profesional.md. Por favor, procede con la auditoría documental contra el Product Brief para asegurar que la historia cumple con los requerimientos originales.
