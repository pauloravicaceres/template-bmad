---

description: "Lista de tareas para HU-003: Gestión de Sprint de Dos Semanas (Crear y Consultar)"
---

# Tasks: Gestión de Sprint de Dos Semanas (Crear y Consultar)

**Input**: Documentos de diseño en `/specs/003-HU_gestion_sprint_dos_semanas/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/sprints-api.openapi.yaml, quickstart.md

**Tests**: Se incluyen tareas de prueba porque el plan exige TDD (xUnit + FluentAssertions + Testcontainers; Jest en frontend), sin pruebas tautológicas. Las pruebas se escriben primero y deben fallar antes de implementar.

**Organization**: Tareas agrupadas por historia de usuario. US1 y US2 comparten el endpoint `POST /api/sprints` (P1); US3 y US4 son consultas (P2).

## Format: `[ID] [P?] [Story] Descripción`

- **[P]**: Se puede ejecutar en paralelo (archivos distintos, sin dependencias)
- **[Story]**: Historia de usuario a la que pertenece (US1..US4)
- Todas las rutas son relativas a la raíz del repositorio

## Path Conventions

- Backend: `app/backend/src/Modules/Sprints/`, pruebas en `app/backend/tests/Unit/Sprints/` y `app/backend/tests/Integration/Sprints/`
- Frontend: `app/frontend/src/app/features/sprints/`
- Patrón de referencia: `app/backend/src/Modules/Backlog/` y `app/frontend/src/app/features/backlog/`
- Restricción: no modificar `Modules/Backlog`, `Modules/Application`, `BuildingBlocks/Shared`, `core/auth` ni `features/backlog`. Solo se permite tocar fuera del módulo: `Api.csproj`, `Program.cs`, `TechWorkHub.sln` y `app.routes.ts`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Esqueleto del módulo `Sprints` y de los proyectos de prueba

- [X] T001 Crear `app/backend/src/Modules/Sprints/Sprints.csproj` (net8.0) replicando referencias y paquetes de `app/backend/src/Modules/Backlog/Backlog.csproj` (Carter 8.1.0, MediatR 12.4.1, FluentValidation 11.9.2, Mapster 7.4.0, EF Core Npgsql 8.0.11, referencia a `Shared`)
- [X] T002 [P] Crear `app/backend/tests/Unit/Sprints/Sprints.UnitTests.csproj` replicando `app/backend/tests/Unit/Backlog/Backlog.UnitTests.csproj` y referenciando `Sprints.csproj`
- [X] T003 [P] Crear `app/backend/tests/Integration/Sprints/Sprints.IntegrationTests.csproj` replicando `app/backend/tests/Integration/Backlog/Backlog.IntegrationTests.csproj` y referenciando `Sprints.csproj` y `Api.csproj`
- [X] T004 Añadir `Sprints`, `Sprints.UnitTests` y `Sprints.IntegrationTests` a `app/backend/TechWorkHub.sln` (`dotnet sln add`)
- [X] T005 [P] Crear la estructura de carpetas del frontend `app/frontend/src/app/features/sprints/{components,services,models}/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Dominio, persistencia y registro del módulo que TODAS las historias necesitan

**⚠️ CRITICAL**: Ninguna historia puede comenzar hasta completar esta fase

- [X] T006 [P] Crear `app/backend/src/Modules/Sprints/Domain/Sprints/SprintRules.cs`: constantes `WindowDays = 14`, `IdentificationMaxLength = 100`, `DateFormat = "yyyy-MM-dd"` y mensajes de error (identificación obligatoria, formato de fecha, fin ≤ inicio, "el Sprint debe abarcar exactamente una ventana de 2 semanas"); fuente única de la regla (ADR-005)
- [X] T007 [P] Escribir pruebas (deben fallar) de dominio en `app/backend/tests/Unit/Sprints/SprintDomainTests.cs`: `Sprint.Create` crea con `EndDate = StartDate + 13`; lanza `BadRequestException` para ventanas de 7, 13, 15 y 21 días, fin ≤ inicio e identificación vacía; `Id` generado distinto de `Guid.Empty`
- [X] T008 Crear `app/backend/src/Modules/Sprints/Domain/Sprints/Sprint.cs`: `Sprint : Aggregate<Guid>, IAuditableEntity` con `Identification` (string), `StartDate` y `EndDate` (`DateOnly`), `CreatedAt`, `CreatedBy`, `LastModified`, `LastModifiedBy`; método fábrica `Sprint.Create(identification, startDate, endDate)` que repite la invariante usando `SprintRules` y lanza `BadRequestException`; sin estado ni relación con tarjetas (FR-013, FR-014). Depende de T006
- [X] T009 [P] Crear `app/backend/src/Modules/Sprints/Data/ISprintsDbContext.cs` con `DbSet<Sprint> Sprints` y `SaveChangesAsync(CancellationToken)`, siguiendo `IBacklogDbContext`
- [X] T010 Crear `app/backend/src/Modules/Sprints/Data/SprintsDbContext.cs` con `SchemaName = "sprints"`, `HasDefaultSchema("sprints")` y `ApplyConfigurationsFromAssembly`. Depende de T008, T009
- [X] T011 Crear `app/backend/src/Modules/Sprints/Data/Configurations/SprintConfiguration.cs`: tabla `Sprints`, PK `Id` (uuid), `Identification` `varchar(100)` NOT NULL, `StartDate` y `EndDate` `date` NOT NULL, `CreatedAt` `timestamptz` NOT NULL, `CreatedBy` `varchar` NOT NULL, `LastModified` `timestamptz` NULL, `LastModifiedBy` `varchar` NULL; `CK_Sprints_Window` con `("EndDate" - "StartDate") = 13` derivado de `SprintRules.WindowDays - 1`; SIN índice único sobre `Identification`, sin FK hacia `backlog`/`application`. Depende de T010
- [X] T012 [P] Crear `app/backend/src/Modules/Sprints/Data/SprintsDbContextFactory.cs` (design-time) siguiendo la factoría del módulo Backlog
- [X] T013 Generar la migración `InitialSprintsSchema` en `app/backend/src/Modules/Sprints/Data/Migrations/` (`dotnet ef migrations add InitialSprintsSchema`), verificando que solo toca el schema `sprints` e incluye `CK_Sprints_Window`. Depende de T011, T012
- [X] T014 Crear `app/backend/src/Modules/Sprints/SprintsModule.cs` con `AddSprintsModule(IServiceCollection, IConfiguration)` (MediatR + `ValidationBehavior<,>`, `AddValidatorsFromAssembly`, `AddDbContext<SprintsDbContext>` con `AuditableEntityInterceptor` y tabla de historial en schema `sprints`, registro de `ISprintsDbContext`) y `MigrateSprintsModuleAsync`. Depende de T010
- [X] T015 Registrar el módulo en `app/backend/src/Bootstrapper/Api/Api.csproj` (`ProjectReference` a `Sprints.csproj`) y en `app/backend/src/Bootstrapper/Api/Program.cs` (`AddSprintsModule` y `MigrateSprintsModuleAsync` junto a los de Backlog; asegurar que Carter descubre los módulos del ensamblado `Sprints`). Depende de T014
- [X] T016 [P] Crear `app/backend/tests/Integration/Sprints/PostgresFixture.cs` y `SprintsApiFactory.cs` (Testcontainers PostgreSQL, autenticación de prueba con `sub`), reutilizando el patrón de `app/backend/tests/Integration/Backlog/PostgresFixture.cs` y `BacklogApiFactory.cs`
- [X] T017 [P] Escribir `app/backend/tests/Integration/Sprints/MigrationsPostgresTests.cs`: la migración crea `sprints."Sprints"`; una inserción SQL con ventana de 13 o 15 días es rechazada por `CK_Sprints_Window`; una de 14 días se acepta (FR-015, quickstart #8). Depende de T013, T016

**Checkpoint**: Dominio, BD y módulo registrados; las historias ya pueden implementarse

---

## Phase 3: User Story 1 - Crear un Sprint con ventana válida de 2 semanas (Priority: P1) 🎯 MVP

**Goal**: Un usuario autenticado crea un Sprint (`POST /api/sprints`) y recibe 201 con `Location` y los cuatro datos; se persiste con auditoría `CreatedAt`/`CreatedBy` (= `sub`), sin tocar el backlog.

**Independent Test**: POST con fechas separadas por 13 días → 201, fila en `sprints."Sprints"` con `CreatedBy` = `sub`, sin cambios en `backlog."BacklogItems"`; sin token → 401 sin persistir.

### Tests for User Story 1 ⚠️ (escribir primero, deben fallar)

- [X] T018 [P] [US1] Pruebas unitarias en `app/backend/tests/Unit/Sprints/CreateSprintCommandHandlerTests.cs`: crea y persiste con `CreatedBy` del `ICurrentUser.UserId`, devuelve `SprintResponse` con 4 campos, lanza `UnauthorizedAccessException` si no hay `UserId`, respeta `CancellationToken` (patrón de `CreateBacklogItemCommandHandlerTests.cs`)
- [X] T019 [P] [US1] Pruebas de integración en `app/backend/tests/Integration/Sprints/CreateSprintTests.cs`: 201 con `Location` y cuerpo `{id, identification, startDate, endDate}` para `2026-10-05`→`2026-10-18`; fila con `CreatedAt` y `CreatedBy` = `sub`; backlog sin cambios (FR-013, SC-006); 401 sin token / token inválido sin persistir (FR-010); 500 sin trazas internas ni Sprint parcial ante fallo de persistencia (FR-011, FR-012)

### Implementation for User Story 1

- [X] T020 [P] [US1] Crear `app/backend/src/Modules/Sprints/Features/Sprints/CreateSprint/CreateSprintCommand.cs` con `CreateSprintCommand(string? Identification, string? StartDate, string? EndDate) : IRequest<SprintResponse>`, y `app/backend/src/Modules/Sprints/Features/Sprints/SprintResponse.cs` con `SprintResponse(Guid Id, string Identification, DateOnly StartDate, DateOnly EndDate)` (compartido por las cuatro historias)
- [X] T021 [US1] Crear `app/backend/src/Modules/Sprints/Features/Sprints/CreateSprint/CreateSprintCommandHandler.cs`: resuelve `ICurrentUser.UserId` ANTES de acceder a datos (sin claim → `UnauthorizedAccessException`), parsea fechas con `DateOnly.ParseExact(..., "yyyy-MM-dd", InvariantCulture)`, llama a `Sprint.Create`, persiste con `SaveChangesAsync(cancellationToken)` y mapea con Mapster (`Adapt<SprintResponse>()`). Depende de T008, T014, T020
- [X] T022 [US1] Crear `app/backend/src/Modules/Sprints/Features/Sprints/CreateSprint/CreateSprintEndpoint.cs` (`ICarterModule`): `POST /api/sprints`, `.RequireAuthorization()`, responde `Results.Created($"/api/sprints/{id}", response)` (201 + `Location`), sin `[ApiController]`, propagando `CancellationToken`. Depende de T021
- [X] T023 [US1] Verificar que `CustomExceptionHandler` (en `Shared`) mapea `UnauthorizedAccessException`→401 y excepción genérica→500 sin trazas; solo documentar el hallazgo, sin modificar `Shared`. Si falta un mapeo, registrarlo como punto abierto

**Checkpoint**: US1 funcional y verificable de forma independiente (MVP)

---

## Phase 4: User Story 2 - Rechazo de Sprints con datos inválidos (Priority: P1)

**Goal**: Rechazar con 400 (ProblemDetails con `errors` por campo) toda solicitud con ventana ≠ 14 días, fin ≤ inicio, o campos ausentes/malformados, sin persistir.

**Independent Test**: Ventanas de 7, 13, 15 y 21 días, fin ≤ inicio, identificación vacía o > 100, fecha ausente o `"no-es-fecha"` → 400 y tabla sin filas nuevas.

### Tests for User Story 2 ⚠️

- [X] T024 [P] [US2] Pruebas unitarias en `app/backend/tests/Unit/Sprints/CreateSprintValidatorTests.cs` (casos parametrizados, sin tautologías): ventanas de 6, 12, 14 (válida), 20 días y límites ±1 día respecto a 14; fin = inicio y fin < inicio con mensaje de FR-004; identificación vacía/espacios/`null`, de 101 caracteres (rechazada) y de 100 (válida); fecha de inicio o fin `null`, vacía, `"no-es-fecha"`, `"05/10/2026"` y `"2026-13-40"`; los errores de ventana caen sobre `EndDate`
- [X] T025 [P] [US2] Pruebas de integración en `app/backend/tests/Integration/Sprints/CreateSprintValidationTests.cs`: 400 `application/problem+json` con `errors` por campo (camelCase: `identification`, `startDate`, `endDate`) y mensaje "ventana de 2 semanas" para ventanas de 7, 13, 15 y 21 días; fin ≤ inicio; campos ausentes o malformados; en todos los casos `sprints."Sprints"` queda sin filas nuevas (FR-012, SC-002)

### Implementation for User Story 2

- [X] T026 [US2] Crear `app/backend/src/Modules/Sprints/Features/Sprints/CreateSprint/CreateSprintValidator.cs`: `AbstractValidator<CreateSprintCommand>` con identificación obligatoria y máximo `SprintRules.IdentificationMaxLength`; `StartDate`/`EndDate` obligatorias y formato exacto `yyyy-MM-dd` con `DateOnly.TryParseExact` (`InvariantCulture`, `DateTimeStyles.None`); si ambas parsean: fin ≤ inicio → mensaje FR-004 y ventana ≠ `SprintRules.WindowDays` → mensaje de ventana de 2 semanas, ambos sobre `EndDate`. Depende de T006, T020
- [X] T027 [US2] Ejecutar `app/backend/tests/Integration/Sprints/CreateSprintValidationTests.cs` y confirmar que `ValidationBehavior` + `CustomExceptionHandler` devuelven 400 con `errors` por campo en camelCase; si no lo cumplen, documentarlo como hallazgo (no modificar `Shared`). Depende de T025, T026

**Checkpoint**: US1 y US2 completas: creación válida y rechazo consistente (FR-001..FR-006, FR-011..FR-015)

---

## Phase 5: User Story 3 - Consultar el listado de Sprints (Priority: P2)

**Goal**: `GET /api/sprints` devuelve 200 con todos los Sprints (`id`, `identification`, `startDate`, `endDate`), sin modificar datos.

**Independent Test**: Con Sprints sembrados, el listado contiene exactamente esos Sprints; sin token → 401; < 2 s con 100 Sprints.

### Tests for User Story 3 ⚠️

- [X] T028 [P] [US3] Pruebas unitarias en `app/backend/tests/Unit/Sprints/ListSprintsQueryHandlerTests.cs`: devuelve exactamente los Sprints registrados con 4 campos, orden determinista por `StartDate` asc y luego `Id`, lista vacía cuando no hay datos
- [X] T029 [P] [US3] Pruebas de integración en `app/backend/tests/Integration/Sprints/ListSprintsTests.cs`: 200 con exactamente los Sprints sembrados; 401 sin credenciales; sin cambios en datos tras consultar; con 100 Sprints sembrados responde en < 2 s (SC-005, quickstart #10)

### Implementation for User Story 3

- [X] T030 [P] [US3] Crear `app/backend/src/Modules/Sprints/Features/Sprints/ListSprints/ListSprintsQuery.cs`: `ListSprintsQuery : IRequest<IReadOnlyList<SprintResponse>>`
- [X] T031 [US3] Crear `app/backend/src/Modules/Sprints/Features/Sprints/ListSprints/ListSprintsQueryHandler.cs`: `AsNoTracking()`, orden `StartDate` asc luego `Id`, proyección a `SprintResponse` (sin paginación ni filtros), `ToListAsync(cancellationToken)`. Depende de T014, T030
- [X] T032 [US3] Crear `app/backend/src/Modules/Sprints/Features/Sprints/ListSprints/ListSprintsEndpoint.cs` (`ICarterModule`): `GET /api/sprints`, `.RequireAuthorization()`, 200 con arreglo JSON. Depende de T031

**Checkpoint**: US3 funcional e independiente

---

## Phase 6: User Story 4 - Consultar el detalle de un Sprint (Priority: P2)

**Goal**: `GET /api/sprints/{id:guid}` devuelve 200 con los cuatro datos o 404 si no existe.

**Independent Test**: Id existente → 200; id inexistente → 404; sin token → 401.

### Tests for User Story 4 ⚠️

- [X] T033 [P] [US4] Pruebas unitarias en `app/backend/tests/Unit/Sprints/GetSprintByIdQueryHandlerTests.cs`: devuelve el Sprint con 4 campos; lanza `NotFoundException` cuando el id no existe
- [X] T034 [P] [US4] Pruebas de integración en `app/backend/tests/Integration/Sprints/GetSprintByIdTests.cs`: 200 con datos; 404 `application/problem+json` para un GUID inexistente; 401 sin credenciales; un id que no es GUID no coincide con la ruta

### Implementation for User Story 4

- [X] T035 [P] [US4] Crear `app/backend/src/Modules/Sprints/Features/Sprints/GetSprintById/GetSprintByIdQuery.cs`: `GetSprintByIdQuery(Guid Id) : IRequest<SprintResponse>`
- [X] T036 [US4] Crear `app/backend/src/Modules/Sprints/Features/Sprints/GetSprintById/GetSprintByIdQueryHandler.cs`: `AsNoTracking()`, busca por `Id` con `FirstOrDefaultAsync(cancellationToken)`, lanza `NotFoundException` si no existe (FR-009) y proyecta a `SprintResponse`. Depende de T014, T035
- [X] T037 [US4] Crear `app/backend/src/Modules/Sprints/Features/Sprints/GetSprintById/GetSprintByIdEndpoint.cs` (`ICarterModule`): `GET /api/sprints/{id:guid}`, `.RequireAuthorization()`, 200/404. Depende de T036

**Checkpoint**: Las 4 historias del backend completas

---

## Phase 7: Frontend (cubre US1–US4 en la SPA)

**Purpose**: Tres páginas Angular 22 Zoneless + Signals (`sprint-form`, `sprint-list`, `sprint-detail`), PrimeNG tema neutral, i18n, componentes standalone `OnPush`. UX de referencia: `documents/designer-ux/ux_003_gestion_sprint_dos_semanas.md`.

### Tests (escribir primero)

- [X] T038 [P] [US1] Pruebas Jest en `app/frontend/src/app/features/sprints/services/sprint-api.service.spec.ts`: `create` hace POST `/api/sprints`, `list` hace GET `/api/sprints`, `getById` hace GET `/api/sprints/{id}`; las fechas se envían como `yyyy-MM-dd`
- [X] T039 [P] [US2] Pruebas Jest en `app/frontend/src/app/features/sprints/components/sprint-form/sprint-form.component.spec.ts`: identificación obligatoria (máx. 100), fechas obligatorias, el 400 del servidor se muestra por campo, el botón se deshabilita mientras se envía (evita doble envío), tras 201 navega a `/sprints`
- [X] T040 [P] [US3] Pruebas Jest en `app/frontend/src/app/features/sprints/components/sprint-list/sprint-list.component.spec.ts`: estados de carga, vacío, error y con datos; consulta fresca al servidor en cada navegación
- [X] T041 [P] [US4] Pruebas Jest en `app/frontend/src/app/features/sprints/components/sprint-detail/sprint-detail.component.spec.ts`: muestra identificación y fechas; estado 404 "Sprint no existe"; estado de error

### Implementation

- [X] T042 [P] [US1] Crear `app/frontend/src/app/features/sprints/models/sprint.models.ts`: `Sprint`, `CreateSprintRequest` y tipo de error de validación por campo, siguiendo `app/frontend/src/app/features/backlog/models/backlog-item.models.ts`
- [X] T043 [US1] Crear `app/frontend/src/app/features/sprints/services/sprint-api.service.ts` (`HttpClient`: `create`, `list`, `getById`), siguiendo `app/frontend/src/app/features/backlog/services/backlog-api.service.ts`. Depende de T042
- [X] T044 [US2] Crear `app/frontend/src/app/features/sprints/components/sprint-form/sprint-form.component.ts` (y su plantilla): standalone `OnPush`, formulario reactivo tipado, PrimeNG tema neutral, textos con i18n nativo, fechas enviadas como `yyyy-MM-dd`, errores 400 por campo, navegación a `/sprints` tras 201. Depende de T043
- [X] T045 [US3] Crear `app/frontend/src/app/features/sprints/components/sprint-list/sprint-list.component.ts` (y su plantilla): tabla con identificación, inicio y fin; estados cargando/vacío/error con Signals; enlace al detalle y a `/sprints/nuevo`. Depende de T043
- [X] T046 [US4] Crear `app/frontend/src/app/features/sprints/components/sprint-detail/sprint-detail.component.ts` (y su plantilla): lee `:id` de la ruta, muestra identificación y fechas, maneja 404 y error. Depende de T043
- [X] T047 Añadir rutas lazy `/sprints`, `/sprints/nuevo` y `/sprints/:id` (con el guard de autenticación existente) en `app/frontend/src/app/app.routes.ts`. Depende de T044, T045, T046
- [X] T048 [P] Añadir las claves de traducción i18n de las tres páginas con el mecanismo de i18n existente del frontend (mismo patrón que `features/backlog`)

**Checkpoint**: Flujo UI completo (quickstart #11)

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Verificación final y calidad transversal

- [X] T049 [P] Revisar que los tres endpoints tienen `.RequireAuthorization()` y que `CancellationToken` se propaga de endpoint a handler y a EF Core en `app/backend/src/Modules/Sprints/Features/`
- [X] T050 [P] Verificar ausencia de FK/navegación a otros schemas, de estados, de unicidad y de paginación en `app/backend/src/Modules/Sprints/` (FR-013, FR-014, ADR-006)
- [X] T051 Ejecutar `dotnet test app/backend/TechWorkHub.sln` y confirmar que `Sprints.UnitTests`, `Sprints.IntegrationTests` y las pruebas de HU-001/HU-002 pasan sin regresión
- [ ] T052 Ejecutar `cd app/frontend && npm test && npm run build` y confirmar que pasan
- [ ] T053 Validar los escenarios 1–11 de `specs/003-HU_gestion_sprint_dos_semanas/quickstart.md` contra la API y la UI en ejecución
- [X] T054 Confirmar con `git status` que no hay cambios fuera de los ficheros permitidos (módulo Sprints, `Api.csproj`, `Program.cs`, `TechWorkHub.sln`, `app.routes.ts` y `features/sprints` del frontend)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sin dependencias
- **Foundational (Phase 2)**: depende de Setup; BLOQUEA todas las historias
- **US1 (Phase 3) y US2 (Phase 4)**: dependen de Foundational. US2 añade el validador sobre el comando de US1 (T026 depende de T020); se entregan juntas como MVP
- **US3 (Phase 5) y US4 (Phase 6)**: dependen de Foundational y de `SprintResponse` (T020); pueden ir en paralelo con US1/US2 (las pruebas de integración siembran datos por DbContext/SQL)
- **Frontend (Phase 7)**: el contrato ya está fijado en el OpenAPI; puede avanzar en paralelo con el backend tras Setup
- **Polish (Phase 8)**: depende de todas las fases anteriores

### Dentro de cada historia

- Pruebas primero (deben fallar) → comando/consulta → handler → validador → endpoint
- Dominio (T006→T008) → DbContext (T010) → configuración (T011) → migración (T013) → módulo (T014) → registro en Api (T015)

### Parallel Opportunities

- Setup: T002, T003, T005 en paralelo
- Foundational: T006, T007, T009, T012, T016 en paralelo; T017 tras T013 y T016
- Las pruebas [P] de cada historia en paralelo entre sí
- US3 y US4 en paralelo por distintas personas
- Frontend: T038–T042 en paralelo; T044–T046 en paralelo una vez hecho T043

---

## Parallel Example: User Story 1

```bash
# Pruebas de US1 en paralelo:
Task: "Pruebas unitarias en app/backend/tests/Unit/Sprints/CreateSprintCommandHandlerTests.cs"
Task: "Pruebas de integración en app/backend/tests/Integration/Sprints/CreateSprintTests.cs"

# Fundacionales en paralelo:
Task: "SprintRules en app/backend/src/Modules/Sprints/Domain/Sprints/SprintRules.cs"
Task: "ISprintsDbContext en app/backend/src/Modules/Sprints/Data/ISprintsDbContext.cs"
Task: "SprintsDbContextFactory en app/backend/src/Modules/Sprints/Data/SprintsDbContextFactory.cs"
```

---

## Implementation Strategy

### MVP First (US1 + US2)

1. Completar Phase 1 (Setup) y Phase 2 (Foundational)
2. Completar Phase 3 (US1) y Phase 4 (US2): creación con validación completa
3. **PARAR y VALIDAR**: probar `POST /api/sprints` (quickstart #1–4, #7–9)

### Incremental Delivery

1. Setup + Foundational → base lista
2. US1 + US2 → creación y rechazo (MVP)
3. US3 → listado
4. US4 → detalle
5. Frontend → flujo completo en UI
6. Polish → verificación final

---

## Notes

- [P] = archivos distintos, sin dependencias
- La etiqueta [Story] mapea cada tarea a su historia; las tareas de frontend llevan la historia que cubren
- Fuente única de la regla de ventana: `SprintRules.WindowDays`, aplicada en validador, `Sprint.Create` y `CK_Sprints_Window`
- Fuera de alcance (no implementar): estados, apertura/cierre, modificación, cancelación, eliminación, unicidad de identificación, solapamiento, fecha en el pasado, paginación, eventos/Outbox/Redis e `ISprintModuleApi`
- Confirmar que las pruebas fallan antes de implementar; commit tras cada tarea o grupo lógico
