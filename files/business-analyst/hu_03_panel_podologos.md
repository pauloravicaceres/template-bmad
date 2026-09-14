# ESPECIFICACIÓN DE HISTORIA DE USUARIO

## 1. HISTORIA DE USUARIO

- **Épica:** Panel de Gestión de Citas para Profesionales Podólogos
- **Título de la HU:** Dashboard de Gestión de Citas y Estado de Atención para Podólogos

> **Como** Podólogo del Spá Ámely  
> **Quiero** visualizar mi agenda del día y actualizar el estado de las citas programadas en tiempo real  
> **Para** organizar eficientemente mis atenciones diarias y mantener visibilidad operativa del estado de cada cliente.

## 2. ALCANCE ESPECÍFICO (SCOPE)

- **Incluye:**
  - Dashboard/Panel dedicado de visualización diaria para el podólogo.
  - Listado cronológico de citas programadas para el día o fechas seleccionadas.
  - Visualización del detalle de cada atención: nombre del cliente, servicios solicitados, duración estimada e intervalo de tiempo reservado.
  - Funcionalidad para actualizar manualmente el estado de cada cita (ej. "Programada", "En Atención", "Atendida", "No Asistió").
  - Actualización dinámica e instantánea del panel ante nuevos agendamientos o anulaciones.

- **NO Incluye:**
  - Creación manual de citas desde el panel (las reservas ingresan por el motor público de reservas).
  - Configuración o modificación de horarios/turnos de atención del podólogo desde el panel (corresponde a administración del sistema).
  - Envío manual de notificaciones por WhatsApp desde el panel (las notificaciones se ejecutan automáticamente por la Épica P2).
  - Despliegue de reportes financieros o montos facturados (restringido por la Restricción Comercial).

## 3. REGLAS DE NEGOCIO

- **RN-01 (Aislamiento de Agenda):** Cada podólogo autenticado visualiza por defecto exclusivamente las citas asignadas a su persona.
- **RN-02 (Transición de Estados):** El podólogo puede cambiar progresivamente el estado de la cita respetando la secuencia del flujo de atención.
- **RN-03 (Sincronización en Tiempo Real):** Cualquier cambio en el estado de una cita o cancelación externa debe reflejarse de forma inmediata en el dashboard.
- **RN-04 (Ocultación de Tarifas):** El dashboard de gestión no expondrá precios ni importes de los servicios atendidos.

## 4. CRITERIOS DE ACEPTACIÓN (Gherkin BDD)

**Escenario 1: Visualización de la agenda del día (Happy Path)**
- **Dado** que el podólogo ha accedido a su panel de gestión
- **Cuando** ingresa a la vista del dashboard diario
- **Entonces** el sistema despliega la lista cronológica de todas sus citas asignadas para el día actual
- **Y** muestra para cada cita el nombre del cliente, servicios incluidos, horario de inicio, hora fin y el estado actual de la atención.

**Escenario 2: Actualización exitosa del estado de atención (Happy Path)**
- **Dado** que el podólogo se encuentra en la atención de una cita programada
- **Cuando** selecciona la cita y cambia su estado de "Programada" a "En Atención" o "Atendida"
- **Entonces** el sistema actualiza de inmediato el registro en la base de datos
- **Y** refleja el nuevo estado visualmente en el panel sin requerir la recarga manual de la página.

**Escenario 3: Reflejo en tiempo real de una anulación por el cliente (Happy Path)**
- **Dado** que un podólogo visualiza una cita en estado "Programada" en su dashboard
- **Cuando** el cliente anula dicha cita a través del canal correspondiente
- **Entonces** el panel del podólogo actualiza el estado de la cita a "Anulada" automáticamente
- **Y** libera el bloque de tiempo correspondiente en la vista del día.

**Escenario 4: Intento de visualización de agenda sin citas programadas (Sad Path / Flujo Alternativo)**
- **Dado** que el podólogo ingresa a su dashboard en un día determinado
- **Y** no cuenta con reservas registradas para esa fecha
- **Cuando** el sistema carga la agenda
- **Entonces** muestra un mensaje indicando "No tienes citas programadas para esta fecha" y permite navegar a otros días.

## 5. PUNTOS ABIERTOS / DEPENDENCIAS

- **PA-01 (Mecanismo de Autenticación de Podólogos):** No se especifica en el PRD la tecnología ni el método de inicio de sesión de los podólogos (ej. usuario/contraseña, PIN de acceso o SSO).
- **PA-02 (Definición de Matriz de Estados):** Falta la definición formal del catálogo de estados autorizados para una cita y sus reglas de transición (ej. ¿Se permite marcar "No asistió" de forma retroactiva?).
- **PA-03 (Permisos Inter-profesionales):** No se especifica si un podólogo podrá ver la agenda de sus colegas o si el acceso debe ser estrictamente exclusivo.
- **DEP-01 (Autenticación y Perfiles):** Depende del módulo de gestión de usuarios y roles para la identificación de cada profesional podólogo.
