# Feature Specification: Gestión de Sprint de Dos Semanas (Crear y Consultar)

**Feature Branch**: `feat/003-HU_gestion_sprint_dos_semanas`

**Created**: 2026-10-04

**Status**: 🔗 Consolidado en specs/README.md (Product State Ledger)

**Input**: User description: "documents/business-analyst/003-HU_gestion_sprint_dos_semanas.md"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Crear un Sprint con ventana válida de 2 semanas (Priority: P1)

Como Líder Técnico autenticado, quiero crear un Sprint indicando su identificación y sus fechas de inicio y fin, con la garantía de que abarca exactamente una ventana de 2 semanas, para disponer de los ciclos de trabajo sobre los que se planificará el equipo.

**Why this priority**: Es la capacidad principal de la historia y la base de la planificación: la HU-004 (asignación de elementos al Sprint) no puede avanzar si el Sprint no existe.

**Independent Test**: Se prueba enviando una solicitud de creación con identificación y fechas separadas por 13 días y verificando que el Sprint queda registrado con sus datos y auditoría de creación, sin tocar el backlog.

**Acceptance Scenarios**:

1. **Given** un usuario autenticado y que no existe un Sprint con la identificación "Sprint 2026-01", **When** solicita crear un Sprint con inicio "2026-10-05" y fin "2026-10-18", **Then** el sistema responde HTTP 201 Created con el identificador único, la identificación y las fechas del Sprint, y lo persiste con `CreatedAt` y `CreatedBy` igual al `sub` del token.
2. **Given** la creación exitosa de un Sprint, **When** se revisa el backlog, **Then** no se creó ni modificó ningún elemento del backlog.
3. **Given** una solicitud sin token o con token inválido o expirado, **When** intenta crear un Sprint, **Then** es rechazada con HTTP 401 Unauthorized y no se persiste nada.

---

### User Story 2 - Rechazo de Sprints con datos inválidos (Priority: P1)

Como Líder Técnico, quiero que el sistema rechace cualquier Sprint cuya ventana no sea de 2 semanas o cuyos datos obligatorios falten o estén malformados, para que ningún Sprint inconsistente llegue a persistirse.

**Why this priority**: La restricción de ventana de 2 semanas es una regla de negocio central del Product Brief; sin su validación el módulo pierde su garantía.

**Independent Test**: Se prueba enviando solicitudes con ventanas de 7, 13, 15 y 21 días, fin anterior o igual al inicio, y campos ausentes o con formato inválido, verificando HTTP 400 y ausencia de persistencia en todos los casos.

**Acceptance Scenarios**:

1. **Given** un usuario autenticado, **When** crea un Sprint con una ventana de 7, 13, 15 o 21 días, **Then** el sistema responde HTTP 400 indicando que el Sprint debe abarcar exactamente una ventana de 2 semanas y no persiste nada.
2. **Given** un usuario autenticado, **When** crea un Sprint con fecha de fin anterior o igual a la de inicio, **Then** responde HTTP 400 y no persiste nada.
3. **Given** un usuario autenticado, **When** crea un Sprint con identificación vacía, fecha de inicio o fin ausente, o fecha con formato inválido, **Then** responde HTTP 400 con el detalle de los campos inválidos y no persiste nada.

---

### User Story 3 - Consultar el listado de Sprints (Priority: P2)

Como Líder Técnico autenticado, quiero consultar los Sprints registrados, para conocer los ciclos de trabajo disponibles.

**Why this priority**: Aporta visibilidad sobre lo creado, pero depende de que la creación (P1) funcione.

**Independent Test**: Con Sprints previamente registrados, se solicita el listado y se verifica que contiene exactamente esos Sprints con sus cuatro datos y que no se modificó información.

**Acceptance Scenarios**:

1. **Given** Sprints registrados con ventana válida, **When** el usuario consulta el listado, **Then** el sistema responde HTTP 200 OK con exactamente los Sprints registrados, cada uno con identificador, identificación, fecha de inicio y fecha de fin.
2. **Given** la consulta del listado, **When** se completa, **Then** no se modificó ningún dato.
3. **Given** una solicitud sin credenciales válidas, **When** intenta consultar el listado, **Then** responde HTTP 401 Unauthorized y no se lee ningún dato de Sprint.

---

### User Story 4 - Consultar el detalle de un Sprint (Priority: P2)

Como Líder Técnico autenticado, quiero consultar un Sprint concreto por su identificador, para ver su identificación y sus fechas.

**Why this priority**: Complementa la consulta del listado y es el punto de acceso que usará la HU-004.

**Independent Test**: Se consulta un identificador existente (200 con datos) y uno inexistente (404).

**Acceptance Scenarios**:

1. **Given** un Sprint registrado, **When** el usuario lo consulta por su identificador, **Then** responde HTTP 200 OK con identificador, identificación, fecha de inicio y fecha de fin.
2. **Given** un identificador sin Sprint asociado, **When** el usuario lo consulta, **Then** responde HTTP 404 Not Found indicando que el Sprint no existe.
3. **Given** una solicitud sin credenciales válidas, **When** intenta consultar el detalle, **Then** responde HTTP 401 Unauthorized.

---

### Edge Cases

- ¿Qué pasa si la duración es distinta de 14 días calendario inclusivos (por ejemplo 13 o 15 días)? Se rechaza con HTTP 400 sin persistir (FR-003).
- ¿Qué pasa si la fecha de fin es anterior o igual a la de inicio? Se rechaza con HTTP 400 (FR-004).
- ¿Qué pasa si falta la identificación o alguna fecha, o una fecha tiene formato inválido? Se rechaza con HTTP 400 con la lista de campos inválidos (FR-005).
- ¿Qué pasa si se consulta un Sprint inexistente? HTTP 404 (FR-009).
- ¿Qué pasa si falla la persistencia al crear? HTTP 500 sin trazas internas y sin Sprint parcial (FR-011).
- Sin comportamiento definido, por estar ❓ No documentado en la HU y fuera de alcance: identificación duplicada, solapamiento entre Sprints, fecha de inicio en el pasado, y estados, apertura o cierre del Sprint. No se inventan escenarios para ellos (ver Assumptions).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema DEBE permitir a un usuario autenticado crear un Sprint con identificación, fecha de inicio y fecha de fin.
- **FR-002**: El sistema DEBE asignar a cada Sprint creado un identificador único y devolverlo junto con la identificación y las fechas (HTTP 201 Created).
- **FR-003**: El sistema DEBE rechazar con HTTP 400 todo Sprint cuya ventana no sea exactamente de 14 días calendario consecutivos con ambos extremos incluidos (fecha de fin = fecha de inicio + 13 días), indicando que debe abarcar una ventana de 2 semanas.
- **FR-004**: El sistema DEBE rechazar con HTTP 400 todo Sprint cuya fecha de fin sea anterior o igual a la de inicio.
- **FR-005**: El sistema DEBE rechazar con HTTP 400, con el detalle de los campos inválidos, todo Sprint con identificación vacía, fecha de inicio o fin ausente, o fechas con formato inválido.
- **FR-006**: El sistema DEBE persistir cada Sprint creado con los metadatos de auditoría `CreatedAt` y `CreatedBy`, este último tomado del `sub` del token.
- **FR-007**: El sistema DEBE permitir a un usuario autenticado consultar el listado de Sprints registrados (HTTP 200), devolviendo para cada uno identificador, identificación, fecha de inicio y fecha de fin, sin modificar datos.
- **FR-008**: El sistema DEBE permitir a un usuario autenticado consultar un Sprint por su identificador (HTTP 200), devolviendo identificador, identificación, fecha de inicio y fecha de fin.
- **FR-009**: El sistema DEBE responder HTTP 404 cuando el Sprint consultado no exista.
- **FR-010**: El sistema DEBE rechazar con HTTP 401 toda operación de esta funcionalidad (crear, listar, detalle) sin token, o con token inválido o expirado, sin leer ni persistir datos de Sprint.
- **FR-011**: Ante un fallo de persistencia al crear, el sistema DEBE responder HTTP 500 sin exponer trazas internas y sin dejar ningún Sprint parcial.
- **FR-012**: Toda operación rechazada (400, 401, 500) NO DEBE persistir ningún Sprint.
- **FR-013**: La creación de un Sprint NO DEBE crear ni modificar elementos del backlog, ni establecer relación alguna entre Sprint y tarjetas.
- **FR-014**: El sistema NO DEBE definir ni persistir estados, apertura ni cierre del Sprint, ni permitir su modificación, cancelación o eliminación en esta funcionalidad.
- **FR-015**: Todo Sprint persistido DEBE cumplir la invariante de ventana de 2 semanas de FR-003.
- **FR-016**: La funcionalidad DEBE respetar las restricciones de `.specify/memory/constitution.md` (aislamiento por schema por módulo, sin consultas cross-schema, endpoints protegidos con `.RequireAuthorization()`, manejo centralizado de excepciones).

### Key Entities *(include if feature involves data)*

- **Sprint**: Ciclo de trabajo de 2 semanas. Atributos: identificador único, identificación, fecha de inicio, fecha de fin, `CreatedAt`, `CreatedBy`. No tiene estado ni relación con tarjetas en esta funcionalidad.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un Líder Técnico puede crear un Sprint válido y verlo en el listado en menos de 1 minuto.
- **SC-002**: El 100 % de las solicitudes con ventana distinta de 14 días calendario inclusivos es rechazado sin persistir ningún Sprint, incluidos los límites de ±1 día.
- **SC-003**: El 100 % de los Sprints registrados cumple la ventana de 2 semanas.
- **SC-004**: El 100 % de las solicitudes sin credenciales válidas es rechazado sin exponer datos de Sprint.
- **SC-005**: Las consultas de listado y detalle devuelven resultados en menos de 2 segundos para hasta 100 Sprints registrados.
- **SC-006**: La creación de un Sprint no altera ningún elemento del backlog en el 100 % de los casos verificados.

## Assumptions

- La "ventana de 2 semanas" se interpreta como 14 días calendario consecutivos con extremos incluidos; pendiente de confirmación de negocio (punto abierto 3 de la HU).
- El Líder Técnico es el actor previsto; los permisos exactos por rol no están documentados, por lo que basta un token válido con identidad (patrón de HU-001) (punto abierto 7).
- Los ejemplos de identificación (p. ej. "Sprint 2026-01") son ilustrativos: formato y unicidad de la identificación no están definidos (punto abierto 4), y no se especifica comportamiento ante duplicados.
- Solapamiento entre Sprints y fecha de inicio en el pasado no se validan en esta funcionalidad (puntos abiertos 5 y 6).
- Orden, filtros y paginación del listado no están definidos (punto abierto 9); el listado devuelve todos los Sprints registrados.
- Ciclo de vida del Sprint (estados, apertura, cierre) está bloqueado por una decisión de negocio pendiente y queda fuera de alcance (punto abierto 1); modificación, cancelación y eliminación también (punto abierto 8).
- La pertenencia de tarjetas a uno o varios Sprints (pregunta abierta 9 del Product Brief) no se asume; la asignación es alcance de la HU-004, que depende de esta.
- Dependencia: autenticación con token emitido por el servidor de identidad existente (HU-001).
