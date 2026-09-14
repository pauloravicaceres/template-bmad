## 1. HISTORIA DE USUARIO

- **Épica:** Panel de Gestión de Citas para Profesionales Podólogos
- **Título de la HU:** Consulta y Monitoreo de Agenda Diaria para Podólogos

> **Como** Profesional Podólogo del Spa Ámely  
> **Quiero** acceder a un panel privado para consultar y monitorear mi agenda diaria de citas en tiempo real  
> **Para** organizar mi jornada laboral, dar seguimiento al flujo de atenciones asignadas y verificar los detalles de cada cita sin visualizar precios

## 2. ALCANCE ESPECÍFICO (SCOPE)

- **Incluye:**
  - Acceso privado al panel de gestión de citas para el profesional podólogo.
  - Visualización cronológica de la agenda diaria de atenciones en tiempo real.
  - Consulta del detalle de cada cita: cliente asignado, lista de servicios a realizar, horario de inicio y fin, y estado de la atención (ej. reservada, en proceso, completada, anulada).
  - Ocultamiento estricto de cualquier tarifa, costo acumulado o importe monetario en las fichas de las citas.
- **NO Incluye:**
  - Gestión de cobros, facturación o comisiones del profesional.
  - Modificación de horarios de atención general del spa o altas de servicios.
  - Creación manual de nuevas citas desde el panel (el flujo de agendamiento proviene del cliente en P1).
  - Notificaciones salientes por WhatsApp (abarcado en Épica P2).

## 3. REGLAS DE NEGOCIO

- **RN-01 (Sin Precios en Panel):** El panel de gestión de los profesionales podólogos no debe mostrar datos financieros, precios de servicios ni ingresos generados.
- **RN-02 (Actualización en Tiempo Real):** La agenda del profesional debe reflejar de forma inmediata cualquier nueva reserva realizada o anulación confirmada por los clientes.
- **RN-03 (Privacidad por Profesional):** Cada podólogo consulta únicamente las citas y bloqueos pertenecientes a su propia agenda de atención.

## 4. CRITERIOS DE ACEPTACIÓN (Gherkin BDD)

**Escenario 1: Consulta de agenda diaria de atenciones (Happy Path)**
- **Dado** que el profesional podólogo accede a su panel privado de gestión
- **Cuando** selecciona la fecha de consulta (por defecto, el día actual)
- **Entonces** el sistema lista ordenadamente todas las citas asignadas para esa jornada mostrando cliente, rango de horario, servicios a realizar y estado de la cita
- **Y** garantiza que no aparezca ninguna información de precios o importes

**Escenario 2: Actualización en tiempo real por nueva reserva o cancelación**
- **Dado** que el profesional se encuentra visualizando su panel de agenda del día
- **Cuando** un cliente agenda una nueva cita o anula una existente asignada a dicho profesional
- **Entonces** el panel actualiza automáticamente la lista de atenciones reflejando el nuevo bloqueo o la liberación del espacio sin necesidad de recargar manualmente la página

**Escenario 3: Verificación de Prohibición de Precios en el Panel Privado**
- **Dado** que el profesional revisa el detalle de cualquiera de sus atenciones en el panel
- **Cuando** examina la información de los servicios o clientes
- **Entonces** el sistema omite estrictamente cualquier campo o valor numérico de precios o tarifas

## 5. PUNTOS ABIERTOS / DEPENDENCIAS

- **Punto Abierto 1 (Mecanismo de Autenticación de Podólogos):** El PRD indica que el panel es privado pero no especifica el método de inicio de sesión/autenticación para los profesionales (ej. credenciales usuario/contraseña, PIN de acceso).
- **Punto Abierto 2 (Manejo de Inasistencias y Retrasos):** Pendiente definir en el PRD la funcionalidad o estados para registrar "No-show" (cliente no se presentó) o retrasos dentro del panel.
- **Dependencia:** Se conecta con el Motor de Reservas (P1) para recibir las reservas creadas y con el Módulo de Anulación (P4) para actualizar las cancelaciones.

## 6. ORDEN DE DELEGACIÓN PARA EL QA

@QA: La Historia de Usuario Consulta y Monitoreo de Agenda Diaria para Podólogos está lista en el archivo hu_05_panel_profesionales.md. Por favor, procede con la auditoría documental contra el Product Brief para asegurar que la historia cumple con los requerimientos originales.
