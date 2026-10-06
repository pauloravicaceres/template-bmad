# Feature Specification: Asignación de Elementos del Backlog a un Sprint

**Feature Branch**: `feat/004-HU_asignacion_elementos_sprint`

**Created**: 2026-10-04

**Status**: 🔗 Consolidado en specs/README.md (Product State Ledger)

**Input**: User description: "documents/business-analyst/004-HU_asignacion_elementos_sprint.md"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Asignar un elemento del backlog a un Sprint existente (Priority: P1)

Como Líder Técnico autenticado, quiero asignar un elemento ya registrado del backlog a un Sprint de 2 semanas ya existente, para definir qué trabajo planificado abarca cada ciclo.

**Why this priority**: Es la capacidad principal de la historia; las HU-006 y HU-031 dependen de ella y sin asignación el Sprint no tiene contenido planificable.

**Independent Test**: Con un Sprint y un elemento sin asignar previamente registrados, se solicita la asignación y se verifica que se confirma con los identificadores de ambos, que queda persistida con auditoría y que el elemento conserva sin cambios sus datos.

**Acceptance Scenarios**:

1. **Given** un usuario autenticado, un Sprint registrado y un elemento del backlog que no pertenece a ningún Sprint, **When** solicita asignar ese elemento a ese Sprint, **Then** el sistema confirma la asignación con un código de éxito, la respuesta contiene el identificador del Sprint y el del elemento, y la asignación se persiste con `CreatedAt` y `CreatedBy` igual al `sub` del token.
2. **Given** la asignación exitosa, **When** se revisa el elemento, **Then** conserva sin cambios su título, tipo, estimaciones por rol y estado.
3. **Given** un Sprint y dos elementos distintos sin asignar, **When** el usuario asigna cada uno al Sprint en solicitudes sucesivas, **Then** ambas se confirman y el Sprint queda con exactamente esos dos elementos.

---

### User Story 2 - Consultar los elementos asignados a un Sprint (Priority: P2)

Como Líder Técnico autenticado, quiero consultar los elementos asignados a un Sprint, para verificar de forma observable qué trabajo abarca el ciclo.

**Why this priority**: Hace verificable la asignación, pero depende de que esta (P1) funcione.

**Independent Test**: Con un Sprint con elementos asignados y otro sin ellos, se solicita la consulta de cada uno y se verifica el contenido devuelto y que no se modificó ningún dato.

**Acceptance Scenarios**:

1. **Given** un Sprint con elementos asignados, **When** el usuario consulta sus elementos, **Then** el sistema responde HTTP 200 OK con exactamente los elementos asignados, cada uno con identificador, título, tipo y estimaciones por rol, sin modificar datos.
2. **Given** un Sprint sin elementos asignados, **When** el usuario consulta sus elementos, **Then** responde HTTP 200 OK con una colección vacía.
3. **Given** un identificador de Sprint inexistente, **When** el usuario consulta sus elementos, **Then** responde HTTP 404 Not Found indicando que el Sprint no existe.

---

### User Story 3 - Rechazo de asignaciones inválidas (Priority: P1)

Como Líder Técnico, quiero que el sistema rechace asignaciones a Sprints o elementos inexistentes y solicitudes con identificadores ausentes o malformados, para que no se persista ninguna relación inconsistente.

**Why this priority**: Garantiza la integridad referencial de la planificación; sin ella pueden quedar asignaciones huérfanas.

**Independent Test**: Se envían solicitudes con Sprint inexistente, elemento inexistente y los cuatro casos de identificadores ausentes o malformados, verificando el código de respuesta y que no se persiste nada.

**Acceptance Scenarios**:

1. **Given** un elemento registrado y un identificador de Sprint sin Sprint asociado, **When** se solicita la asignación, **Then** responde HTTP 404 Not Found indicando que el Sprint no existe y no se persiste ninguna asignación.
2. **Given** un Sprint registrado y un identificador de elemento sin elemento asociado, **When** se solicita la asignación, **Then** responde HTTP 404 Not Found indicando que el elemento no existe y no se persiste ninguna asignación.
3. **Given** un identificador de Sprint o de elemento ausente o con formato inválido, **When** se solicita la asignación, **Then** responde HTTP 400 Bad Request con el detalle de los campos inválidos y no se persiste ninguna asignación.

4. **Given** un elemento ya asignado a un Sprint (el mismo u otro), **When** se solicita asignarlo de nuevo, **Then** responde HTTP 409 Conflict sin revelar a qué Sprint pertenece, no se persiste ninguna asignación nueva y la original permanece intacta (FR-017).
5. **Given** dos solicitudes simultáneas para asignar el mismo elemento sin asignar a Sprints distintos, **When** se procesan, **Then** exactamente una responde éxito y la otra HTTP 409 (FR-017).

---

### User Story 4 - Protección de acceso y resiliencia ante fallos (Priority: P1)

Como Líder Técnico, quiero que solo usuarios con credenciales válidas puedan asignar o consultar, y que un fallo interno no deje asignaciones a medias, para confiar en la integridad de la planificación.

**Why this priority**: Es una restricción transversal de seguridad e integridad exigida por la Constitución del proyecto.

**Independent Test**: Se ejecutan ambas operaciones sin token y con token inválido o expirado, y se simula un fallo de persistencia al asignar, verificando 401 y 500 respectivamente y ausencia de datos persistidos parcialmente.

**Acceptance Scenarios**:

1. **Given** una solicitud sin token o con token inválido o expirado, **When** intenta asignar un elemento a un Sprint o consultar los elementos de un Sprint, **Then** responde HTTP 401 Unauthorized y no se lee ni persiste ningún dato de asignación.
2. **Given** un Sprint y un elemento sin asignar, y una persistencia que falla al guardar, **When** se solicita la asignación, **Then** responde HTTP 500 Internal Server Error sin exponer trazas internas y no queda ninguna asignación parcial.

---

### Edge Cases

- ¿Qué pasa si el Sprint solicitado no existe (al asignar o consultar)? HTTP 404 sin persistir (FR-005).
- ¿Qué pasa si el elemento solicitado no existe? HTTP 404 sin persistir (FR-006).
- ¿Qué pasa si falta un identificador o tiene formato inválido? HTTP 400 con la lista de campos inválidos (FR-007).
- ¿Qué pasa si no hay credenciales válidas? HTTP 401 (FR-010).
- ¿Qué pasa si falla la persistencia al asignar? HTTP 500 sin trazas internas y sin asignación parcial (FR-012).
- ¿Qué pasa si el elemento ya está asignado al mismo Sprint, a otro Sprint, o se asigna simultáneamente a dos Sprints? HTTP 409 sin persistir; exactamente una asignación simultánea se confirma (FR-017).
- Sin comportamiento definido, por estar ❓ No documentado en la HU y fuera de alcance: restricciones por estado o fecha del Sprint, elegibilidad del elemento por tipo o estado, y límites de elementos o puntos por Sprint. No se inventan escenarios para ellos (ver Assumptions).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema DEBE permitir a un usuario autenticado asignar un elemento registrado del backlog a un Sprint existente, con un elemento por solicitud.
- **FR-002**: El sistema DEBE confirmar la asignación con un código de éxito y devolver el identificador del Sprint y el del elemento asignado.
- **FR-003**: El sistema DEBE persistir cada asignación con los metadatos de auditoría `CreatedAt` y `CreatedBy`, este último tomado del `sub` del token.
- **FR-004**: El sistema DEBE permitir asignar varios elementos distintos, ninguno asignado previamente, al mismo Sprint en solicitudes sucesivas, quedando el Sprint con exactamente esos elementos.
- **FR-005**: El sistema DEBE responder HTTP 404 indicando que el Sprint no existe cuando el Sprint indicado no exista, tanto al asignar como al consultar, sin persistir nada.
- **FR-006**: El sistema DEBE responder HTTP 404 indicando que el elemento no existe cuando el elemento del backlog indicado no exista, sin persistir ninguna asignación.
- **FR-007**: El sistema DEBE rechazar con HTTP 400, con el detalle de los campos inválidos, toda solicitud de asignación con identificador de Sprint o de elemento ausente o con formato inválido, sin persistir ninguna asignación.
- **FR-008**: El sistema DEBE permitir a un usuario autenticado consultar los elementos asignados a un Sprint (HTTP 200), devolviendo exactamente los elementos asignados, cada uno con identificador, título, tipo y estimaciones por rol, sin modificar datos.
- **FR-009**: El sistema DEBE responder HTTP 200 OK con una colección vacía cuando el Sprint consultado no tenga elementos asignados.
- **FR-010**: El sistema DEBE rechazar con HTTP 401 toda operación de esta funcionalidad (asignar, consultar) sin token, o con token inválido o expirado, sin leer ni persistir datos de asignación.
- **FR-011**: Toda operación rechazada (400, 401, 404, 500) NO DEBE persistir ninguna asignación.
- **FR-012**: Ante un fallo de persistencia al asignar, el sistema DEBE responder HTTP 500 sin exponer trazas internas y sin dejar ninguna asignación parcial.
- **FR-013**: La asignación NO DEBE alterar los datos del elemento (título, tipo, estimaciones por rol, estado) ni los del Sprint (identificación, fechas), ni modificar el comportamiento de las HU-001 y HU-003.
- **FR-014**: La asignación NO DEBE definir ni cambiar el estado del elemento ni del Sprint.
- **FR-015** *(reemplazado por FR-017; resolución humana A, tracker 04-10-2026 10:32)*: un elemento pertenece a un solo Sprint. Ya no se deja indefinida la pertenencia a uno o varios Sprints.
- **FR-017**: El sistema DEBE rechazar con HTTP 409 Conflict toda asignación de un elemento que ya esté asignado a un Sprint (el mismo u otro), sin persistir nada y sin revelar a qué Sprint pertenece. La unicidad se garantiza de forma declarativa (índice único por elemento), de modo que ante solicitudes simultáneas del mismo elemento exactamente una se confirma y las demás responden 409. El orden de evaluación es 400, 401, 404 (Sprint), 404 (elemento), 409.
- **FR-018**: La consulta de elementos asignados DEBE devolver las estimaciones por rol con la misma fidelidad que el elemento del backlog: valores decimales, con `null` cuando el elemento no tiene estimación para el rol; sin redondeo ni conversión de `null` a 0.
- **FR-016**: La funcionalidad DEBE respetar las restricciones de `.specify/memory/constitution.md` (aislamiento por schema por módulo, sin consultas cross-schema, endpoints protegidos con `.RequireAuthorization()`, manejo centralizado de excepciones).

### Key Entities *(include if feature involves data)*

- **Asignación Sprint–Elemento**: Relación entre un Sprint y un elemento del backlog. Atributos: identificador del Sprint, identificador del elemento, `CreatedAt`, `CreatedBy`. No define estado; cada elemento tiene como máximo una asignación (FR-017).
- **Sprint** (preexistente, HU-003): Ciclo de trabajo de 2 semanas; no se modifica.
- **Elemento del backlog** (preexistente, HU-001): Título, tipo, estimaciones por rol y estado; no se modifica.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un Líder Técnico puede asignar un elemento a un Sprint y verlo en la consulta del Sprint en menos de 1 minuto.
- **SC-002**: El 100 % de las solicitudes con Sprint o elemento inexistente, o con identificadores ausentes o malformados, es rechazado sin persistir ninguna asignación.
- **SC-003**: El 100 % de las solicitudes sin credenciales válidas es rechazado sin exponer ni modificar datos de asignación.
- **SC-004**: La consulta de elementos de un Sprint devuelve exactamente los elementos asignados (ni más ni menos) en el 100 % de los casos verificados.
- **SC-005**: La asignación no altera ningún dato del elemento ni del Sprint en el 100 % de los casos verificados.
- **SC-006**: La consulta de elementos de un Sprint devuelve resultados en menos de 2 segundos para hasta 100 elementos asignados.
- **SC-007**: Ante un fallo de persistencia, el 100 % de los casos termina sin asignaciones parciales.

## Assumptions

- El Líder Técnico es el actor previsto; los permisos exactos por rol no están documentados, por lo que basta un token válido con identidad (patrón de HU-001 y HU-003) (punto abierto 6 de la HU).
- Cada solicitud asigna un único elemento a un único Sprint; asignación en lote, desasignación y movimiento entre Sprints quedan fuera de alcance (punto abierto 5).
- Un elemento pertenece a un solo Sprint (resolución humana A a la pregunta abierta 9 y a los puntos abiertos 1 y 8): la asignación repetida o concurrente responde 409 (FR-017).
- La asignación no cambia el estado del elemento (depende de la HU-005) ni se restringe por estado o fecha del Sprint (depende del ciclo de vida de la HU-003) (puntos abiertos 2 y 3).
- No se validan elegibilidad del elemento ni límites de carga o capacidad del Sprint (punto abierto 4; HU-012/013).
- El formato de la consulta (campos adicionales, orden, filtros, paginación) no está definido; se devuelve todo lo asignado con los campos indicados (punto abierto 7).
- La consulta de elementos asignados es ⚠️ [PROPUESTO] y se incluye solo para hacer verificable la asignación.
- Dependencias: HU-003 (el Sprint debe existir), HU-001 (el elemento debe existir) y autenticación con token emitido por el servidor de identidad existente. El mecanismo para validar la existencia del elemento respetando el aislamiento por schema corresponde a Architecture.
