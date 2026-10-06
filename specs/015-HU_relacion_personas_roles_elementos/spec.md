# Feature Specification: Relación entre Personas, Roles y Elementos de Trabajo

**Feature Branch**: `feat/015-HU_relacion_personas_roles_elementos`

**Created**: 2026-10-04

**Status**: 🔗 Consolidado en specs/README.md (Product State Ledger)

**Input**: User description: "documents/business-analyst/015-HU_relacion_personas_roles_elementos.md"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Asignar miembros como responsables de un elemento del backlog (Priority: P1)

Como Líder Técnico autenticado, quiero asignar a miembros del equipo registrados como responsables de un elemento del backlog (uno o más por elemento), para que cada tarjeta quede relacionada con las personas que la trabajan y con su rol técnico.

**Why this priority**: Es la capacidad principal de la historia y habilita el criterio de éxito "tarjetas consultables con responsable y rol"; HU-010 y las vistas de carga por persona dependen de esta relación.

**Independent Test**: Con un elemento "item-101" y los miembros "Ana Torres" (Desarrollo) y "Luis Rojas" (QA), se asigna a cada uno como responsable y se verifica que cada asignación se confirma con elemento, miembro y rol, que queda persistida con auditoría, que la asignación del segundo no altera la del primero y que las estimaciones, el estado y el Sprint del elemento no cambian.

**Acceptance Scenarios**:

1. **Given** un usuario autenticado, el elemento "item-101" y el miembro "Ana Torres" con rol "Desarrollo", **When** solicita asignar a "Ana Torres" como responsable de "item-101", **Then** el sistema confirma la asignación con un código de éxito, la respuesta contiene el identificador del elemento, el identificador y nombre del miembro y su rol "Desarrollo", la relación se persiste con `CreatedAt` y `CreatedBy` igual al `sub` del token, y `devPoints`, `qaPoints`, estado y Sprint del elemento permanecen sin cambios.
2. **Given** un usuario autenticado, "item-101" con responsable "Ana Torres" (Desarrollo) y el miembro "Luis Rojas" con rol "QA", **When** solicita asignar a "Luis Rojas" como responsable de "item-101", **Then** el sistema confirma la asignación, "item-101" queda relacionado con "Ana Torres" (Desarrollo) y "Luis Rojas" (QA), y la relación previa con "Ana Torres" permanece intacta.

---

### User Story 2 - Consultar las personas y roles relacionados con un elemento (Priority: P2)

Como Líder Técnico autenticado, quiero consultar qué personas, con qué rol técnico, están relacionadas con un elemento del backlog, para ver el trabajo junto con su responsable.

**Why this priority**: Hace observable la relación en el sentido tarjeta→personas, pero depende de que la asignación (P1) funcione. Es una capacidad ⚠️ [PROPUESTO].

**Independent Test**: Con un elemento con dos responsables y otro sin responsables, se solicita la consulta de cada uno y se verifica el contenido devuelto y que no se modificó ningún dato.

**Acceptance Scenarios**:

1. **Given** un usuario autenticado y "item-101" con responsables "Ana Torres" (Desarrollo) y "Luis Rojas" (QA), **When** consulta las personas relacionadas con "item-101", **Then** el sistema responde HTTP 200 OK con exactamente esas dos personas, cada una con identificador, nombre y rol, sin modificar datos.
2. **Given** un usuario autenticado y un elemento sin responsables, **When** consulta las personas relacionadas con ese elemento, **Then** el sistema responde HTTP 200 OK con una colección vacía.

---

### User Story 3 - Consultar los elementos relacionados con un miembro (Priority: P2)

Como Líder Técnico autenticado, quiero consultar qué elementos del backlog tiene relacionados un miembro del equipo, para ver su trabajo asignado.

**Why this priority**: Completa la consulta en el sentido persona→tarjetas y es dato de entrada de las vistas de carga por persona. Depende de P1. Es ⚠️ [PROPUESTO].

**Independent Test**: Con "Ana Torres" como responsable de "item-101" y "item-102", se solicita la consulta y se verifica que devuelve exactamente esos dos elementos con identificador, título y tipo, sin modificar datos.

**Acceptance Scenarios**:

1. **Given** un usuario autenticado y "Ana Torres" responsable de "item-101" y "item-102", **When** consulta los elementos relacionados con "Ana Torres", **Then** el sistema responde HTTP 200 OK con exactamente "item-101" y "item-102", cada uno con identificador, título y tipo, sin modificar datos.

---

### User Story 4 - Rechazo de asignaciones con referencias inexistentes o inválidas (Priority: P1)

Como Líder Técnico, quiero que el sistema rechace asignaciones con un miembro o un elemento inexistente, o con identificadores ausentes o con formato inválido, para que no se persistan relaciones inconsistentes.

**Why this priority**: Garantiza la integridad de la relación; sin estas validaciones podrían persistirse relaciones huérfanas. Es ⚠️ [PROPUESTO].

**Independent Test**: Se solicitan asignaciones con miembro inexistente, elemento inexistente y combinaciones de identificadores ausentes o mal formados, y se verifica el rechazo correspondiente y que no se persistió ninguna relación.

**Acceptance Scenarios**:

1. **Given** un usuario autenticado, un elemento existente y un identificador de miembro que no existe, **When** solicita la asignación, **Then** el sistema responde HTTP 404 Not Found indicando que el miembro no existe y no persiste ninguna relación.
2. **Given** un usuario autenticado, un miembro existente y un identificador de elemento que no existe, **When** solicita la asignación, **Then** el sistema responde HTTP 404 Not Found indicando que el elemento no existe y no persiste ninguna relación.
3. **Given** un usuario autenticado, **When** solicita asignar con elemento ausente, miembro ausente, elemento con formato inválido o miembro con formato inválido, **Then** el sistema responde HTTP 400 Bad Request con el detalle de los campos inválidos y no persiste ninguna relación.

---

### User Story 5 - Protección de acceso y robustez ante fallos (Priority: P1)

Como organización, quiero que ninguna operación de relaciones esté disponible sin credenciales válidas y que un fallo de persistencia no deje datos parciales ni exponga detalles internos, para proteger la información y la consistencia.

**Why this priority**: Es una restricción transversal de seguridad y consistencia exigida por la Constitución del proyecto.

**Independent Test**: Se invocan las tres operaciones sin token, con token inválido y con token expirado, y se simula un fallo de persistencia al asignar.

**Acceptance Scenarios**:

1. **Given** una solicitud sin token o con token inválido o expirado, **When** intenta asignar un responsable, consultar las personas de un elemento o consultar los elementos de un miembro, **Then** el sistema responde HTTP 401 Unauthorized y no lee ni persiste ningún dato de relaciones, miembros ni elementos.
2. **Given** un usuario autenticado, el elemento "item-101", el miembro "Ana Torres" y una persistencia que falla al guardar, **When** solicita la asignación, **Then** el sistema responde HTTP 500 Internal Server Error sin exponer trazas internas y no queda registrada ninguna relación parcial.

---

### Edge Cases

- Asignar al mismo miembro dos veces al mismo elemento: comportamiento no documentado (rechazar, idempotencia o duplicar); sin escenario hasta definirlo.
- Número máximo de responsables por elemento: no documentado; no se restringe.
- Quitar o reemplazar un responsable ya asignado (y el evento "cambio de responsable" del historial): no documentado y fuera de alcance; no se restringe.
- Asignar un miembro cuyo rol técnico no coincide con las estimaciones del elemento (p. ej. QA en un elemento con `qaPoints` nulo): no documentado; no se restringe.
- Asignar responsables según el estado del elemento o su pertenencia a un Sprint: no documentado; no se restringe.
- Permisos por rol de acceso para asignar y consultar: no documentado; solo se exige un token válido con identidad.
- Consulta sobre un elemento sin responsables: devuelve una colección vacía, no un error.
- Un fallo en la asignación no debe dejar ninguna relación parcial.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST permitir a un usuario autenticado asignar a un miembro del equipo registrado como responsable de un elemento del backlog existente, relacionando un miembro con un elemento por solicitud.
- **FR-002**: El sistema MUST permitir más de un responsable por elemento y MUST conservar intactas las relaciones previas al asignar un responsable adicional.
- **FR-003**: Al confirmar una asignación, el sistema MUST responder con un código de éxito y devolver el identificador del elemento, el identificador y nombre del miembro y su rol técnico registrado.
- **FR-004**: El sistema MUST persistir cada relación con metadatos de auditoría `CreatedAt` y `CreatedBy`, siendo este último el `sub` del token.
- **FR-005**: El sistema MUST mostrar como rol de la relación el rol técnico que el miembro ya tiene registrado, sin permitir elegir otro rol por asignación.
- **FR-006**: El sistema MUST permitir consultar las personas relacionadas con un elemento, devolviendo para cada una identificador, nombre y rol, o una colección vacía si no hay ninguna.
- **FR-007**: El sistema MUST permitir consultar los elementos relacionados con un miembro, devolviendo para cada uno identificador, título y tipo.
- **FR-008**: Las consultas MUST NOT modificar ningún dato.
- **FR-009**: El sistema MUST rechazar con HTTP 404 la asignación cuando el miembro no existe o cuando el elemento no existe, indicando cuál de los dos falta, sin persistir relación alguna.
- **FR-010**: El sistema MUST rechazar con HTTP 400 y detalle de los campos inválidos la asignación con identificador de elemento o de miembro ausente o con formato inválido, sin persistir relación alguna.
- **FR-011**: El sistema MUST rechazar con HTTP 401 toda solicitud de asignación o consulta sin token válido, sin leer ni persistir datos de relaciones, miembros ni elementos.
- **FR-012**: Ante un fallo de persistencia al asignar, el sistema MUST responder HTTP 500 sin exponer trazas internas y sin dejar relaciones parciales.
- **FR-013**: La asignación MUST NOT alterar las estimaciones `devPoints` y `qaPoints` del elemento, su estado, su pertenencia a un Sprint, el registro del miembro ni su rol técnico, ni modificar el comportamiento observable de HU-001, HU-003, HU-004 ni HU-012.
- **FR-014**: El sistema MUST respetar el aislamiento por schema de cada módulo: los datos de miembros y roles pertenecen al módulo de equipos y los de elementos al módulo de backlog, sin consultas cruzadas entre schemas.
- **FR-015**: El sistema MUST NOT asumir ni imponer reglas sobre asignaciones duplicadas, máximo de responsables, baja o reemplazo de responsables, coherencia entre rol y estimaciones, ni restricciones por estado o Sprint del elemento, hasta que se definan.

### Key Entities *(include if feature involves data)*

- **Relación de responsabilidad**: Vínculo entre un elemento del backlog y un miembro del equipo, identificado por ambos; incluye metadatos de auditoría (`CreatedAt`, `CreatedBy`). Un elemento puede tener varias y un miembro puede aparecer en varias.
- **Miembro del equipo**: Persona registrada (HU-012) con identificador, nombre y rol técnico; a través de él la relación expone el rol.
- **Elemento del backlog**: Tarjeta multitipo (HU-001) con identificador, título, tipo, estimaciones Dev y QA, estado y Sprint; no es modificada por esta capacidad.
- **Rol técnico**: Clasificación del miembro (p. ej. Desarrollo, QA) definida en HU-012; se muestra tal cual en la relación.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 100 % de las asignaciones válidas se confirman mostrando elemento, miembro y rol, y quedan consultables de inmediato en ambos sentidos.
- **SC-002**: Un Líder Técnico puede asignar un responsable a una tarjeta y verificar la relación en menos de 1 minuto.
- **SC-003**: El 100 % de las asignaciones con miembro o elemento inexistente, o con identificadores ausentes o inválidos, se rechazan sin dejar ninguna relación persistida.
- **SC-004**: El 100 % de las solicitudes sin credenciales válidas se rechazan sin exponer datos de relaciones, miembros ni elementos.
- **SC-005**: Tras cualquier asignación, el 100 % de las estimaciones, estados y pertenencias a Sprint de los elementos permanecen idénticos a su valor previo.
- **SC-006**: Tras un fallo de persistencia no queda ninguna relación parcial en el 100 % de los casos probados.
- **SC-007**: Las consultas devuelven el conjunto exacto de relaciones existentes (sin omisiones ni extras) en el 100 % de los casos probados, y una colección vacía cuando no hay ninguna.

## Assumptions

- El actor es el Líder Técnico autenticado (inferido); que otros perfiles (Administrador de Plataforma, Desarrollador) asignen o consulten no está documentado, por lo que solo se exige un token válido con identidad.
- Las operaciones de asignación y las dos consultas son ⚠️ [PROPUESTO] para hacer verificable la relación; la forma de la solicitud (ruta o cuerpo) la decide el API Architect.
- El rol mostrado es el rol técnico registrado en HU-012; elegir otro rol por asignación queda como punto abierto.
- Los códigos HTTP 400/404/500 siguen el manejo centralizado de excepciones y 401 la exigencia de autorización de la Constitución del proyecto, igual que HU-001, HU-004 y HU-012.
- El formato de las consultas (campos adicionales, orden, filtros, paginación) no está definido; se entrega el contenido mínimo descrito.
- La relación solo cubre elementos del backlog; responsables de actividades, incidentes y reuniones (HU-021, HU-023, HU-027), capacidad (HU-013), carga por persona (HU-014) y demás relaciones de HU-010 quedan fuera de alcance.
- Dónde reside la relación y cómo cada consulta obtiene datos del otro módulo (llamada en proceso o proyección local) corresponde a Architecture.
- Dependencias: HU-012 (miembros y roles técnicos) y HU-001 (elementos del backlog) están activas.
