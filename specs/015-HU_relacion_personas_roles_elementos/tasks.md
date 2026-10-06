---

description: "Lista de tareas para HU-015: Relación entre Personas, Roles y Elementos de Trabajo"
---

# Tasks: Relación entre Personas, Roles y Elementos de Trabajo

**Input**: Documentos de diseño en `/specs/015-HU_relacion_personas_roles_elementos/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/item-assignments-api.openapi.yaml, quickstart.md

**Tests**: Se incluyen tareas de prueba porque el plan exige TDD (xUnit + FluentAssertions + Testcontainers PostgreSQL en backend; Jest en frontend), sin pruebas tautológicas y con doble escrito a mano para `IBacklogItemLookup` en unitarias. Las pruebas se escriben primero y deben fallar antes de implementar.

**Organization**: Tareas agrupadas por historia de usuario. US1 (asignar), US4 (rechazos 400/404) y US5 (401/500) comparten el endpoint `POST /api/backlog-items/{itemId}/assignees`; US2 es `GET /api/backlog-items/{itemId}/assignees`; US3 es `GET /api/team-members/{memberId}/items`. La consulta aditiva `GET /api/backlog-items` (selector del UX, ADR-006) se entrega dentro de US1.

## Format: `[ID] [P?] [Story] Descripción`

- **[P]**: Se puede ejecutar en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: Historia de usuario a la que pertenece (US1..US5)
- Todas las rutas son relativas a la raíz del repositorio

## Path Conventions

- Backend: `app/backend/src/Modules/Teams/` (abreviado `TEAMS/`) y `app/backend/src/Modules/Backlog/` (abreviado `BACKLOG/`); pruebas en `app/backend/tests/Unit/{Teams,Backlog}/` y `app/backend/tests/Integration/{Teams,Backlog}/`
- Frontend: `app/frontend/src/app/features/teams/` (abreviado `FE/`)
- Patrón de referencia: HU-012 (`Features/TeamMembers/*`, `TeamsInMemoryDb.cs`, `TeamsApiFactory.cs`, `PostgresFixture.cs`) y HU-004 (`IBacklogModuleApi` en `Sprints.Contracts` implementado por `BacklogModuleApi.cs`)
- Restricción: fuera de `Modules/Teams` y `features/teams` solo se permite tocar `BACKLOG/Backlog.csproj`, `BACKLOG/BacklogModule.cs`, `BACKLOG/BacklogItemLookup.cs`, `BACKLOG/Features/BacklogItems/ListBacklogItems/` y `app/frontend/src/app/app.routes.ts`. NO modificar `Modules/Application`, `Modules/Sprints`, `BuildingBlocks/Shared`, `core/auth`, `features/backlog`, `features/sprints`, ni `BacklogItem`, `BacklogDbContext`, configuraciones y migraciones de Backlog, ni `TeamMember`/`TechnicalRole` ni la migración `InitialTeamsSchema` (FR-013, FR-014)
- Sin RabbitMQ/MassTransit/Redis/Outbox, sin eventos de dominio, sin FKs ni consultas hacia el schema `backlog` ni referencia a `BacklogDbContext` desde `Teams`; `CancellationToken` propagado hasta EF Core y el contrato; el 500 no expone trazas; sin paquetes nuevos
- Nombres de campo y mensajes en español; nombres de clases/archivos exactamente como en plan.md
- **Reconciliación pendiente (BA)**: `spec.md` (Edge Case y FR-015) aún dice "no documentado" para la asignación duplicada; es vinculante la resolución humana B / ADR-004 del SA: duplicado idempotente (200). No implementar 409. Actualizar la spec es una tarea del BA, fuera de este código

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Carpetas y referencias de proyecto nuevas (el módulo `Teams` ya existe)

- [X] T001 Crear las carpetas `app/backend/src/Modules/Teams/Contracts/`, `Domain/ItemAssignments/`, `Features/ItemAssignments/{AssignMemberToItem,ListItemAssignees,ListMemberItems}/` y `app/backend/src/Modules/Backlog/Features/BacklogItems/ListBacklogItems/`
- [X] T002 Añadir `<ProjectReference Include="..\Teams\Teams.csproj" />` en `app/backend/src/Modules/Backlog/Backlog.csproj` (sentido contrato→implementador, igual que `Backlog` → `Sprints`); verificar con `dotnet build app/backend/TechWorkHub.sln` que no hay referencia circular (`Teams` NO referencia `Backlog`)
- [X] T003 [P] Añadir `ProjectReference` a `Teams.csproj` en `app/backend/tests/Unit/Backlog/Backlog.UnitTests.csproj` y `app/backend/tests/Integration/Backlog/Backlog.IntegrationTests.csproj` solo si el compilador lo exige tras T002. Depende de T002
- [X] T004 [P] Crear las carpetas del frontend `app/frontend/src/app/features/teams/components/{item-assignees-view,member-items-view,assign-assignee-dialog}/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Contrato in-process, dominio, persistencia, migración y su infraestructura de pruebas que TODAS las historias necesitan

**⚠️ CRITICAL**: Ninguna historia puede comenzar hasta completar esta fase

- [X] T005 [P] Crear `app/backend/src/Modules/Teams/Contracts/IBacklogItemLookup.cs`: interfaz pública `IBacklogItemLookup` con `Task<bool> ExistsAsync(Guid itemId, CancellationToken ct)` y `Task<IReadOnlyCollection<BacklogItemRef>> GetItemsAsync(IReadOnlyCollection<Guid> itemIds, CancellationToken ct)`, y `public sealed record BacklogItemRef(Guid Id, string Title, string Type)` (`Type` = nombre del enum como `string`). No devuelve estimaciones, estado, Sprint, descripción ni criterios de aceptación
- [X] T006 [P] Crear `app/backend/src/Modules/Teams/Domain/ItemAssignments/ItemAssignmentRules.cs`: constantes de campo `ItemIdField = "itemId"` y `MemberIdField = "memberId"`; mensajes en español (identificador de elemento/miembro requerido, formato inválido, `MemberNotFoundMessage = "El miembro indicado no existe."`, `ItemNotFoundMessage = "El elemento indicado no existe."`); `PairUniqueIndexName = "UX_ItemAssignments_ItemId_MemberId"`
- [X] T007 [P] Escribir pruebas (deben fallar) en `app/backend/tests/Unit/Teams/ItemAssignmentDomainTests.cs`: `ItemAssignment.Create(itemId, memberId)` genera `Id` distinto de `Guid.Empty`, conserva `ItemId` y `MemberId`, no registra eventos de dominio, y lanza `BadRequestException` con `Guid.Empty` en `itemId` o en `memberId`
- [X] T008 Crear `app/backend/src/Modules/Teams/Domain/ItemAssignments/ItemAssignment.cs`: `ItemAssignment : Aggregate<Guid>, IAuditableEntity` con `ItemId` (`Guid`, `uuid NOT NULL`, sin FK), `MemberId` (`Guid`, `uuid NOT NULL`), `CreatedAt` (`timestamptz NOT NULL`), `CreatedBy` (`varchar NOT NULL`), `LastModified` (`timestamptz` NULL), `LastModifiedBy` (`varchar` NULL); navegación local `Member` (`TeamMember`) solo lectura; factoría `ItemAssignment.Create(Guid itemId, Guid memberId)` que usa `ItemAssignmentRules`, rechaza `Guid.Empty` con `BadRequestException`; sin columna de rol, estado ni orden, sin eventos (ADR-007). Depende de T006 (T007 debe fallar antes)
- [X] T009 Modificar `app/backend/src/Modules/Teams/Data/ITeamsDbContext.cs` y `app/backend/src/Modules/Teams/Data/TeamsDbContext.cs` añadiendo `DbSet<ItemAssignment> ItemAssignments`; no tocar `TeamMembers` ni `TechnicalRoles`. Depende de T008
- [X] T010 Crear `app/backend/src/Modules/Teams/Data/Configurations/ItemAssignmentConfiguration.cs`: tabla `ItemAssignments` en schema `teams`, PK `Id` `uuid`; `ItemId` `uuid NOT NULL` SIN FK; `MemberId` `uuid NOT NULL` con FK real a `teams."TeamMembers"("Id")` `ON DELETE RESTRICT`; `CreatedAt` `timestamptz NOT NULL`; `CreatedBy` `varchar NOT NULL`; `LastModified` `timestamptz` NULL; `LastModifiedBy` `varchar` NULL; índice ÚNICO `UX_ItemAssignments_ItemId_MemberId` sobre `(ItemId, MemberId)` (usar `ItemAssignmentRules.PairUniqueIndexName`) e índice NO único `IX_ItemAssignments_MemberId` sobre `(MemberId)`. Depende de T009
- [X] T011 Generar la migración `AddItemAssignments` con `dotnet ef migrations add AddItemAssignments --project app/backend/src/Modules/Teams --startup-project app/backend/src/Bootstrapper/Api --context TeamsDbContext --output-dir Data/Migrations`; revisar que `Up` solo cree `teams."ItemAssignments"`, la FK y los dos índices, sin tocar `TeamMembers`, `TechnicalRoles` ni otros schemas, y que `Down` los elimine. Depende de T010
- [X] T012 [P] Escribir pruebas (deben fallar) en `app/backend/tests/Integration/Teams/ItemAssignmentsMigrationTests.cs` (Testcontainers PostgreSQL, siguiendo `TeamsMigrationTests.cs`): tras migrar existen la tabla, `UX_ItemAssignments_ItemId_MemberId` y `IX_ItemAssignments_MemberId`; un segundo `INSERT` SQL del mismo par `(ItemId, MemberId)` viola el índice único (SQLSTATE 23505); se admite el mismo elemento con otro miembro y el mismo miembro con otro elemento; la FK rechaza un `MemberId` inexistente; `backlog`, `sprints` y `application` no cambian. Depende de T011
- [X] T013 [P] Registrar en `app/backend/tests/Unit/Teams/TeamsInMemoryDb.cs` (solo si la clase lo requiere) lo necesario para `ItemAssignments` y crear el doble escrito a mano `app/backend/tests/Unit/Teams/FakeBacklogItemLookup.cs` (implementa `IBacklogItemLookup` con elementos configurables, contador de llamadas a `GetItemsAsync` y captura del `CancellationToken` recibido; sin librería de mocks). Depende de T005, T009
- [X] T014 [P] Crear `app/backend/tests/Integration/Teams/FakeBacklogItemLookup.cs` (doble para `TeamsApiFactory`: lista mutable de elementos conocidos) y modificar `app/backend/tests/Integration/Teams/TeamsApiFactory.cs` para sustituir `IBacklogItemLookup` por el doble en las pruebas de `Teams`, de modo que estas no dependan de `Backlog`. Depende de T005
- [X] T015 [P] Añadir los tipos del contrato en `app/frontend/src/app/features/teams/models/team.models.ts`: `ItemAssigneeResponse { itemId, memberId, memberName, role }`, `AssigneeResponse { id, name, role }`, `MemberItemResponse { id, title, type }` y `AssignMemberRequest { memberId }`

**Checkpoint**: Migración aplicable, contrato definido y dobles listos; las historias pueden comenzar

---

## Phase 3: User Story 1 - Asignar miembros como responsables de un elemento (Priority: P1) 🎯 MVP

**Goal**: `POST /api/backlog-items/{itemId}/assignees` con un miembro por solicitud: 201 + `Location` al crear y 200 con la relación existente si el par ya existía (idempotente); persiste con auditoría desde el `sub` y no altera el elemento ni el miembro.

**Independent Test**: Con "item-101" y los miembros "Ana Torres" (Desarrollo) y "Luis Rojas" (QA): asignar a cada uno devuelve 201 con `{ itemId, memberId, memberName, role }`, la fila lleva `CreatedAt`/`CreatedBy` = `sub`, la segunda asignación no altera la primera, repetir el par devuelve 200 sin nueva fila y el elemento queda intacto (FR-013).

### Tests for User Story 1 (escribir primero, deben fallar)

- [X] T016 [P] [US1] Escribir pruebas en `app/backend/tests/Unit/Teams/AssignMemberToItemCommandHandlerTests.cs` (EF InMemory + `FakeBacklogItemLookup`): éxito devuelve resultado "creado" con `itemId`, `memberId`, `memberName` y `role` del rol técnico vigente del miembro (JOIN local, no almacenado); `CreatedBy` queda con el `sub` del usuario actual y nunca con un valor del cuerpo; un segundo miembro sobre el mismo elemento conserva intacta la fila del primero; par ya existente devuelve resultado "existente" sin insertar y sin alterar `CreatedAt`/`CreatedBy`; un único `SaveChangesAsync` por asignación nueva; orden de evaluación miembro antes que elemento (el doble registra que `ExistsAsync` no se invoca si el miembro no existe); el `CancellationToken` llega al doble
- [X] T017 [P] [US1] Escribir pruebas en `app/backend/tests/Integration/Teams/AssignMemberToItemTests.cs` (Testcontainers, `TeamsApiFactory` + token válido): escenario 1 del quickstart → 201, cabecera `Location` = `/api/backlog-items/{itemId}/assignees`, cuerpo `{ itemId, memberId, memberName, role: "Desarrollo" }` sin `CreatedAt`/`CreatedBy`; fila persistida con `CreatedBy` = `sub` del token; escenario 2 (Luis, "QA") → 201 y la fila de Ana idéntica; escenario 3 (repetir Ana) → 200 mismo cuerpo, una sola fila, auditoría sin cambios
- [X] T018 [P] [US1] Escribir prueba de concurrencia en `app/backend/tests/Integration/Teams/AssignMemberToItemConcurrencyTests.cs`: N solicitudes simultáneas del mismo par → exactamente un 201, el resto 200, una sola fila (escenario 11); la carrera se resuelve por `UX_ItemAssignments_ItemId_MemberId` y la relectura de la fila ganadora
- [X] T019 [P] [US1] Escribir pruebas en `app/backend/tests/Unit/Backlog/BacklogItemLookupTests.cs` (EF InMemory de `BacklogDbContext`): `ExistsAsync` verdadero/falso; `GetItemsAsync` devuelve solo `Id`, `Title` y `Type` (string del enum) para los ids pedidos, omite los inexistentes, devuelve vacío con lista vacía y usa una única consulta
- [X] T020 [P] [US1] Escribir pruebas en `app/backend/tests/Unit/Backlog/ListBacklogItemsQueryHandlerTests.cs` y `app/backend/tests/Integration/Backlog/ListBacklogItemsTests.cs`: `GET /api/backlog-items` → 200 con `[{ id, title, type }]` sin estimaciones, estado ni Sprint (escenario 12), 401 sin token; no regresión: el `POST` de elementos de HU-001 conserva su comportamiento
- [X] T021 [P] [US1] Escribir pruebas Jest en `app/frontend/src/app/features/teams/services/team-api.service.spec.ts` (ampliar): `assignMember` hace `POST /api/backlog-items/{itemId}/assignees` con `{ memberId }` y expone el código HTTP (201 vs 200) en la respuesta observada; `listBacklogItems` hace `GET /api/backlog-items`
- [X] T022 [P] [US1] Escribir pruebas Jest en `app/frontend/src/app/features/teams/components/assign-assignee-dialog/assign-assignee-dialog.component.spec.ts`: selectores de miembro y elemento cargados desde el servicio; el rol se muestra de solo lectura derivado del miembro seleccionado; toast de éxito distinto para 201 ("asignado") y 200 ("ya era responsable"); tras 201/200 se vuelve a consultar al servidor (sin Optimistic UI); con 404/400/500 el diálogo permanece abierto conservando el campo no culpable

### Implementation for User Story 1

- [X] T023 [US1] Crear `app/backend/src/Modules/Backlog/BacklogItemLookup.cs`: `BacklogItemLookup : IBacklogItemLookup` (de `Teams.Contracts`) que consulta solo el schema `backlog` con `BacklogDbContext`, `AsNoTracking()`, solo lectura; `GetItemsAsync` en una única consulta con proyección a `BacklogItemRef(Id, Title, Type.ToString())`; `CancellationToken` propagado. Depende de T002, T005 (T019 debe fallar antes)
- [X] T024 [US1] Modificar `app/backend/src/Modules/Backlog/BacklogModule.cs` añadiendo `services.AddScoped<IBacklogItemLookup, BacklogItemLookup>()` sin alterar el resto del registro. Depende de T023
- [X] T025 [P] [US1] Crear `app/backend/src/Modules/Backlog/Features/BacklogItems/ListBacklogItems/BacklogItemSummaryResponse.cs`, `ListBacklogItemsQuery.cs`, `ListBacklogItemsQueryHandler.cs` y `ListBacklogItemsEndpoint.cs`: `GET /api/backlog-items` Carter con `.RequireAuthorization()`, MediatR, `AsNoTracking()` y proyección a `{ id, title, type }` (Type como string), sin paginación ni filtros, `CancellationToken` propagado, sin estimaciones, estado ni Sprint. Depende de T002 (T020 debe fallar antes)
- [X] T026 [P] [US1] Crear `app/backend/src/Modules/Teams/Features/ItemAssignments/ItemAssigneeResponse.cs`: `record ItemAssigneeResponse(Guid ItemId, Guid MemberId, string MemberName, string Role)` serializado en camelCase (`itemId`, `memberId`, `memberName`, `role`)
- [X] T027 [US1] Crear `app/backend/src/Modules/Teams/Features/ItemAssignments/AssignMemberToItem/AssignMemberToItemCommand.cs`: `AssignMemberToItemCommand(string ItemId, string? MemberId) : IRequest<AssignMemberToItemResult>`; `AssignMemberToItemResult` con `Response` (`ItemAssigneeResponse`) y `Created` (`bool`: `true` = 201, `false` = 200). `ItemId` y `MemberId` como `string` para reportar el formato inválido por campo (ADR-008)
- [X] T028 [US1] Crear `app/backend/src/Modules/Teams/Features/ItemAssignments/AssignMemberToItem/AssignMemberToItemCommandHandler.cs` con este orden determinista: identidad presente (si no, `UnauthorizedAccessException` → 401) → miembro existente en `teams` con JOIN local a `TechnicalRoles` (si no, `NotFoundException` con `ItemAssignmentRules.MemberNotFoundMessage`) → `IBacklogItemLookup.ExistsAsync` (si no, `NotFoundException` con `ItemNotFoundMessage`) → lectura del par `(ItemId, MemberId)` (si existe ⇒ resultado `Created = false`, sin escribir) → `ItemAssignment.Create` + `Add` + un único `SaveChangesAsync(ct)` ⇒ `Created = true`. `CreatedAt`/`CreatedBy` los rellena `AuditableEntityInterceptor` desde el `sub`. Capturar `DbUpdateException` cuyo `InnerException` sea `PostgresException` con `SqlState = "23505"` **y** `ConstraintName = ItemAssignmentRules.PairUniqueIndexName`: relee la fila ganadora y devuelve `Created = false`; cualquier otro fallo se relanza (500). El rol sale de `TechnicalRole.Name`, nunca de la solicitud. Depende de T008, T009, T026, T027 (T016 debe fallar antes)
- [X] T029 [US1] Crear `app/backend/src/Modules/Teams/Features/ItemAssignments/AssignMemberToItem/AssignMemberToItemEndpoint.cs`: `ICarterModule` con `POST /api/backlog-items/{itemId}/assignees`, `.RequireAuthorization()`, `itemId` como `string` de ruta y cuerpo `{ memberId: string? }`; `201 Created` con `Results.Created(location, response)` y `Location = /api/backlog-items/{itemId}/assignees` cuando `Created = true`, `200 OK` con el mismo cuerpo cuando es `false`; documentar 400/401/404/500 con `Produces`/`ProducesProblem`. Depende de T028 (T017 y T018 deben fallar antes)
- [X] T030 [US1] Registrar en `app/backend/src/Modules/Teams/TeamsModule.cs` lo que haga falta (los handlers y validadores se descubren por ensamblado; confirmar que el ensamblado `Teams` ya está en MediatR/FluentValidation/Carter y que `ItemAssignmentConfiguration` se aplica por `ApplyConfigurationsFromAssembly`). Depende de T029
- [X] T031 [P] [US1] Ampliar `app/frontend/src/app/features/teams/services/team-api.service.ts` con `assignMember(itemId, memberId)` (usar `observe: 'response'` para leer el código 201/200), `listBacklogItems()` y reutilizar `listMembers()` existente (`GET /api/team-members`). Depende de T015 (T021 debe fallar antes)
- [X] T032 [US1] Crear `app/frontend/src/app/features/teams/components/assign-assignee-dialog/assign-assignee-dialog.component.{ts,html,scss}`: componente standalone OnPush con Signals y PrimeNG (tema neutral); selector de elemento (`GET /api/backlog-items`), selector de miembro (`GET /api/team-members`), campo de rol de solo lectura derivado del miembro (sin elección por asignación, FR-005); textos con i18n; toast diferenciado por 201/200 y recarga desde el servidor; conserva el campo no culpable ante errores. Depende de T031 (T022 debe fallar antes)

**Checkpoint**: US1 funcional: asignar y reasignar idempotente, con auditoría e integridad del elemento

---

## Phase 4: User Story 4 - Rechazo de asignaciones con referencias inexistentes o inválidas (Priority: P1)

**Goal**: El `POST` responde 400 con detalle por campo ante identificadores ausentes o mal formados y 404 distinguiendo miembro de elemento, sin persistir nada.

**Independent Test**: Asignaciones con miembro inexistente, elemento inexistente, ambos inexistentes y 4 combinaciones de identificadores ausentes/mal formados más `Guid.Empty`: se verifica el rechazo exacto y que la tabla no recibió filas nuevas.

### Tests for User Story 4 (escribir primero, deben fallar)

- [X] T033 [P] [US4] Escribir pruebas en `app/backend/tests/Unit/Teams/AssignMemberToItemValidatorTests.cs`: `itemId` nulo/vacío/solo espacios/no GUID/`Guid.Empty` → error bajo `itemId`; `memberId` nulo/vacío/no GUID/`Guid.Empty` → error bajo `memberId`; GUID válidos sin errores; los errores usan los mensajes de `ItemAssignmentRules`
- [X] T034 [P] [US4] Escribir pruebas en `app/backend/tests/Integration/Teams/AssignMemberToItemValidationTests.cs`: elemento ausente/malformado y miembro ausente/malformado (más `Guid.Empty`) → 400 `application/problem+json` con `errors.itemId` o `errors.memberId`; miembro inexistente → 404 con `detail` "El miembro indicado no existe."; elemento inexistente → 404 con `detail` "El elemento indicado no existe."; ambos inexistentes → 404 de miembro (gana el miembro); en todos los casos la tabla `ItemAssignments` queda sin filas nuevas (escenarios 7 y 8)

### Implementation for User Story 4

- [X] T035 [US4] Crear `app/backend/src/Modules/Teams/Features/ItemAssignments/AssignMemberToItem/AssignMemberToItemValidator.cs`: `AbstractValidator<AssignMemberToItemCommand>`; `ItemId` y `MemberId` presentes, `Guid.TryParse` exitoso y distintos de `Guid.Empty`, con errores bajo las claves `itemId` y `memberId` (`ItemAssignmentRules.ItemIdField`/`MemberIdField`); sin consultas a BD. Depende de T006, T027 (T033 debe fallar antes)
- [X] T036 [US4] Verificar y, si hace falta, ajustar `AssignMemberToItemCommandHandler.cs` para que tras el validador use `Guid.Parse` sobre los identificadores ya validados y los 404 lleven los mensajes exactos de `ItemAssignmentRules` (el `CustomExceptionHandler` existente los traduce a `ProblemDetails`; no modificar `Shared`). Depende de T028, T035 (T034 debe fallar antes)
- [X] T037 [P] [US4] Ampliar `app/frontend/src/app/features/teams/components/assign-assignee-dialog/assign-assignee-dialog.component.{ts,html}` para mostrar el mensaje por campo ante 400 (`errors.itemId`/`errors.memberId`) y el mensaje de miembro/elemento inexistente ante 404, sin cerrar el diálogo; ampliar su `spec.ts` con esos casos. Depende de T032

**Checkpoint**: US4 funcional: integridad referencial verificada sin persistir relaciones huérfanas

---

## Phase 5: User Story 5 - Protección de acceso y robustez ante fallos (Priority: P1)

**Goal**: Las tres operaciones de la HU (y `GET /api/backlog-items`) exigen token válido (401) y un fallo de persistencia en el `POST` produce 500 sin trazas ni fila parcial.

**Independent Test**: Las operaciones sin token, con token inválido y con token expirado devuelven 401 sin leer ni escribir; un fallo de persistencia forzado devuelve 500 ProblemDetails sin traza y sin fila.

### Tests for User Story 5 (escribir primero, deben fallar)

- [X] T038 [P] [US5] Escribir pruebas en `app/backend/tests/Integration/Teams/ItemAssignmentsAuthTests.cs` (siguiendo `TeamsAuthTests.cs`): `POST` y los dos `GET` sin token, con token inválido y con token expirado → 401 sin lectura ni escritura (escenario 9); handler con identidad ausente → 401 (prueba unitaria adicional en `AssignMemberToItemCommandHandlerTests.cs`)
- [X] T039 [P] [US5] Escribir pruebas en `app/backend/tests/Integration/Teams/AssignMemberToItemFailureTests.cs` (siguiendo `RegisterTeamMemberFailureTests.cs`): forzar fallo de persistencia en el `POST` → 500 `application/problem+json` sin traza de pila ni mensajes internos y sin fila; una `PostgresException` 23505 de OTRO constraint no se confunde con la carrera y termina en 500 (escenario 10)
- [X] T040 [P] [US5] Escribir pruebas de no regresión en `app/backend/tests/Integration/Teams/ItemAssignmentsNoRegressionTests.cs`: tras las operaciones de la HU, `devPoints`, `qaPoints`, estado y Sprint de los elementos y los registros de `TeamMembers`/`TechnicalRoles` quedan idénticos y `backlog`, `sprints` y `application` no cambian (FR-013, FR-014, escenario 13); las suites de HU-001, HU-003, HU-004 y HU-012 siguen verdes sin modificaciones

### Implementation for User Story 5

- [X] T041 [US5] Confirmar que los tres endpoints (`AssignMemberToItemEndpoint`, `ListItemAssigneesEndpoint`, `ListMemberItemsEndpoint`) y `ListBacklogItemsEndpoint` declaran `.RequireAuthorization()` y que el handler de asignación lanza 401 sin identidad antes de leer miembros o elementos; ajustar lo que falte (sin tocar `Shared`). Depende de T029, T025, T047, T051 (T038 debe fallar antes; completar esta tarea al final de la fase 7 si los endpoints de lectura aún no existen)
- [X] T042 [US5] Confirmar en `AssignMemberToItemCommandHandler.cs` que cualquier fallo distinto de la carrera del índice único se relanza para que `CustomExceptionHandler` responda 500 sin trazas, que el `SaveChangesAsync` es único (sin estado parcial, SC-006) y que no se registra el nombre del miembro en logs. Depende de T028 (T039 debe fallar antes)

**Checkpoint**: US5 verificada: seguridad y robustez de todas las operaciones

---

## Phase 6: User Story 2 - Consultar las personas y roles relacionados con un elemento (Priority: P2)

**Goal**: `GET /api/backlog-items/{itemId}/assignees` devuelve exactamente las personas relacionadas (`id`, `name`, `role`) o `[]`; solo lectura.

**Independent Test**: Con un elemento con dos responsables y otro sin ninguno, cada consulta devuelve el contenido exacto (200, `[]` para el segundo) y no modifica datos.

### Tests for User Story 2 (escribir primero, deben fallar)

- [X] T043 [P] [US2] Escribir pruebas en `app/backend/tests/Unit/Teams/ListItemAssigneesQueryHandlerTests.cs`: devuelve exactamente Ana (Desarrollo) y Luis (QA); elemento sin responsables → colección vacía; elemento bien formado pero inexistente → colección vacía (D7); el rol sale del rol técnico vigente (JOIN local); no se invoca el contrato `IBacklogItemLookup`; `CancellationToken` propagado
- [X] T044 [P] [US2] Escribir pruebas en `app/backend/tests/Integration/Teams/ListItemAssigneesTests.cs`: escenario 4 → 200 con exactamente Ana y Luis; escenario 5 → 200 `[]`; los datos no cambian tras la consulta (FR-008); un `itemId` malformado no enruta (404, ruta `:guid`)
- [X] T045 [P] [US2] Escribir pruebas Jest en `app/frontend/src/app/features/teams/components/item-assignees-view/item-assignees-view.component.spec.ts` y ampliar `team-api.service.spec.ts` con `listItemAssignees`: estado con datos, estado vacío, estado de error y de carga; selector de elemento

### Implementation for User Story 2

- [X] T046 [P] [US2] Crear `app/backend/src/Modules/Teams/Features/ItemAssignments/AssigneeResponse.cs`: `record AssigneeResponse(Guid Id, string Name, string Role)` (camelCase `id`, `name`, `role`)
- [X] T047 [US2] Crear `app/backend/src/Modules/Teams/Features/ItemAssignments/ListItemAssignees/ListItemAssigneesQuery.cs`, `ListItemAssigneesQueryHandler.cs` y `ListItemAssigneesEndpoint.cs`: `GET /api/backlog-items/{itemId:guid}/assignees` Carter con `.RequireAuthorization()`; consulta `AsNoTracking()` con JOIN local `ItemAssignments`↔`TeamMembers`↔`TechnicalRoles` y proyección directa a `AssigneeResponse`; sin paginación; `CancellationToken` propagado; sin llamar a Backlog. Depende de T009, T046 (T043 y T044 deben fallar antes)
- [X] T048 [P] [US2] Ampliar `app/frontend/src/app/features/teams/services/team-api.service.ts` con `listItemAssignees(itemId)`. Depende de T015
- [X] T049 [US2] Crear `app/frontend/src/app/features/teams/components/item-assignees-view/item-assignees-view.component.{ts,html,scss}`: standalone OnPush con Signals y PrimeNG; selector de elemento, tabla de responsables (nombre y rol), estados de carga, vacío y error; botón que abre `assign-assignee-dialog`; i18n. Depende de T032, T048 (T045 debe fallar antes)
- [X] T050 [US2] Añadir la pestaña `Responsables` en `app/frontend/src/app/features/teams/components/team-page/team-page.component.{ts,html}` y la ruta hija `equipos/responsables` (con `data: { tab: 'responsables' }` y `loadComponent` de `ItemAssigneesViewComponent`) dentro del bloque `equipos` existente de `app/frontend/src/app/app.routes.ts` (hereda `authGuard`); ampliar `team-page.component.spec.ts`. Depende de T049

**Checkpoint**: US2 funcional en API y UI

---

## Phase 7: User Story 3 - Consultar los elementos relacionados con un miembro (Priority: P2)

**Goal**: `GET /api/team-members/{memberId}/items` devuelve exactamente los elementos relacionados (`id`, `title`, `type`) con una única llamada de lote al contrato; solo lectura.

**Independent Test**: Con Ana responsable de "item-101" e "item-102", la consulta devuelve exactamente esos dos elementos sin modificar datos.

### Tests for User Story 3 (escribir primero, deben fallar)

- [X] T051 [P] [US3] Escribir pruebas en `app/backend/tests/Unit/Teams/ListMemberItemsQueryHandlerTests.cs` (con `FakeBacklogItemLookup`): devuelve exactamente los dos elementos con `id`, `title` y `type`; una sola llamada a `GetItemsAsync` (sin N+1); miembro sin elementos → `[]` sin llamar al contrato; miembro inexistente → `[]` (D7); un elemento que el contrato ya no devuelve se omite y se registra `LogWarning` sin inventar título (D8); `CancellationToken` propagado al contrato
- [X] T052 [P] [US3] Escribir pruebas en `app/backend/tests/Integration/Teams/ListMemberItemsTests.cs`: escenario 6 → 200 con exactamente item-101 e item-102; miembro sin elementos → 200 `[]`; los datos no cambian tras la consulta (FR-008)
- [X] T053 [P] [US3] Escribir pruebas Jest en `app/frontend/src/app/features/teams/components/member-items-view/member-items-view.component.spec.ts` y ampliar `team-api.service.spec.ts` con `listMemberItems`: estado con datos, vacío, error y carga; selector de miembro

### Implementation for User Story 3

- [X] T054 [P] [US3] Crear `app/backend/src/Modules/Teams/Features/ItemAssignments/MemberItemResponse.cs`: `record MemberItemResponse(Guid Id, string Title, string Type)` (camelCase `id`, `title`, `type`)
- [X] T055 [US3] Crear `app/backend/src/Modules/Teams/Features/ItemAssignments/ListMemberItems/ListMemberItemsQuery.cs`, `ListMemberItemsQueryHandler.cs` y `ListMemberItemsEndpoint.cs`: `GET /api/team-members/{memberId:guid}/items` Carter con `.RequireAuthorization()`; lee los `ItemId` de `ItemAssignments` del miembro (`AsNoTracking()`, índice `IX_ItemAssignments_MemberId`), los envía en una sola llamada a `IBacklogItemLookup.GetItemsAsync(ids, ct)` y proyecta a `MemberItemResponse`; si el contrato no devuelve un id, se omite y se registra `LogWarning` (sin título inventado); sin paginación; sin consultas cross-schema. Depende de T005, T009, T054 (T051 y T052 deben fallar antes)
- [X] T056 [P] [US3] Ampliar `app/frontend/src/app/features/teams/services/team-api.service.ts` con `listMemberItems(memberId)`. Depende de T015
- [X] T057 [US3] Crear `app/frontend/src/app/features/teams/components/member-items-view/member-items-view.component.{ts,html,scss}`: standalone OnPush con Signals y PrimeNG; selector de miembro, tabla de elementos (título y tipo), estados de carga, vacío y error; i18n. Depende de T056 (T053 debe fallar antes)
- [X] T058 [US3] Añadir la ruta hija `equipos/responsables/miembro` (`loadComponent` de `MemberItemsViewComponent`) en `app/frontend/src/app/app.routes.ts` y el acceso desde la pestaña `Responsables` en `team-page.component.{ts,html}`; ampliar `team-page.component.spec.ts`. Depende de T050, T057

**Checkpoint**: Todas las historias son funcionales de forma independiente

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Verificación transversal y cierre

- [X] T059 [P] Revisar con `Grep` que `Teams` no referencia `BacklogDbContext`, el schema `backlog` ni `Backlog.csproj`, y que ningún archivo de código fuera de las rutas permitidas fue modificado (`git status`); verificar que `BacklogItem`, `TeamMember` y la migración `InitialTeamsSchema` no cambiaron (FR-013, FR-014)
- [X] T060 [P] Revisar que todos los `async` de E/S de producción de la HU propagan `CancellationToken` (endpoints, handlers, consultas y contrato) y que ningún log expone el nombre del miembro ni trazas
- [X] T061 Ejecutar `dotnet build app/backend/TechWorkHub.sln` y `dotnet test app/backend/TechWorkHub.sln` (integración con contenedores en serie); todas las suites de HU-001, HU-002, HU-003, HU-004 y HU-012 deben seguir verdes sin modificar sus pruebas
- [ ] T062 Ejecutar `npm test` y `npm run build` en `app/frontend`; corregir fallos de la HU
- [ ] T063 Ejecutar la validación manual de `specs/015-HU_relacion_personas_roles_elementos/quickstart.md` (escenarios 1–13 y pruebas de UI: pestaña `Responsables`, rutas `/equipos/responsables` y `/equipos/responsables/miembro`, toasts distintos para 201 y 200, rol de solo lectura)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sin dependencias
- **Foundational (Phase 2)**: depende de Setup; BLOQUEA todas las historias
- **US1 (Phase 3)**: depende de Foundational; es el MVP
- **US4 (Phase 4)** y **US5 (Phase 5)**: dependen de US1 (comparten el endpoint y el handler del `POST`); T041 se cierra tras las fases 6 y 7
- **US2 (Phase 6)** y **US3 (Phase 7)**: dependen de Foundational y de la entidad/migración; para probarlas con datos reales se apoyan en el `POST` de US1, pero su código es independiente y puede escribirse en paralelo
- **Polish (Phase 8)**: depende de todas las historias

### User Story Dependencies

- **US1 (P1)**: tras Foundational; sin dependencias de otras historias
- **US4 (P1)**: amplía el handler/endpoint de US1 (validador y mensajes 404)
- **US5 (P1)**: verifica seguridad de todos los endpoints; confirma el manejo de fallos de US1
- **US2 (P2)**: tras Foundational; lectura sobre `ItemAssignments`
- **US3 (P2)**: tras Foundational; lectura más el contrato `IBacklogItemLookup` (implementado en US1: T023/T024; en las pruebas de `Teams` se usa el doble)

### Within Each User Story

- Las pruebas se escriben primero y deben fallar
- Dominio → configuración/migración → handlers → endpoints → UI
- Historia completa antes de pasar a la siguiente prioridad

### Parallel Opportunities

- Setup: T003 y T004 en paralelo
- Foundational: T005, T006, T007, T012–T015 en paralelo donde no haya dependencia de archivo
- US1: T016–T022 en paralelo (archivos distintos); T025 y T026 en paralelo; T031 en paralelo con el backend
- US4: T033, T034 y T037 en paralelo
- US5: T038, T039 y T040 en paralelo
- US2 y US3 pueden desarrollarse en paralelo entre sí (archivos distintos) tras Foundational; `team-api.service.ts` y `app.routes.ts` son archivos compartidos: coordinar T031, T048, T056 y T050, T058

---

## Parallel Example: User Story 1

```bash
# Pruebas de US1 en paralelo:
Task: "Pruebas del handler en app/backend/tests/Unit/Teams/AssignMemberToItemCommandHandlerTests.cs"
Task: "Pruebas de integración en app/backend/tests/Integration/Teams/AssignMemberToItemTests.cs"
Task: "Pruebas de concurrencia en app/backend/tests/Integration/Teams/AssignMemberToItemConcurrencyTests.cs"
Task: "Pruebas de BacklogItemLookup en app/backend/tests/Unit/Backlog/BacklogItemLookupTests.cs"

# Piezas independientes de implementación:
Task: "ListBacklogItems en app/backend/src/Modules/Backlog/Features/BacklogItems/ListBacklogItems/"
Task: "ItemAssigneeResponse en app/backend/src/Modules/Teams/Features/ItemAssignments/ItemAssigneeResponse.cs"
```

---

## Implementation Strategy

### MVP First (US1 + US4 + US5)

1. Completar Phase 1 (Setup) y Phase 2 (Foundational)
2. Completar Phase 3 (US1): asignar con idempotencia y auditoría
3. Completar Phase 4 (US4) y Phase 5 (US5): rechazos y seguridad, que comparten el mismo endpoint y son P1
4. **DETENERSE y VALIDAR** con los escenarios 1–3 y 7–11 del quickstart

### Incremental Delivery

1. Setup + Foundational → base lista
2. US1 → probar → demo (MVP)
3. US4 + US5 → endurecer el `POST`
4. US2 → consulta tarjeta→personas
5. US3 → consulta persona→tarjetas
6. Polish → regresión completa y quickstart

---

## Notes

- [P] = archivos distintos, sin dependencias
- [Story] mapea cada tarea a su historia para trazabilidad
- Verificar que las pruebas fallen antes de implementar
- Hacer commit tras cada tarea o grupo lógico
- Evitar: tareas vagas, conflictos en el mismo archivo, dependencias entre historias que rompan su independencia
