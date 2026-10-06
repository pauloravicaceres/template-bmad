# Feature Specification: Registro de Elementos en Backlog Multitipo

**Feature Branch**: `feat/001-HU_registro_elementos_backlog_multitipo`

**Created**: 2026-10-03

**Status**: 🔗 Consolidado en specs/README.md (Product State Ledger)

**Input**: User description: "documents/business-analyst/001-HU_registro_elementos_backlog_multitipo.md"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Registro completo de Historia de Usuario (Priority: P1)

Como Líder Técnico o Miembro del Equipo de Desarrollo/QA autenticado, quiero registrar un elemento de tipo Historia de Usuario con estimaciones independientes para desarrollo y QA.

**Why this priority**: Es la funcionalidad principal (Happy Path) que permite alimentar el backlog para la planificación de Sprints.

**Independent Test**: Puede ser probado enviando un payload completo a la API y verificando la creación exitosa del registro con los puntos separados por rol.

**Acceptance Scenarios**:

1. **Given** que el usuario cuenta con un token JWT válido, **When** el cliente envía un POST a `/api/backlog/items` con datos completos, **Then** el sistema responde HTTP 201 Created y persiste el elemento con los `devPoints` y `qaPoints`.
2. **Given** un intento de registro sin token, **When** se hace la solicitud, **Then** es rechazada con HTTP 401 Unauthorized.

---

### User Story 2 - Registro de elemento técnico sin estimación de QA (Priority: P2)

Como usuario autenticado, quiero registrar una investigación técnica preliminar (Spike) que no requiere puntos de QA.

**Why this priority**: Es un caso común en elementos técnicos que no requieren validación funcional por parte del QA.

**Independent Test**: Puede ser probado enviando un elemento tipo `Spike` con `qaPoints` igual a nulo y verificando que se almacena correctamente.

**Acceptance Scenarios**:

1. **Given** un payload de tipo `Spike` con `qaPoints` nulo, **When** el usuario lo envía al endpoint, **Then** el sistema responde con HTTP 201 Created y el campo `qaPoints` se almacena como nulo.

---

### Edge Cases

- ¿Qué pasa si se envía un campo `title` vacío o excesivamente largo? El sistema debe validarlo y rechazarlo con HTTP 400 (ValidationException).
- ¿Qué sucede si el `type` enviado no está en el catálogo oficial (UserStory, Bug, TechEvolution, TechRequirement, TechDebt, Research, Spike)? El sistema debe rechazarlo con HTTP 400.
- ¿Cómo se maneja un intento de establecer estimaciones numéricas negativas? La validación debe bloquearlo y devolver HTTP 400 indicando que los puntos deben ser >= 0.
- ¿Qué pasa si el `applicationId` provisto no existe en la base de datos? Debe retornar HTTP 400 (NotFoundException) fallando la validación de integridad.
- ¿Qué pasa si se envía `qaPoints` con valor para un ítem de tipo técnico (`TechEvolution`, `TechRequirement`, `TechDebt`, `Research`, `Spike`)? El sistema debe rechazarlo con HTTP 400 indicando que los ítems técnicos no admiten puntos de QA; no se descarta el valor en silencio (FR-008).
- ¿Qué pasa si falta el claim de identidad del usuario al auditar `CreatedBy`? La petición se rechaza con HTTP 401; nunca se persiste un `CreatedBy` vacío (FR-009).
- ¿Qué pasa si `description` o `acceptanceCriteria` exceden el límite? El sistema debe rechazarlo con HTTP 400 (FR-012).
- ¿Qué pasa si la conexión a base de datos falla al guardar el registro? La transacción falla (HTTP 500) y ningún evento de dominio es emitido al bus.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema DEBE exponer un endpoint POST `/api/backlog/items` asegurado mediante Bearer token.
- **FR-002**: El sistema DEBE persistir elementos de backlog en la base de datos de PostgreSQL con un identificador único (UUID).
- **FR-003**: El sistema DEBE forzar que todo nuevo elemento registrado ingrese con el estado inicial inmutable de `Backlog`.
- **FR-004**: El sistema DEBE validar que el título no esté vacío y no exceda los 200 caracteres.
- **FR-005**: El sistema DEBE validar que el tipo de elemento pertenezca al catálogo permitido.
- **FR-006**: El sistema DEBE validar que los puntos de estimación (`devPoints` y `qaPoints`), si están presentes, sean mayores o iguales a 0.
- **FR-007**: El sistema DEBE verificar la existencia de `applicationId` si este es proporcionado en la carga útil.
- **FR-008**: El sistema DEBE disociar el esfuerzo estimativo permitiendo almacenar valores nulos para los puntos de QA en ítems técnicos. Para un ítem técnico, `qaPoints` DEBE ser nulo: si llega con valor se rechaza con HTTP 400 (no se descarta en silencio). La regla es un invariante del agregado `BacklogItem`, no solo del handler ni del cliente. Para `UserStory` y `Bug`, un `qaPoints` ausente se persiste como nulo ("no estimado"); el cliente no debe enviar `0` como valor por defecto.
- **FR-009**: El sistema DEBE inyectar automáticamente metadatos de auditoría (`CreatedAt` y `CreatedBy`). `CreatedBy` se toma del claim de identidad del token JWT; si el claim falta, la petición se rechaza con HTTP 401.
- **FR-010**: El sistema DEBE publicar un evento de dominio (`BacklogItemCreatedDomainEvent`) internamente mediante MediatR una vez completada la persistencia.
- **FR-011**: El sistema DEBE aceptar y persistir la prioridad (`priority`) del elemento, con valores del catálogo `Low`, `Medium`, `High`, `Critical`. En JSON se serializa como texto (p. ej. `"High"`), no como entero.
- **FR-012**: El sistema DEBE aceptar y persistir los criterios de aceptación (`acceptanceCriteria`, texto opcional). `description` y `acceptanceCriteria` tienen un límite máximo de longitud definido en el plan.
- **FR-013**: Toda respuesta HTTP 400 DEBE usar el formato `ProblemDetails` con el diccionario `errors` por campo (incluidos los fallos de `applicationId` inexistente), de modo que el cliente muestre el error específico leyendo `errors`.

### Key Entities *(include if feature involves data)*

- **BacklogItem**: Representa un elemento de trabajo dentro de la planificación ágil. Sus atributos principales son Id, Title, Description, Type, Priority, AcceptanceCriteria, Status, DevPoints, QAPoints, ApplicationId y metadatos de auditoría.
- **Application**: Entidad externa a la que puede vincularse un elemento de backlog mediante `applicationId`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% de las peticiones para crear elementos de backlog con formato válido y autenticado persisten en base de datos.
- **SC-002**: 100% de los elementos creados publican su evento de dominio correspondiente tras confirmarse la transacción de DB.
- **SC-003**: El sistema rechaza en menos de 200ms todas las peticiones que no cumplan con el contrato o esquemas permitidos (400 Bad Request).
- **SC-004**: Tiempos de respuesta de creación bajo 500ms en condiciones normales.

## Assumptions

- Se asume que el token JWT es gestionado por Keycloak.
- Se asume que el esquema de base de datos (`BacklogItems`) será aprovisionado en una migración previa o concurrente a este desarrollo.
- Se asume que la validación de integridad referencial para `applicationId` puede completarse consultando el módulo de aplicaciones dentro de la red del monolito modular.
