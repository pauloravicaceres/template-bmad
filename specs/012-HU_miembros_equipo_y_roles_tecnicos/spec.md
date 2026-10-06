# Feature Specification: Miembros del Equipo y Roles Técnicos

**Feature Branch**: `feat/012-HU_miembros_equipo_y_roles_tecnicos`

**Created**: 2026-10-04

**Status**: 🔗 Consolidado en specs/README.md (Product State Ledger)

**Input**: User description: "documents/business-analyst/012-HU_miembros_equipo_y_roles_tecnicos.md"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Registrar un miembro del equipo con un rol técnico (Priority: P1)

Como Líder Técnico o Administrador de Plataforma autenticado, quiero registrar a un miembro del equipo técnico indicando su nombre y su rol técnico (Desarrollo, QA u otro del catálogo), para contar con los datos maestros de personas y roles que la planificación necesita.

**Why this priority**: Es la capacidad principal de la historia; las HU-013, HU-014, HU-015, HU-021, HU-023 y HU-027 dependen de ella y sin miembros registrados no es posible asignar responsables ni roles.

**Independent Test**: Con el catálogo de roles que contiene "Desarrollo" y "QA", se solicita registrar un miembro con cada rol y se verifica que se confirma con identificador, nombre y rol, que queda persistido con auditoría y que no cambia ningún elemento del backlog, Sprint ni asignación.

**Acceptance Scenarios**:

1. **Given** un usuario autenticado y el rol "Desarrollo" en el catálogo, **When** solicita registrar un miembro con nombre "Ana Torres" y rol "Desarrollo", **Then** el sistema confirma el registro con un código de éxito, la respuesta contiene el identificador único del miembro, su nombre y su rol, y el miembro se persiste con `CreatedAt` y `CreatedBy` igual al `sub` del token.
2. **Given** un usuario autenticado y el rol "QA" en el catálogo, **When** solicita registrar un miembro con nombre "Luis Rojas" y rol "QA", **Then** el sistema confirma el registro y la respuesta contiene el identificador único, el nombre "Luis Rojas" y el rol "QA".
3. **Given** un registro exitoso, **When** se revisan el backlog, los Sprints y las asignaciones, **Then** ninguno ha sido modificado.

---

### User Story 2 - Consultar los miembros registrados (Priority: P2)

Como Líder Técnico o Administrador de Plataforma autenticado, quiero consultar los miembros del equipo registrados, para verificar de forma observable quién forma parte del equipo y con qué rol.

**Why this priority**: Hace verificable el registro, pero depende de que este (P1) funcione. Es una capacidad ⚠️ [PROPUESTO] incluida solo para esa verificación.

**Independent Test**: Con miembros registrados y con ninguno, se solicita la consulta y se verifica el contenido devuelto y que no se modificó ningún dato.

**Acceptance Scenarios**:

1. **Given** un usuario autenticado y miembros registrados, **When** consulta los miembros del equipo, **Then** el sistema responde HTTP 200 OK con exactamente los miembros registrados, cada uno con identificador, nombre y rol, sin modificar datos.
2. **Given** un usuario autenticado y ningún miembro registrado, **When** consulta los miembros del equipo, **Then** responde HTTP 200 OK con una colección vacía.

---

### User Story 3 - Consultar el catálogo de roles técnicos (Priority: P2)

Como Líder Técnico o Administrador de Plataforma autenticado, quiero consultar los roles técnicos disponibles, para saber qué roles puedo asignar al registrar un miembro.

**Why this priority**: Permite conocer los valores válidos del rol y verificar que el catálogo contiene los roles respaldados por la fuente. Es ⚠️ [PROPUESTO].

**Independent Test**: Se solicita el catálogo y se verifica que contiene al menos "Desarrollo" y "QA", cada uno con identificador y nombre, y que no se modificó ningún dato.

**Acceptance Scenarios**:

1. **Given** un usuario autenticado, **When** consulta los roles técnicos disponibles, **Then** el sistema responde HTTP 200 OK con al menos los roles "Desarrollo" y "QA", cada uno con su identificador y nombre, sin modificar datos.

---

### User Story 4 - Rechazo de registros inválidos (Priority: P1)

Como Líder Técnico o Administrador de Plataforma, quiero que el sistema rechace registros con un rol inexistente o con nombre o rol ausentes o vacíos, para que no se persistan miembros inconsistentes.

**Why this priority**: Garantiza la integridad de los datos maestros de los que dependen otras historias.

**Independent Test**: Se envían solicitudes con rol inexistente ("Chef"), nombre ausente, nombre de solo espacios y rol ausente, verificando el código de respuesta y que no se persiste nada.

**Acceptance Scenarios**:

1. **Given** un usuario autenticado y un rol "Chef" que no existe en el catálogo, **When** solicita registrar un miembro con nombre "Ana Torres" y rol "Chef", **Then** responde HTTP 400 Bad Request indicando que el rol no es válido y no se persiste ningún miembro.
2. **Given** un usuario autenticado, **When** solicita registrar un miembro con nombre ausente, nombre compuesto solo de espacios o rol ausente, **Then** responde HTTP 400 Bad Request con el detalle de los campos inválidos y no se persiste ningún miembro.

---

### User Story 5 - Protección de acceso y resiliencia ante fallos (Priority: P1)

Como Líder Técnico o Administrador de Plataforma, quiero que solo usuarios con credenciales válidas puedan registrar o consultar, y que un fallo interno no deje miembros a medias, para confiar en la integridad de los datos maestros.

**Why this priority**: Es una restricción transversal de seguridad e integridad exigida por la Constitución del proyecto.

**Independent Test**: Se ejecutan las tres operaciones (registrar miembro, consultar miembros, consultar roles) sin token y con token inválido o expirado, y se simula un fallo de persistencia al registrar, verificando 401 y 500 respectivamente y ausencia de datos parciales.

**Acceptance Scenarios**:

1. **Given** una solicitud sin token o con token inválido o expirado, **When** intenta registrar un miembro, consultar los miembros o consultar los roles técnicos, **Then** responde HTTP 401 Unauthorized y no se lee ni persiste ningún dato de miembros ni de roles.
2. **Given** un usuario autenticado, el rol "Desarrollo" en el catálogo y una persistencia que falla al guardar, **When** solicita registrar un miembro con nombre "Ana Torres" y rol "Desarrollo", **Then** responde HTTP 500 Internal Server Error sin exponer trazas internas y no queda registrado ningún miembro parcial.

---

### Edge Cases

- ¿Qué pasa si el rol indicado no existe en el catálogo? HTTP 400 sin persistir (FR-006).
- ¿Qué pasa si el nombre o el rol están ausentes, vacíos o compuestos solo de espacios? HTTP 400 con la lista de campos inválidos (FR-007).
- ¿Qué pasa si no hay credenciales válidas en cualquiera de las tres operaciones? HTTP 401 (FR-011).
- ¿Qué pasa si falla la persistencia al registrar? HTTP 500 sin trazas internas y sin miembro parcial (FR-013).
- ¿Qué pasa si no hay miembros registrados al consultar? HTTP 200 con colección vacía (FR-009).
- Sin comportamiento definido, por estar ❓ No documentado en la HU y fuera de alcance: nombre duplicado, longitud máxima y caracteres admitidos del nombre, varios roles por miembro, modificación, desactivación o eliminación de miembros, alta o edición de roles del catálogo, vínculo con el servidor de identidad y permisos por rol de acceso. No se inventan escenarios para ellos (ver Assumptions).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema DEBE permitir a un usuario autenticado registrar un miembro del equipo técnico con un nombre y un rol técnico del catálogo, con un miembro y un rol por solicitud.
- **FR-002**: El sistema DEBE confirmar el registro con un código de éxito y devolver el identificador único del miembro, su nombre y su rol.
- **FR-003**: El sistema DEBE persistir cada miembro con los metadatos de auditoría `CreatedAt` y `CreatedBy`, este último tomado del `sub` del token.
- **FR-004**: El sistema DEBE mantener un catálogo de roles técnicos que contenga al menos los roles "Desarrollo" y "QA", cada uno con identificador y nombre.
- **FR-005**: El sistema DEBE permitir a un usuario autenticado consultar los roles técnicos disponibles (HTTP 200), devolviendo al menos "Desarrollo" y "QA" con su identificador y nombre, sin modificar datos.
- **FR-006**: El sistema DEBE rechazar con HTTP 400, indicando que el rol no es válido, todo registro cuyo rol no exista en el catálogo, sin persistir ningún miembro.
- **FR-007**: El sistema DEBE rechazar con HTTP 400, con el detalle de los campos inválidos, todo registro con nombre o rol ausente, vacío o compuesto solo de espacios, sin persistir ningún miembro.
- **FR-008**: El sistema DEBE permitir a un usuario autenticado consultar los miembros registrados (HTTP 200), devolviendo exactamente los miembros registrados, cada uno con identificador, nombre y rol, sin modificar datos.
- **FR-009**: El sistema DEBE responder HTTP 200 OK con una colección vacía cuando no exista ningún miembro registrado.
- **FR-010**: El miembro DEBE identificarse por un nombre; el sistema NO DEBE exigir otros datos de la persona (correo, usuario de acceso, etc.).
- **FR-011**: El sistema DEBE rechazar con HTTP 401 toda operación de esta funcionalidad (registrar miembro, consultar miembros, consultar roles) sin token, o con token inválido o expirado, sin leer ni persistir datos de miembros ni de roles.
- **FR-012**: Toda operación rechazada (400, 401, 500) NO DEBE persistir ningún miembro.
- **FR-013**: Ante un fallo de persistencia al registrar, el sistema DEBE responder HTTP 500 sin exponer trazas internas y sin dejar ningún miembro parcial.
- **FR-014**: El registro NO DEBE modificar elementos del backlog, Sprints ni asignaciones, ni alterar el comportamiento de las HU-001, HU-003 y HU-004; las estimaciones por rol Dev y QA del backlog permanecen independientes de este catálogo.
- **FR-015**: El diseño NO DEBE asumir ni imponer la cardinalidad miembro–rol, la unicidad del miembro ni su ciclo de vida (puntos abiertos 1, 2 y 3 de la HU).
- **FR-016**: La funcionalidad DEBE respetar las restricciones de `.specify/memory/constitution.md` (aislamiento por schema por módulo, sin consultas cross-schema, endpoints protegidos con `.RequireAuthorization()`, manejo centralizado de excepciones).

### Key Entities *(include if feature involves data)*

- **Miembro del equipo**: Persona del equipo técnico. Atributos: identificador único, nombre, rol técnico, `CreatedAt`, `CreatedBy`. No define estado ni ciclo de vida.
- **Rol técnico**: Entrada del catálogo de roles (al menos "Desarrollo" y "QA"). Atributos: identificador y nombre. Cada miembro registrado referencia un rol del catálogo.
- **Elemento del backlog, Sprint y Asignación** (preexistentes, HU-001, HU-003 y HU-004): no se modifican.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un Líder Técnico puede registrar un miembro con su rol y verlo en la consulta de miembros en menos de 1 minuto.
- **SC-002**: El 100 % de los registros con rol inexistente, o con nombre o rol ausentes, vacíos o de solo espacios, es rechazado sin persistir ningún miembro.
- **SC-003**: El 100 % de las solicitudes sin credenciales válidas, en las tres operaciones, es rechazado sin exponer ni modificar datos de miembros ni de roles.
- **SC-004**: La consulta de miembros devuelve exactamente los miembros registrados (ni más ni menos) en el 100 % de los casos verificados.
- **SC-005**: La consulta del catálogo contiene los roles "Desarrollo" y "QA" en el 100 % de los casos verificados.
- **SC-006**: El registro no altera ningún dato del backlog, Sprints ni asignaciones en el 100 % de los casos verificados.
- **SC-007**: Las consultas de miembros y de roles devuelven resultados en menos de 2 segundos para hasta 100 miembros registrados.
- **SC-008**: Ante un fallo de persistencia, el 100 % de los casos termina sin miembros parciales.

## Assumptions

- Los actores previstos son el Líder Técnico y el Administrador de Plataforma; los permisos exactos por rol de acceso no están documentados, por lo que basta un token válido con identidad (patrón de HU-001, HU-003 y HU-004) (punto abierto 6 de la HU).
- Cada solicitud registra un único miembro con un único rol; varios roles por miembro y registro en lote no se especifican (puntos abiertos 1 y 2).
- La unicidad del miembro (homónimos), la longitud máxima y los caracteres admitidos del nombre no están definidos; no se restringen (punto abierto 2).
- Modificar, desactivar o eliminar un miembro y cambiar su rol quedan fuera de alcance (punto abierto 3).
- El catálogo garantiza solo "Desarrollo" y "QA", únicos roles respaldados por la fuente; el alta o edición de roles y el conjunto completo ("etc.") quedan fuera de alcance (punto abierto 4).
- No se vincula al miembro con un usuario del servidor de identidad ni se mapean roles técnicos con roles de acceso (punto abierto 5).
- El formato de las consultas (campos adicionales, orden, filtros por rol, paginación) no está definido; se devuelve todo lo registrado con los campos indicados (punto abierto 7).
- El catálogo de roles no se vincula con las estimaciones Dev y QA del backlog en esta HU (punto abierto 8).
- Las consultas de miembros y del catálogo de roles son ⚠️ [PROPUESTO] y se incluyen solo para hacer verificable el registro.
- Dependencias: ninguna HU previa; autenticación con token emitido por el servidor de identidad existente. Cómo P1 consumirá estos datos respetando el aislamiento por schema corresponde a Architecture.
