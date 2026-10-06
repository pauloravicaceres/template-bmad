---

description: "Lista de tareas para HU-012: Miembros del Equipo y Roles Técnicos"
---

# Tasks: Miembros del Equipo y Roles Técnicos

**Input**: Documentos de diseño en `/specs/012-HU_miembros_equipo_y_roles_tecnicos/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/teams-api.openapi.yaml, quickstart.md

**Tests**: Se incluyen tareas de prueba porque el plan exige TDD (xUnit + FluentAssertions + Testcontainers PostgreSQL en backend; Jest en frontend), sin pruebas tautológicas y con BD en memoria solo en unitarias. Las pruebas se escriben primero y deben fallar antes de implementar.

**Organization**: Tareas agrupadas por historia de usuario. US1 (registrar), US4 (rechazos 400) y US5 (401/500) comparten el endpoint `POST /api/team-members`; US2 es `GET /api/team-members`; US3 es `GET /api/technical-roles`.

## Format: `[ID] [P?] [Story] Descripción`

- **[P]**: Se puede ejecutar en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: Historia de usuario a la que pertenece (US1..US5)
- Todas las rutas son relativas a la raíz del repositorio

## Path Conventions

- Backend: `app/backend/src/Modules/Teams/` (raíz abreviada `TEAMS/` en las descripciones), pruebas en `app/backend/tests/Unit/Teams/` y `app/backend/tests/Integration/Teams/`
- Frontend: `app/frontend/src/app/features/teams/`
- Patrón de referencia: módulo `Sprints` (`SprintsModule.cs`, `Sprints.csproj`, `Features/Sprints/CreateSprint`, `ListSprints`, `Data/SprintsDbContext*.cs`, `tests/Unit/Sprints`, `tests/Integration/Sprints/PostgresFixture.cs` y `SprintsApiFactory.cs`) y `features/sprints` en frontend
- Restricción: fuera de `Modules/Teams` y `features/teams` solo se permite tocar `app/backend/TechWorkHub.sln`, `app/backend/src/Bootstrapper/Api/Api.csproj`, `app/backend/src/Bootstrapper/Api/Program.cs` y `app/frontend/src/app/app.routes.ts`. NO modificar `Modules/Backlog`, `Modules/Application`, `Modules/Sprints`, `BuildingBlocks/Shared`, `core/auth`, `features/backlog` ni `features/sprints` (FR-014)
- Sin RabbitMQ/MassTransit/Redis/Outbox, sin eventos de dominio, sin FKs ni consultas hacia otros schemas; `CancellationToken` propagado hasta EF Core; el nombre del miembro no se escribe en logs; sin paquetes nuevos
- Nombres de campo y mensajes en español; nombres de clases/archivos exactamente como en plan.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Proyectos y carpetas nuevos del módulo `Teams`

- [X] T001 Crear `app/backend/src/Modules/Teams/Teams.csproj` con las mismas referencias y paquetes que `app/backend/src/Modules/Sprints/Sprints.csproj` (sin paquetes nuevos) y las carpetas `Domain/TeamMembers/`, `Domain/TechnicalRoles/`, `Data/Configurations/`, `Features/TeamMembers/{RegisterTeamMember,ListTeamMembers}/`, `Features/TechnicalRoles/ListTechnicalRoles/`
- [X] T002 [P] Crear `app/backend/tests/Unit/Teams/Teams.UnitTests.csproj` copiando `Sprints.UnitTests.csproj` (xUnit, NSubstitute, FluentAssertions, EF InMemory) con `RootNamespace` `Unit.Teams` y `ProjectReference` a `Teams.csproj` y `Shared.csproj`
- [X] T003 [P] Crear `app/backend/tests/Integration/Teams/Teams.IntegrationTests.csproj` copiando `Sprints.IntegrationTests.csproj` (Testcontainers PostgreSQL, `WebApplicationFactory`) con `ProjectReference` a `Teams.csproj`, `Api.csproj` y `Shared.csproj`
- [X] T004 Añadir `Teams`, `Teams.UnitTests` y `Teams.IntegrationTests` a `app/backend/TechWorkHub.sln` con `dotnet sln app/backend/TechWorkHub.sln add ...`. Depende de T001, T002, T003
- [X] T005 [P] Añadir `<ProjectReference Include="..\..\Modules\Teams\Teams.csproj" />` en `app/backend/src/Bootstrapper/Api/Api.csproj`. Depende de T001
- [X] T006 [P] Crear las carpetas del frontend `app/frontend/src/app/features/teams/{components/team-page,components/register-member-dialog,services,models}/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Dominio, persistencia, migración con semilla, registro del módulo, infraestructura de pruebas y contrato frontend que TODAS las historias necesitan

**⚠️ CRITICAL**: Ninguna historia puede comenzar hasta completar esta fase

- [X] T007 [P] Crear `app/backend/src/Modules/Teams/Domain/TechnicalRoles/TechnicalRoleSeed.cs`: constantes `DevelopmentId` y `QaId` (GUID fijos y distintos, escritos como literales, nunca `Guid.NewGuid()`) y `DevelopmentName = "Desarrollo"`, `QaName = "QA"`
- [X] T008 [P] Crear `app/backend/src/Modules/Teams/Domain/TeamMembers/TeamMemberRules.cs`: constantes de campo `NameField = "name"` y `RoleField = "role"`; mensajes en español: nombre requerido, rol requerido y `InvalidRoleMessage = "El rol indicado no es válido."`
- [X] T009 [P] Escribir pruebas (deben fallar) en `app/backend/tests/Unit/Teams/TeamMemberDomainTests.cs`: `TeamMember.Create` genera `Id` distinto de `Guid.Empty`, conserva `TechnicalRoleId`, guarda `Name` recortado (`"  Ana Torres  "` → `"Ana Torres"`), y lanza `BadRequestException` con nombre `null`, vacío o de solo espacios y con `Guid.Empty` como rol
- [X] T010 Crear `app/backend/src/Modules/Teams/Domain/TechnicalRoles/TechnicalRole.cs`: `TechnicalRole : Aggregate<Guid>` (sin `IAuditableEntity`, sin eventos) con `Name` (`string`, `NOT NULL`); sin factoría pública de alta (constructor privado/protegido para EF). Depende de T007
- [X] T011 Crear `app/backend/src/Modules/Teams/Domain/TeamMembers/TeamMember.cs`: `TeamMember : Aggregate<Guid>, IAuditableEntity` con `Name` (`string`, `text NOT NULL`, sin límite de longitud ni unicidad), `TechnicalRoleId` (`Guid`, `uuid NOT NULL`), `CreatedAt`, `CreatedBy`, `LastModified`, `LastModifiedBy`; navegación local `TechnicalRole`; factoría `TeamMember.Create(string name, Guid technicalRoleId)` que usa `TeamMemberRules`, rechaza nombre vacío/solo espacios y `Guid.Empty` con `BadRequestException` y guarda `name.Trim()`; sin estado ni eventos de dominio (ADR-006). Depende de T008, T010 (T009 debe fallar antes)
- [X] T012 Crear `app/backend/src/Modules/Teams/Data/ITeamsDbContext.cs` y `app/backend/src/Modules/Teams/Data/TeamsDbContext.cs` con `DbSet<TeamMember> TeamMembers`, `DbSet<TechnicalRole> TechnicalRoles`, `SchemaName = "teams"` y `HasDefaultSchema`, siguiendo `SprintsDbContext.cs`. Depende de T010, T011
- [X] T013 [P] Crear `app/backend/src/Modules/Teams/Data/Configurations/TechnicalRoleConfiguration.cs`: tabla `TechnicalRoles`, PK `Id` `uuid`, `Name` `text NOT NULL`, índice ÚNICO `UX_TechnicalRoles_Name` sobre `Name`, y `HasData` con los dos roles de `TechnicalRoleSeed` (`Desarrollo` y `QA`). Depende de T012
- [X] T014 [P] Crear `app/backend/src/Modules/Teams/Data/Configurations/TeamMemberConfiguration.cs`: tabla `TeamMembers`, PK `Id` `uuid`, `Name` `text NOT NULL` (sin índice único ni límite), `TechnicalRoleId` `uuid NOT NULL` con FK real a `teams."TechnicalRoles"("Id")` `ON DELETE RESTRICT`, `CreatedAt` `timestamptz NOT NULL`, `CreatedBy` `text NOT NULL`, `LastModified` `timestamptz` NULL, `LastModifiedBy` `text` NULL, e índice NO único `IX_TeamMembers_TechnicalRoleId`. Depende de T012
- [X] T015 [P] Crear `app/backend/src/Modules/Teams/Data/TeamsDbContextFactory.cs` (fábrica de diseño para `dotnet ef`) siguiendo `SprintsDbContextFactory.cs`. Depende de T012
- [X] T016 Crear `app/backend/src/Modules/Teams/TeamsModule.cs` con `AddTeamsModule` (MediatR con `ValidationBehavior<,>`, `AddValidatorsFromAssembly`, `AddDbContext<TeamsDbContext>` con `MigrationsHistoryTable` en el schema `teams` y `AuditableEntityInterceptor`, `ITeamsDbContext` → `TeamsDbContext`) y `MigrateTeamsModuleAsync`, idénticos en estructura a `SprintsModule.cs`. Depende de T012
- [X] T017 Generar la migración `InitialTeamsSchema` en `app/backend/src/Modules/Teams/Data/Migrations/` (`dotnet ef migrations add InitialTeamsSchema`), verificando que solo crea objetos en el schema `teams` (`TechnicalRoles`, `TeamMembers`, `__EFMigrationsHistory`, índices, FK con `RESTRICT` y `InsertData` de los dos roles) y no toca `backlog`, `application` ni `sprints`. Depende de T013, T014, T015, T016
- [X] T018 Registrar el módulo en `app/backend/src/Bootstrapper/Api/Program.cs`: `using Teams;`, `builder.Services.AddTeamsModule(builder.Configuration);` y `await app.Services.MigrateTeamsModuleAsync();` junto a las llamadas de Sprints existentes, sin alterar las demás. Depende de T016, T005
- [X] T019 [P] Crear los helpers `app/backend/tests/Unit/Teams/TeamsInMemoryDb.cs` (`TeamsDbContext` en memoria con los dos roles sembrados) siguiendo `SprintsInMemoryDb.cs`. Depende de T012
- [X] T020 [P] Crear `app/backend/tests/Integration/Teams/PostgresFixture.cs` y `app/backend/tests/Integration/Teams/TeamsApiFactory.cs` siguiendo `PostgresFixture.cs` y `SprintsApiFactory.cs` (Testcontainers, token JWT de prueba válido/inválido/expirado, `MigrateOnStartup`). Depende de T018
- [X] T021 Escribir `app/backend/tests/Integration/Teams/TeamsMigrationTests.cs`: sobre base vacía la migración crea solo objetos del schema `teams`; la semilla contiene exactamente dos roles ("Desarrollo" y "QA") con los GUID de `TechnicalRoleSeed`; un `INSERT` SQL con nombre de rol repetido viola `UX_TechnicalRoles_Name` (SQLSTATE 23505); un `TechnicalRoleId` inexistente viola la FK (23503); los schemas `backlog`, `sprints` y `application` no cambian. Depende de T017, T020
- [X] T022 [P] Crear `app/backend/src/Modules/Teams/Features/TeamMembers/TeamMemberResponse.cs` (`record TeamMemberResponse(Guid Id, string Name, string Role)`) y `app/backend/src/Modules/Teams/Features/TechnicalRoles/TechnicalRoleResponse.cs` (`record TechnicalRoleResponse(Guid Id, string Name)`); sin `CreatedAt`/`CreatedBy` ni estado (UX D-09). Depende de T001
- [X] T023 [P] Crear `app/frontend/src/app/features/teams/models/team.models.ts` con `TeamMember { id, name, role }`, `TechnicalRole { id, name }` y `RegisterTeamMemberRequest { name, role }` (tipos del contrato `teams-api.openapi.yaml`)
- [X] T024 Escribir `app/frontend/src/app/features/teams/services/team-api.service.spec.ts` (Jest + `HttpTestingController`; debe fallar): `listMembers` hace `GET /api/team-members`, `listRoles` hace `GET /api/technical-roles`, `registerMember` hace `POST /api/team-members` con `{ name, role }` y devuelve `TeamMember`; patrón de `sprint-api.service.spec.ts`. Depende de T023
- [X] T025 Crear `app/frontend/src/app/features/teams/services/team-api.service.ts` con `listMembers()`, `listRoles()` y `registerMember(request)` sobre `HttpClient`, siguiendo `sprint-api.service.ts` (sin añadir cabecera de token: ya lo hace el interceptor de `core/auth`). Depende de T024

**Checkpoint**: Migración aplicable, módulo registrado, fixtures de prueba y servicio frontend listos

---

## Phase 3: User Story 1 - Registrar un miembro del equipo con un rol técnico (Priority: P1) 🎯 MVP

**Goal**: `POST /api/team-members` registra un miembro con nombre y rol del catálogo, responde 201 con `{ id, name, role }`, persiste `CreatedAt`/`CreatedBy` (`sub` del token) y no altera backlog, Sprints ni asignaciones.

**Independent Test**: Con el catálogo sembrado, registrar "Ana Torres" / "Desarrollo" y "Luis Rojas" / "QA" → 201 con identificador, nombre y rol; la fila queda con `CreatedBy` = `sub` y los schemas `backlog` y `sprints` sin cambios.

### Tests for User Story 1 ⚠️ (escribir primero; deben fallar)

- [X] T026 [P] [US1] Escribir `app/backend/tests/Unit/Teams/RegisterTeamMemberCommandHandlerTests.cs`: con `TeamsInMemoryDb` y un `ICurrentUser` simulado, el handler resuelve el rol por nombre, agrega un `TeamMember` con `Name` recortado y `TechnicalRoleId` del rol, invoca `SaveChangesAsync` exactamente una vez y devuelve `TeamMemberResponse(id, name, role)` con el nombre del rol (casos "Desarrollo" y "QA")
- [X] T027 [P] [US1] Escribir `app/backend/tests/Integration/Teams/RegisterTeamMemberTests.cs`: `POST /api/team-members` con `{ "name": "Ana Torres", "role": "Desarrollo" }` y con `{ "name": "Luis Rojas", "role": "QA" }` → 201, cuerpo `{ id, name, role }` (sin `createdAt`/`createdBy`), cabecera `Location` = `/api/team-members`; la fila en `teams."TeamMembers"` tiene `CreatedBy` igual al `sub` del token (nunca el del cuerpo) y `CreatedAt` informado
- [X] T028 [P] [US1] Escribir `app/backend/tests/Integration/Teams/RegisterTeamMemberNoRegressionTests.cs` (FR-014, SC-006): contar filas de `backlog`, `sprints."Sprints"` y `sprints."SprintItems"` antes y después de registrar un miembro; deben ser idénticas
- [X] T029 [P] [US1] Escribir `app/frontend/src/app/features/teams/components/register-member-dialog/register-member-dialog.component.spec.ts` (Jest, servicio simulado; debe fallar): el selector se alimenta de `listRoles()`; al enviar con éxito llama `registerMember({ name, role })`, emite el evento de éxito con el miembro devuelto y cierra el diálogo; el botón "Registrar" queda deshabilitado mientras `isSubmitting()` es verdadero; sin validación de negocio duplicada en el cliente (UX D-05)

### Implementation for User Story 1

- [X] T030 [P] [US1] Crear `app/backend/src/Modules/Teams/Features/TeamMembers/RegisterTeamMember/RegisterTeamMemberCommand.cs`: `RegisterTeamMemberCommand(string? Name, string? Role) : ICommand<TeamMemberResponse>` (el cuerpo del `POST` es `{ name, role }`; el rol es el NOMBRE del rol)
- [X] T031 [US1] Crear `app/backend/src/Modules/Teams/Features/TeamMembers/RegisterTeamMember/RegisterTeamMemberCommandHandler.cs`: en este orden, (1) obtener `ICurrentUser.UserId` y, si no hay claim, lanzar `UnauthorizedAccessException` (401); (2) `TechnicalRoles.FirstOrDefaultAsync(r => r.Name == command.Role, cancellationToken)` (comparación sensible a mayúsculas) y, si no existe, lanzar `BadRequestException(TeamMemberRules.InvalidRoleMessage)`; (3) `TeamMember.Create(name, role.Id)` + `Add` + un único `SaveChangesAsync(cancellationToken)`; devolver `TeamMemberResponse` con el nombre del rol. No escribir el nombre en logs, sin reintentos, sin eventos. Depende de T011, T022, T030
- [X] T032 [US1] Crear `app/backend/src/Modules/Teams/Features/TeamMembers/RegisterTeamMember/RegisterTeamMemberEndpoint.cs`: `ICarterModule` con `MapPost("/api/team-members", ...)`, `.RequireAuthorization()`, `Produces<TeamMemberResponse>(201)`, `ProducesProblem` 400/401/500, `request.Adapt<RegisterTeamMemberCommand>()` con Mapster y `Results.Created("/api/team-members", response)`, propagando `CancellationToken`. Depende de T031
- [X] T033 [US1] Crear `app/frontend/src/app/features/teams/components/register-member-dialog/register-member-dialog.component.{ts,html,scss}`: componente standalone `OnPush` con `p-dialog`, campo "Nombre" (`pInputText`) y "Rol técnico" (`p-select` cargado con `listRoles()`), botones "Cancelar"/"Registrar", estado en Signals (`isSubmitting`, `roles`), textos con i18n, tema neutral de PrimeNG (estados 4 a 6 del UX). Inputs/outputs: visibilidad del diálogo y evento `registered` con el `TeamMember`. Depende de T025, T029

**Checkpoint**: US1 funcional: se puede registrar un miembro vía API y existe el diálogo (se monta en la página en US2)

---

## Phase 4: User Story 4 - Rechazo de registros inválidos (Priority: P1)

**Goal**: Rechazar con 400 los registros con rol inexistente o con nombre/rol ausentes, vacíos o de solo espacios, sin persistir nada.

**Independent Test**: Enviar "Chef", nombre ausente, nombre de solo espacios y rol ausente → 400 con el detalle correcto; `teams."TeamMembers"` sin filas nuevas.

### Tests for User Story 4 ⚠️

- [X] T034 [P] [US4] Escribir `app/backend/tests/Unit/Teams/RegisterTeamMemberValidatorTests.cs` (debe fallar): errores bajo `name` y `role` para `null`, `""` y `"   "` en cada campo; comando válido sin errores
- [X] T035 [P] [US4] Añadir a `app/backend/tests/Unit/Teams/RegisterTeamMemberCommandHandlerTests.cs` el caso rol inexistente ("Chef"): lanza `BadRequestException` con `TeamMemberRules.InvalidRoleMessage` y no persiste ningún miembro; y el caso sin claim de identidad → `UnauthorizedAccessException` sin persistir
- [X] T036 [P] [US4] Escribir `app/backend/tests/Integration/Teams/RegisterTeamMemberValidationTests.cs`: rol "Chef" → 400 `application/problem+json` con detail "El rol indicado no es válido."; cuatro casos (nombre ausente, nombre de solo espacios, rol ausente, rol de solo espacios) → 400 con `errors.name` o `errors.role`; en todos, `teams."TeamMembers"` sin filas nuevas; con nombre inválido y rol inexistente a la vez gana el 400 del validador
- [X] T037 [P] [US4] Añadir en `register-member-dialog.component.spec.ts` (frontend) los casos de error 400: el diálogo permanece abierto, conserva los valores y muestra el mensaje del servidor bajo el campo `name` o `role` o el detalle "El rol indicado no es válido." (estados 7 y 8 del UX)

### Implementation for User Story 4

- [X] T038 [US4] Crear `app/backend/src/Modules/Teams/Features/TeamMembers/RegisterTeamMember/RegisterTeamMemberValidator.cs`: `AbstractValidator<RegisterTeamMemberCommand>` con `NotEmpty` + no solo espacios sobre `Name` y `Role` (claves `name`/`role` de `TeamMemberRules`, mensajes en español) y SIN `MaximumLength` (ADR-007). Depende de T030, T034
- [X] T039 [US4] Mostrar en `register-member-dialog.component.{ts,html}` los errores 400 del servidor (por campo `errors.name`/`errors.role` y `detail`) sin cerrar el diálogo ni perder los valores. Depende de T033, T037

**Checkpoint**: US1 y US4 operativas; ningún dato inválido se persiste

---

## Phase 5: User Story 5 - Protección de acceso y resiliencia ante fallos (Priority: P1)

**Goal**: Las tres operaciones responden 401 sin credenciales válidas y el registro responde 500 sin trazas ni miembro parcial ante un fallo de persistencia.

**Independent Test**: Sin token, con token inválido y expirado → 401 en las tres rutas; con `SaveChangesAsync` fallando → 500 ProblemDetails sin traza y sin fila.

### Tests for User Story 5 ⚠️

- [X] T040 [P] [US5] Escribir `app/backend/tests/Integration/Teams/TeamsAuthTests.cs`: `POST /api/team-members`, `GET /api/team-members` y `GET /api/technical-roles` sin token, con token inválido y con token expirado → 401; verificar que no se creó ninguna fila ni se leyó dato alguno
- [X] T041 [P] [US5] Escribir `app/backend/tests/Integration/Teams/RegisterTeamMemberFailureTests.cs`: forzar fallo de persistencia en el `POST` (interceptor de prueba que lanza en `SavingChangesAsync`) → 500 `application/problem+json` sin traza ni mensaje interno, y `teams."TeamMembers"` sin filas
- [X] T042 [P] [US5] Añadir en `register-member-dialog.component.spec.ts` el caso 500: el diálogo permanece abierto, conserva los valores, muestra un mensaje genérico sin exponer el cuerpo de la respuesta y rehabilita el botón (estado 10 del UX); y el caso 401 sin cierre silencioso (estado 9)

### Implementation for User Story 5

- [X] T043 [US5] Verificar que `RegisterTeamMemberEndpoint` (T032), `ListTeamMembersEndpoint` (T048) y `ListTechnicalRolesEndpoint` (T055) usan `.RequireAuthorization()` y que el 500 y el 401 salen del `CustomExceptionHandler` existente sin cambios en `Shared`; corregir en `app/backend/src/Modules/Teams/Features/**/*Endpoint.cs` lo que haga fallar T040/T041. Depende de T032, T048, T055
- [X] T044 [US5] Implementar en `register-member-dialog.component.{ts,html}` el manejo de 500 y 401 descrito en T042 (mensaje genérico, sin trazas, valores conservados). Depende de T033, T042

**Checkpoint**: Las historias P1 (US1, US4, US5) están completas

---

## Phase 6: User Story 2 - Consultar los miembros registrados (Priority: P2)

**Goal**: `GET /api/team-members` devuelve exactamente los miembros registrados (`id`, `name`, `role`), o `[]`, y la página `/equipos` los muestra.

**Independent Test**: Con 0 y con N miembros → 200 con el contenido exacto y sin modificar datos; la página muestra la grilla o el estado vacío y el botón "Registrar miembro".

### Tests for User Story 2 ⚠️

- [X] T045 [P] [US2] Escribir `app/backend/tests/Unit/Teams/ListTeamMembersQueryHandlerTests.cs`: con `TeamsInMemoryDb`, devuelve exactamente los miembros con `id`, `name` y nombre de rol, ordenados por `CreatedAt` y `Id`; devuelve lista vacía sin miembros; no modifica datos
- [X] T046 [P] [US2] Escribir `app/backend/tests/Integration/Teams/ListTeamMembersTests.cs`: 200 `[]` sin miembros; 200 con exactamente los dos miembros registrados (`id`, `name`, `role`, sin `createdAt`/`createdBy`); rendimiento (SC-007): con 100 miembros sembrados la consulta responde en < 2 s
- [X] T047 [P] [US2] Escribir `app/frontend/src/app/features/teams/components/team-page/team-page.component.spec.ts` (debe fallar): muestra la grilla con identificador, nombre y rol; con lista vacía muestra "Aún no hay miembros registrados en el equipo."; error de lectura muestra un mensaje genérico con botón `Reintentar` que vuelve a consultar y no expone el cuerpo de la respuesta; el botón "Registrar miembro" abre el diálogo; tras el evento `registered` muestra un toast con los datos devueltos por el servidor y consulta de nuevo la lista (sin caché entre navegaciones)

### Implementation for User Story 2

- [X] T048 [US2] Crear `app/backend/src/Modules/Teams/Features/TeamMembers/ListTeamMembers/ListTeamMembersQuery.cs` (`ListTeamMembersQuery : IQuery<IReadOnlyList<TeamMemberResponse>>`) y `ListTeamMembersQueryHandler.cs`: una sola consulta con `JOIN` local a `TechnicalRoles`, `AsNoTracking()`, orden `CreatedAt` y `Id`, proyección directa a `TeamMemberResponse`, `ToListAsync(cancellationToken)`. Depende de T022, T045
- [X] T049 [US2] Crear `app/backend/src/Modules/Teams/Features/TeamMembers/ListTeamMembers/ListTeamMembersEndpoint.cs`: `MapGet("/api/team-members", ...)`, `.RequireAuthorization()`, `Produces<IReadOnlyList<TeamMemberResponse>>(200)`, `ProducesProblem` 401/500, `CancellationToken` propagado. Depende de T048
- [X] T050 [US2] Crear `app/frontend/src/app/features/teams/components/team-page/team-page.component.{ts,html,scss}`: componente standalone `OnPush` con `p-breadcrumb` ("Inicio > Equipos y Roles > Miembros"), `p-tabs` (pestañas "Miembros" y "Roles técnicos", pestaña activa derivada de la URL `equipos` o `equipos/roles`), `p-table` de miembros con columnas IDENTIFICADOR/NOMBRE/ROL, estado vacío, error de lectura con `Reintentar`, botón "Registrar miembro" (zona superior derecha) que abre `<app-register-member-dialog>`, `p-toast` y refresco de la lista tras `registered`; estado en Signals, i18n, tema neutral, sin acciones de editar/desactivar/eliminar (estados 1, 2 y 5 a 6 del UX). Depende de T025, T033, T047
- [X] T051 [US2] Añadir en `app/frontend/src/app/app.routes.ts` el bloque `equipos` con `canActivate: [authGuard]`, `providers: [MessageService]` y las rutas `equipos` y `equipos/roles` (con `loadComponent` de `TeamPageComponent`), sin tocar las rutas existentes de `backlog` y `sprints`. Depende de T050

**Checkpoint**: US2 funcional y verificable por API y en `/equipos`

---

## Phase 7: User Story 3 - Consultar el catálogo de roles técnicos (Priority: P2)

**Goal**: `GET /api/technical-roles` devuelve el catálogo (al menos "Desarrollo" y "QA", con `id` y `name`) y la pestaña "Roles técnicos" lo muestra.

**Independent Test**: Solicitar el catálogo → 200 con "Desarrollo" y "QA" y los GUID de la semilla, sin modificar datos; `/equipos/roles` muestra la grilla de roles.

### Tests for User Story 3 ⚠️

- [X] T052 [P] [US3] Escribir `app/backend/tests/Unit/Teams/ListTechnicalRolesQueryHandlerTests.cs`: devuelve los roles ordenados por `Name` con `id` y `name`, incluyendo "Desarrollo" y "QA"
- [X] T053 [P] [US3] Escribir `app/backend/tests/Integration/Teams/ListTechnicalRolesTests.cs`: 200 con exactamente "Desarrollo" y "QA", cada uno con su `id` (los GUID de `TechnicalRoleSeed`) y `name`; sin modificar datos; rendimiento < 2 s (SC-007); no existe ruta de alta, edición ni borrado de roles (`POST`/`PUT`/`DELETE /api/technical-roles` → 404/405)
- [X] T054 [P] [US3] Añadir en `team-page.component.spec.ts` el caso de la pestaña "Roles técnicos": carga `listRoles()` y muestra IDENTIFICADOR/NOMBRE, con el breadcrumb "Inicio > Equipos y Roles > Roles técnicos" (estado 3 del UX), error de lectura con `Reintentar`

### Implementation for User Story 3

- [X] T055 [US3] Crear `app/backend/src/Modules/Teams/Features/TechnicalRoles/ListTechnicalRoles/ListTechnicalRolesQuery.cs` (`ListTechnicalRolesQuery : IQuery<IReadOnlyList<TechnicalRoleResponse>>`), `ListTechnicalRolesQueryHandler.cs` (`AsNoTracking()`, orden por `Name`, proyección a `TechnicalRoleResponse`, `CancellationToken` propagado) y `ListTechnicalRolesEndpoint.cs` (`MapGet("/api/technical-roles", ...)`, `.RequireAuthorization()`, `Produces<IReadOnlyList<TechnicalRoleResponse>>(200)`, `ProducesProblem` 401/500). Depende de T022, T052
- [X] T056 [US3] Implementar en `team-page.component.{ts,html}` la pestaña "Roles técnicos" con `p-table` de solo lectura (sin alta ni edición de roles) y el manejo de error con `Reintentar`. Depende de T050, T054

**Checkpoint**: Las cinco historias son funcionales e independientemente verificables

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Verificación final y no regresión

- [X] T057 [P] Ejecutar `dotnet build app/backend/TechWorkHub.sln` y `dotnet test app/backend/TechWorkHub.sln` (integración de Docker en serie): todas las pruebas de Teams en verde y las suites de HU-001 a HU-004 sin modificaciones y en verde (400, 401 y 500 conservan su formato)
- [ ] T058 [P] Ejecutar `npm test` y `npm run build` en `app/frontend` (Node >= 22.22.3): sin regresiones en `features/backlog` ni `features/sprints`
- [X] T059 Verificar con `git diff --stat main...HEAD` que fuera de `Modules/Teams`, `features/teams` y los tests nuevos solo cambiaron `TechWorkHub.sln`, `Api.csproj`, `Program.cs` y `app.routes.ts`; revertir cualquier otro cambio (FR-014)
- [X] T060 Revisar que ningún `ILogger` de `Modules/Teams` escribe el nombre del miembro y que ningún `Teams` consulta tablas de otro schema (`grep` sobre `app/backend/src/Modules/Teams/`)
- [ ] T061 Recorrer los 10 escenarios de `specs/012-HU_miembros_equipo_y_roles_tecnicos/quickstart.md` (API y validación de frontend) y registrar el resultado
- [X] T062 [P] Revisar que `app/backend/src/Modules/Teams/` no contiene código sin uso (p. ej. `ITeamsDbContext` solo con los `DbSet` necesarios) y que el contrato `contracts/teams-api.openapi.yaml` coincide con los endpoints implementados

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sin dependencias
- **Foundational (Phase 2)**: depende de Setup; BLOQUEA todas las historias
- **US1 (P1)**, **US4 (P1)** y **US5 (P1)**: dependen de Foundational. US4 y US5 comparten endpoint, handler y diálogo con US1: ejecutar US1 → US4 → US5
- **US2 (P2)** y **US3 (P2)**: dependen de Foundational y de que exista el diálogo de US1 para montarlo en `team-page` (T050). US3 amplía `team-page` creada en US2 (T056 depende de T050)
- **Polish (Phase 8)**: depende de todas las historias deseadas

### User Story Dependencies

- **US1**: tras Foundational. El selector del diálogo consume `GET /api/technical-roles` (T055, US3 backend): las pruebas del diálogo usan servicio simulado, pero la validación extremo a extremo requiere T055
- **US4**: valida el mismo `POST` de US1 (T038 añade el validador; la rama "rol inexistente" ya está en el handler T031)
- **US5**: T043 cierra la verificación de seguridad de los tres endpoints, por lo que va tras T048 y T055
- **US2**: independiente en backend; el frontend (T050) integra el diálogo de US1
- **US3**: backend independiente; el frontend extiende la página de US2

### Within Each User Story

- Pruebas (marcadas ⚠️) primero y deben fallar
- Dominio → handler → endpoint → frontend
- Cada historia queda verificable antes de pasar a la siguiente prioridad

### Parallel Opportunities

- Setup: T002, T003, T005, T006 en paralelo tras T001
- Foundational: T007, T008, T009 en paralelo; T013, T014, T015 en paralelo; T019, T020, T022, T023 en paralelo
- Pruebas de cada historia (todas las marcadas [P]) en paralelo; backend y frontend de una misma historia en paralelo salvo las dependencias indicadas
- US2 y US3 backend (T048, T049, T055) pueden hacerse en paralelo por distintas personas

---

## Parallel Example: User Story 1

```bash
# Lanzar juntas las pruebas de US1:
Task: "RegisterTeamMemberCommandHandlerTests en app/backend/tests/Unit/Teams/RegisterTeamMemberCommandHandlerTests.cs"
Task: "RegisterTeamMemberTests en app/backend/tests/Integration/Teams/RegisterTeamMemberTests.cs"
Task: "RegisterTeamMemberNoRegressionTests en app/backend/tests/Integration/Teams/RegisterTeamMemberNoRegressionTests.cs"
Task: "register-member-dialog.component.spec.ts en app/frontend/src/app/features/teams/components/register-member-dialog/"
```

---

## Implementation Strategy

### MVP First (US1 + P1)

1. Completar Phase 1 (Setup) y Phase 2 (Foundational)
2. Completar US1 (registrar), US4 (rechazos) y US5 (401/500): el registro seguro e íntegro
3. **PARAR y VALIDAR**: escenarios 2, 3, 6, 7, 8 y 9 del quickstart (el escenario 1 requiere US3 backend)
4. Desplegar/demostrar si procede

### Incremental Delivery

1. Setup + Foundational → módulo y migración listos
2. US1 → registro vía API (MVP) → US4 → US5
3. US2 → consulta de miembros y página `/equipos`
4. US3 → catálogo de roles y pestaña "Roles técnicos"
5. Polish → no regresión, quickstart completo

### Parallel Team Strategy

1. El equipo completa Setup + Foundational
2. Después: Dev A backend US1/US4/US5, Dev B backend US2/US3, Dev C frontend (`team-page`, diálogo)

---

## Notes

- [P] = archivos distintos, sin dependencias pendientes
- La etiqueta [Story] mapea cada tarea a su historia para trazabilidad
- Verificar que las pruebas fallan antes de implementar; confirmar tras cada tarea o grupo lógico
- Evitar: tareas vagas, conflictos en el mismo archivo, imponer cardinalidad miembro–rol, unicidad o límites de nombre (FR-015, ADR-007)
- Los códigos `201` y el orden de las consultas son ⚠️ [PROPUESTO] (research R-08)
