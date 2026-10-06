---

description: "Lista de tareas para HU-004: Asignación de Elementos del Backlog a un Sprint"
---

# Tasks: Asignación de Elementos del Backlog a un Sprint

**Input**: Documentos de diseño en `/specs/004-HU_asignacion_elementos_sprint/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/sprint-items-api.openapi.yaml, contracts/backlog-module-api.md, quickstart.md

**Tests**: Se incluyen tareas de prueba porque el plan exige TDD (xUnit + FluentAssertions + Testcontainers; Jest en frontend), sin pruebas tautológicas y con doble escrito a mano del contrato en unitarias. Las pruebas se escriben primero y deben fallar antes de implementar.

**Organization**: Tareas agrupadas por historia de usuario. US1 (asignar, incluye el 409 de la reconciliación spec ↔ SA), US3 (rechazos 400/404) y US4 (401/500) comparten el endpoint `POST /api/sprints/{sprintId}/items`; US2 es la consulta `GET`.

**Reconciliación vinculante**: la guía del SA prevalece sobre `spec.md`: un elemento pertenece a **un solo Sprint**; repetir la asignación (mismo u otro Sprint) responde **409 Conflict** por el índice único `UX_SprintItems_ItemId`. FR-015 de `spec.md` queda sin efecto.

## Format: `[ID] [P?] [Story] Descripción`

- **[P]**: Se puede ejecutar en paralelo (archivos distintos, sin dependencias)
- **[Story]**: Historia de usuario a la que pertenece (US1..US4)
- Todas las rutas son relativas a la raíz del repositorio

## Path Conventions

- Backend: `app/backend/src/Modules/Sprints/`, pruebas en `app/backend/tests/Unit/Sprints/` y `app/backend/tests/Integration/Sprints/`
- Frontend: `app/frontend/src/app/features/sprints/`
- Patrón de referencia: HU-003 (`Features/Sprints/CreateSprint`, `ListSprints`, `GetSprintById`) y `IApplicationModuleApi` en `Modules/Backlog/Contracts/`
- Restricción: solo se permite tocar fuera del módulo `Sprints`: `Backlog.csproj`, `BacklogModule.cs`, `BacklogModuleApi.cs`, `BuildingBlocks/Shared/Exceptions/` (409 aditivo), `app.routes.ts` y el botón en `sprint-detail`. NO modificar la entidad `Sprint`, `SprintRules`, la migración `InitialSprintsSchema`, `BacklogItem`/`BacklogDbContext`, `Modules/Application`, `core/auth` ni `features/backlog`.
- Sin RabbitMQ/MassTransit/Redis/Outbox, sin FKs ni consultas cross-schema; `CancellationToken` propagado hasta EF Core y el contrato.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Estructura de carpetas; el módulo y los proyectos de prueba ya existen (HU-003)

- [X] T001 [P] Crear las carpetas `app/backend/src/Modules/Sprints/Contracts/`, `app/backend/src/Modules/Sprints/Domain/SprintItems/` y `app/backend/src/Modules/Sprints/Features/SprintItems/{AssignItemToSprint,ListSprintItems}/`
- [X] T002 [P] Crear las carpetas del frontend `app/frontend/src/app/features/sprints/components/sprint-assigned-items/` y `app/frontend/src/app/features/sprints/components/assign-item-dialog/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Excepción 409, contrato in-process, dominio y persistencia que TODAS las historias necesitan

**⚠️ CRITICAL**: Ninguna historia puede comenzar hasta completar esta fase

- [X] T003 [P] Crear `app/backend/src/BuildingBlocks/Shared/Exceptions/ConflictException.cs` siguiendo el estilo de `NotFoundException.cs`/`BadRequestException.cs` (cambio estrictamente aditivo, ADR-005)
- [X] T004 Añadir en `app/backend/src/BuildingBlocks/Shared/Exceptions/CustomExceptionHandler.cs` la rama `ConflictException` → ProblemDetails con `Status = 409` y `Title = "Conflict"`, sin alterar las ramas 400/404/500 existentes. Depende de T003
- [ ] T005 [P] Crear `app/backend/src/Modules/Sprints/Contracts/IBacklogModuleApi.cs` con `Task<bool> ExistsAsync(Guid itemId, CancellationToken cancellationToken)`, `Task<IReadOnlyList<BacklogItemSummary>> GetSummariesAsync(IReadOnlyCollection<Guid> itemIds, CancellationToken cancellationToken)` y `record BacklogItemSummary(Guid Id, string Title, string Type, int DevPoints, int QAPoints)` (`Type` como `string`; sin estado ni descripción)
- [X] T006 [P] Crear `app/backend/src/Modules/Sprints/Domain/SprintItems/SprintItemRules.cs`: constantes de campo `SprintIdField = "sprintId"` y `ItemIdField = "itemId"`, `ItemIdUniqueIndexName = "UX_SprintItems_ItemId"` e `SprintIdIndexName = "IX_SprintItems_SprintId"`; mensajes en español (Sprint no encontrado, elemento no encontrado, conflicto "el elemento ya está asignado a un Sprint" sin revelar a cuál, identificador obligatorio, formato inválido)
- [X] T007 [P] Escribir pruebas (deben fallar) en `app/backend/tests/Unit/Sprints/SprintItemDomainTests.cs`: `SprintItem.Create` genera `Id` distinto de `Guid.Empty`, conserva `SprintId` e `ItemId`, y lanza `BadRequestException` si cualquiera es `Guid.Empty`
- [X] T008 Crear `app/backend/src/Modules/Sprints/Domain/SprintItems/SprintItem.cs`: `SprintItem : Aggregate<Guid>, IAuditableEntity` con `SprintId`, `ItemId`, `CreatedAt`, `CreatedBy`, `LastModified`, `LastModifiedBy`; fábrica `SprintItem.Create(Guid sprintId, Guid itemId)` que usa `SprintItemRules`; sin estado, sin orden y sin eventos de dominio (ADR-006). Depende de T006
- [X] T009 Añadir `DbSet<SprintItem> SprintItems` en `app/backend/src/Modules/Sprints/Data/ISprintsDbContext.cs` y `app/backend/src/Modules/Sprints/Data/SprintsDbContext.cs` (schema `sprints`). Depende de T008
- [X] T010 Crear `app/backend/src/Modules/Sprints/Data/Configurations/SprintItemConfiguration.cs`: tabla `SprintItems`, PK `Id` `uuid`, `SprintId` `uuid NOT NULL` con FK a `sprints."Sprints"("Id")` `ON DELETE RESTRICT`, `ItemId` `uuid NOT NULL` SIN FK, `CreatedAt` `timestamptz NOT NULL`, `CreatedBy` `varchar NOT NULL`, `LastModified` `timestamptz` NULL, `LastModifiedBy` `varchar` NULL; índice ÚNICO `UX_SprintItems_ItemId` sobre `ItemId` (nombre desde `SprintItemRules.ItemIdUniqueIndexName`) e índice no único `IX_SprintItems_SprintId`. Depende de T009
- [X] T011 Generar la migración `AddSprintItems` en `app/backend/src/Modules/Sprints/Data/Migrations/` (`dotnet ef migrations add AddSprintItems`), verificando que solo crea `sprints."SprintItems"` (sin tocar `Sprints`, `backlog` ni `application`). Depende de T010
- [X] T012 [P] Implementar `app/backend/src/Modules/Backlog/BacklogModuleApi.cs` (`IBacklogModuleApi`): `ExistsAsync` con `AnyAsync` y `GetSummariesAsync` con una sola consulta `WHERE Id = ANY(...)` sobre `IBacklogDbContext` (solo lectura, `AsNoTracking`, omite ids inexistentes, `Type` como `ToString()`, `CancellationToken` propagado, sin fallback ante error). Depende de T005
- [X] T013 Añadir `ProjectReference` a `Sprints.csproj` en `app/backend/src/Modules/Backlog/Backlog.csproj` y registrar `services.AddScoped<IBacklogModuleApi, BacklogModuleApi>()` en `app/backend/src/Modules/Backlog/BacklogModule.cs`; verificar con `dotnet build app/backend/TechWorkHub.sln` que no hay referencia circular. Depende de T005, T012
- [X] T014 [P] Escribir `app/backend/tests/Integration/Sprints/SprintItemsMigrationTests.cs`: la migración crea `sprints."SprintItems"`; un `INSERT` SQL con `ItemId` repetido (incluso con otro `SprintId`) viola `UX_SprintItems_ItemId` (SQLSTATE 23505); un `SprintId` inexistente viola la FK; los schemas `backlog` y `application` no cambian. Depende de T011
- [ ] T015 [P] Escribir pruebas de integración del contrato real en `app/backend/tests/Integration/Sprints/BacklogModuleApiTests.cs`: `ExistsAsync` verdadero/falso; `GetSummariesAsync` devuelve solo ids existentes con `Title`, `Type` (texto), `DevPoints`, `QAPoints` en una sola consulta. Depende de T013, T017
- [X] T016 [P] Crear el doble escrito a mano `app/backend/tests/Unit/Sprints/FakeBacklogModuleApi.cs` (elementos configurables, contador de llamadas, opción de lanzar excepción) y, si hace falta, ajustar `app/backend/tests/Unit/Sprints/SprintsInMemoryDb.cs` para `SprintItems`. Depende de T005
- [X] T017 Ajustar `app/backend/tests/Integration/Sprints/SprintsApiFactory.cs` para registrar el `BacklogModuleApi` real y migrar también el schema `backlog` en el contenedor Testcontainers, de modo que las pruebas de integración puedan sembrar elementos de Backlog. Depende de T013

**Checkpoint**: Fundación lista - las historias pueden comenzar

---

## Phase 3: User Story 1 - Asignar un elemento a un Sprint (Priority: P1) 🎯 MVP

**Goal**: `POST /api/sprints/{sprintId}/items` asigna un elemento a un Sprint, responde 201 con `{ sprintId, itemId }` y `Location`, persiste con auditoría y responde 409 si el elemento ya está asignado (mismo u otro Sprint, también bajo concurrencia).

**Independent Test**: Con un Sprint y un elemento sin asignar, el POST devuelve 201, la fila queda con `CreatedBy` = `sub`, el elemento no cambia, un segundo elemento se asigna al mismo Sprint y reasignar el primero (al mismo u otro Sprint) devuelve 409 con una sola fila.

### Tests for User Story 1 (escribir primero; deben FALLAR)

- [X] T018 [P] [US1] Pruebas unitarias en `app/backend/tests/Unit/Sprints/AssignItemToSprintCommandHandlerTests.cs` (doble manual T016, EF in-memory): éxito devuelve `{ sprintId, itemId }` y persiste una fila con `CreatedBy`; `AnyAsync` previo detecta duplicado → `ConflictException`; un `DbUpdateException` cuyo `InnerException` es `PostgresException` con `SqlState = "23505"` y `ConstraintName = "UX_SprintItems_ItemId"` → `ConflictException`; otro `DbUpdateException` (otra restricción) se propaga sin traducir
- [X] T019 [P] [US1] Pruebas de integración en `app/backend/tests/Integration/Sprints/AssignItemToSprintTests.cs`: escenario 1 (201, cuerpo, `Location` hacia el GET, fila con `CreatedAt`/`CreatedBy` = `sub`), escenario 2 (el elemento de `backlog` conserva título, tipo, estimaciones y estado; el Sprint no cambia), escenario 3 (dos elementos distintos en el mismo Sprint), reasignación al mismo Sprint y a otro Sprint → 409 con el mismo mensaje y una sola fila, y concurrencia (N solicitudes simultáneas del mismo elemento a dos Sprints → exactamente un 201, el resto 409, una sola fila)

### Implementation for User Story 1

- [X] T020 [P] [US1] Crear `app/backend/src/Modules/Sprints/Features/SprintItems/AssignedItemResponse.cs`: `record AssignedItemResponse(Guid SprintId, Guid ItemId)`
- [X] T021 [P] [US1] Crear `app/backend/src/Modules/Sprints/Features/SprintItems/AssignItemToSprint/AssignItemToSprintCommand.cs`: `record AssignItemToSprintCommand(string? SprintId, string? ItemId) : IRequest<AssignedItemResponse>` (identificadores como texto, ADR-007)
- [X] T022 [US1] Crear `app/backend/src/Modules/Sprints/Features/SprintItems/AssignItemToSprint/AssignItemToSprintCommandHandler.cs` con este orden fijo: `ICurrentUser.UserId` (401 si falta) → parsear ids → `AnyAsync` del Sprint (`NotFoundException` "Sprint") → `IBacklogModuleApi.ExistsAsync` (`NotFoundException` "elemento", sin invocar el contrato si el Sprint no existe) → `AnyAsync` previo por `ItemId` (`ConflictException`, solo optimización) → `SprintItem.Create` + `Add` + un único `SaveChangesAsync(cancellationToken)`; capturar `DbUpdateException` con `PostgresException` `SqlState = "23505"` **y** `ConstraintName = SprintItemRules.ItemIdUniqueIndexName` → `ConflictException`; cualquier otro error se propaga (500). Depende de T004, T008, T009, T013, T021
- [X] T023 [US1] Crear `app/backend/src/Modules/Sprints/Features/SprintItems/AssignItemToSprint/AssignItemToSprintEndpoint.cs` (Carter `ICarterModule`): `POST /api/sprints/{sprintId}/items` con `sprintId` como `string` en la ruta, cuerpo `{ itemId }`, `.RequireAuthorization()`, respuesta `Results.Created($"/api/sprints/{sprintId}/items", response)` (201 PROPUESTO), `CancellationToken` propagado. Depende de T022
- [X] T024 [US1] Verificar que `app/backend/src/Modules/Sprints/SprintsModule.cs` descubre handler y validador (MediatR y `AddValidatorsFromAssembly` ya son por ensamblado; solo ajustar si hace falta) y ejecutar `dotnet test` de T018 y T019 hasta verde. Depende de T023

**Checkpoint**: US1 funcional y comprobable de forma independiente (MVP)

---

## Phase 4: User Story 3 - Rechazo de asignaciones inválidas (Priority: P1)

**Goal**: 400 con detalle por campo para `sprintId`/`itemId` ausente, malformado o `Guid.Empty`; 404 diferenciado para Sprint y elemento inexistentes; nunca se persiste nada.

**Independent Test**: Los 4 casos de 400, el 404 de Sprint, el 404 de elemento y el caso de ambos inexistentes (gana el 404 del Sprint) dejan `sprints."SprintItems"` vacía.

### Tests for User Story 3 (escribir primero; deben FALLAR)

- [X] T025 [P] [US3] Pruebas unitarias en `app/backend/tests/Unit/Sprints/AssignItemToSprintValidatorTests.cs`: `sprintId` e `itemId` nulos, vacíos, no-GUID y `Guid.Empty` generan error bajo la clave `sprintId` o `itemId`; ids válidos pasan
- [X] T026 [US3] Ampliar `app/backend/tests/Unit/Sprints/AssignItemToSprintCommandHandlerTests.cs` (mismo archivo que T018): Sprint inexistente → `NotFoundException` y el doble del contrato registra 0 llamadas; elemento inexistente → `NotFoundException` con mensaje de elemento; ambos inexistentes → mensaje de Sprint; sin escrituras en los tres casos. Depende de T018
- [X] T027 [P] [US3] Pruebas de integración en `app/backend/tests/Integration/Sprints/AssignItemToSprintValidationTests.cs`: 400 `application/problem+json` con `errors.sprintId` / `errors.itemId` para los 4 casos (ausente, malformado, `Guid.Empty`, cuerpo sin `itemId`), 404 Sprint, 404 elemento (el `detail` distingue el recurso) y tabla vacía en todos

### Implementation for User Story 3

- [X] T028 [US3] Crear `app/backend/src/Modules/Sprints/Features/SprintItems/AssignItemToSprint/AssignItemToSprintValidator.cs`: `AbstractValidator<AssignItemToSprintCommand>` con `NotEmpty` + `Guid.TryParse` + distinto de `Guid.Empty` para cada campo, usando `OverridePropertyName` y los mensajes de `SprintItemRules` para que las claves de error sean `sprintId` e `itemId`. Depende de T021
- [X] T029 [US3] Confirmar que `ValidationBehavior<,>` produce 400 con `errors` por campo a través de `CustomExceptionHandler` y que el handler (T022) lanza los 404 con los mensajes de `SprintItemRules`; ejecutar T025, T026 y T027 hasta verde. Depende de T022, T028

**Checkpoint**: US1 y US3 funcionan de forma independiente

---

## Phase 5: User Story 4 - Protección de acceso y resiliencia (Priority: P1)

**Goal**: 401 sin credenciales válidas para POST y GET sin leer ni escribir; 500 sin trazas ni fila parcial ante fallo de persistencia.

**Independent Test**: POST y GET sin token o con token inválido/expirado devuelven 401 con tabla intacta; un fallo de persistencia devuelve 500 ProblemDetails sin traza y sin fila.

### Tests for User Story 4 (escribir primero; deben FALLAR)

- [X] T030 [P] [US4] Pruebas de integración en `app/backend/tests/Integration/Sprints/SprintItemsAuthTests.cs`: POST y GET sin token y con token inválido/expirado → 401 sin lectura ni escritura (sin filas); regresión: 400, 401, 404 y 500 de HU-001/002/003 conservan su formato tras añadir el 409
- [X] T031 [P] [US4] Pruebas de integración en `app/backend/tests/Integration/Sprints/AssignItemToSprintFailureTests.cs`: forzar un fallo de persistencia (contexto o contrato que lanza) → 500 `application/problem+json` sin traza ni `StackTrace` en el cuerpo y sin fila en `sprints."SprintItems"`; un `DbUpdateException` de otra restricción distinta de `UX_SprintItems_ItemId` termina en 500, no en 409
- [X] T032 [US4] Ampliar `app/backend/tests/Unit/Sprints/AssignItemToSprintCommandHandlerTests.cs` (tras T026): `ICurrentUser.UserId` ausente → falla de identidad antes de consultar Sprint o contrato. Depende de T026

### Implementation for User Story 4

- [X] T033 [US4] Verificar que ambos endpoints llevan `.RequireAuthorization()` (T023 y T039) y que el handler resuelve la identidad antes de acceder a datos; corregir si T030–T032 fallan y ejecutarlas hasta verde. Depende de T023, T039

**Checkpoint**: US1, US3 y US4 completas

---

## Phase 6: User Story 2 - Consultar los elementos asignados (Priority: P2)

**Goal**: `GET /api/sprints/{sprintId}/items` devuelve exactamente los elementos asignados con `id, title, type, devPoints, qaPoints`; arreglo vacío si no hay; 404 si el Sprint no existe.

**Independent Test**: Un Sprint con dos elementos devuelve exactamente esos dos, uno sin elementos devuelve `[]`, uno inexistente devuelve 404, y 100 elementos responden en < 2 s.

### Tests for User Story 2 (escribir primero; deben FALLAR)

- [X] T034 [P] [US2] Pruebas unitarias en `app/backend/tests/Unit/Sprints/ListSprintItemsQueryHandlerTests.cs` (doble manual T016): devuelve exactamente los elementos asignados mapeados desde `BacklogItemSummary`; orden por `CreatedAt` y luego `Id`; Sprint sin elementos → lista vacía sin invocar `GetSummariesAsync`; Sprint inexistente → `NotFoundException`; el contrato se invoca una sola vez (sin N+1); un id que el contrato no devuelve se omite sin inventar título
- [X] T035 [P] [US2] Pruebas de integración en `app/backend/tests/Integration/Sprints/ListSprintItemsTests.cs`: escenarios 2, 3 y 4 del quickstart (200 con exactamente los elementos y campos esperados, sin `status` ni auditoría; 200 `[]`; 404 Sprint inexistente; `sprintId` no GUID → 404), datos del backlog intactos tras la consulta, y rendimiento SC-006 (100 elementos asignados, consulta < 2 s)

### Implementation for User Story 2

- [ ] T036 [P] [US2] Crear `app/backend/src/Modules/Sprints/Features/SprintItems/SprintItemResponse.cs`: `record SprintItemResponse(Guid Id, string Title, string Type, int DevPoints, int QAPoints)` (sin estado ni auditoría)
- [X] T037 [P] [US2] Crear `app/backend/src/Modules/Sprints/Features/SprintItems/ListSprintItems/ListSprintItemsQuery.cs`: `record ListSprintItemsQuery(Guid SprintId) : IRequest<IReadOnlyList<SprintItemResponse>>`
- [X] T038 [US2] Crear `app/backend/src/Modules/Sprints/Features/SprintItems/ListSprintItems/ListSprintItemsQueryHandler.cs`: `AnyAsync` del Sprint (`NotFoundException`) → `SprintItems.AsNoTracking()` filtrado por `SprintId` ordenado por `CreatedAt` y luego `Id` → una sola llamada `GetSummariesAsync` con los `ItemId` → proyección a `SprintItemResponse` preservando el orden; omitir con `LogWarning` los ids no devueltos; `CancellationToken` propagado. Depende de T009, T013, T036, T037
- [X] T039 [US2] Crear `app/backend/src/Modules/Sprints/Features/SprintItems/ListSprintItems/ListSprintItemsEndpoint.cs` (Carter): `GET /api/sprints/{sprintId:guid}/items`, `.RequireAuthorization()`, 200 con la lista. Depende de T038
- [X] T040 [US2] Ejecutar T034 y T035 hasta verde. Depende de T039

**Checkpoint**: Backend completo (las cuatro historias)

---

## Phase 7: Frontend (cubre US1–US4 en UI)

**Purpose**: Vista de elementos asignados y diálogo de asignación, según `documents/designer-ux/ux_004_asignacion_elementos_sprint.md` y R-10

- [ ] T041 [P] [US1] Ampliar `app/frontend/src/app/features/sprints/models/sprint.models.ts` con `SprintItem` (`id`, `title`, `type`, `devPoints`, `qaPoints`) y `AssignedItem` (`sprintId`, `itemId`)
- [X] T042 [US1] Escribir pruebas (deben fallar) en `app/frontend/src/app/features/sprints/services/sprint-api.service.spec.ts` para `assignItem(sprintId, itemId)` (`POST /api/sprints/{id}/items` con `{ itemId }`) y `listItems(sprintId)` (`GET`). Depende de T041
- [X] T043 [US1] Añadir `assignItem` y `listItems` en `app/frontend/src/app/features/sprints/services/sprint-api.service.ts`. Depende de T042
- [X] T044 [P] [US2] Escribir pruebas (deben fallar) en `app/frontend/src/app/features/sprints/components/sprint-assigned-items/sprint-assigned-items.component.spec.ts`: grilla con título, tipo, puntos Dev y QA; estado de carga; estado vacío; 404 de Sprint; error genérico con reintento; apertura del diálogo; nueva consulta al servidor tras el éxito (sin UI optimista); sin acciones de quitar, mover ni reasignar
- [X] T045 [US2] Crear `app/frontend/src/app/features/sprints/components/sprint-assigned-items/sprint-assigned-items.component.{ts,html,scss}`: standalone, `OnPush`, Signals, PrimeNG tema neutral, textos con i18n. Depende de T043, T044
- [X] T046 [P] [US1] Escribir pruebas (deben fallar) en `app/frontend/src/app/features/sprints/components/assign-item-dialog/assign-item-dialog.component.spec.ts`: el botón se deshabilita con `isSubmitting()`; 201 cierra el diálogo y emite el evento; 404 elemento, 409, 400 y 500 conservan el valor y muestran el error; 404 de Sprint bloquea el reintento; sin validación de negocio duplicada en cliente
- [X] T047 [US1] Crear `app/frontend/src/app/features/sprints/components/assign-item-dialog/assign-item-dialog.component.{ts,html,scss}` (standalone, `OnPush`, Signals, i18n). Depende de T043, T046
- [X] T048 [US2] Registrar la ruta `sprints/:id/elementos` en `app/frontend/src/app/app.routes.ts`, dentro del bloque `sprints` (hereda `authGuard`) y declarada ANTES de `sprints/:id`. Depende de T045
- [X] T049 [US2] Añadir solo el botón `Elementos asignados` en `app/frontend/src/app/features/sprints/components/sprint-detail/sprint-detail.component.html` (y `.ts` si hace falta el `routerLink`) y ampliar `sprint-detail.component.spec.ts`; los cuatro datos del Sprint no cambian. Depende de T048

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Verificación final y consistencia

- [X] T050 [P] Ejecutar `dotnet test app/backend/TechWorkHub.sln` y confirmar que las suites de HU-001, HU-002 y HU-003 pasan sin modificaciones
- [ ] T051 [P] Ejecutar `npm test` y `npm run build` en `app/frontend`
- [ ] T052 Recorrer `specs/004-HU_asignacion_elementos_sprint/quickstart.md` (escenarios 1–10 y validación del frontend) contra la API y la SPA en ejecución
- [X] T053 [P] Confirmar con `git diff --stat` que no se modificaron `Sprint`, `SprintRules`, `InitialSprintsSchema`, `BacklogItem`, `BacklogDbContext`, `Modules/Application`, `core/auth` ni `features/backlog` (FR-013, FR-014)
- [X] T054 Revisar que ningún `catch` ni mensaje de error exponga trazas, el Sprint dueño del elemento en el 409, ni secretos (FR-012)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sin dependencias
- **Foundational (Phase 2)**: depende de Setup; BLOQUEA todas las historias
- **US1 (Phase 3)**: depende de Foundational; es el MVP
- **US3 (Phase 4) y US4 (Phase 5)**: dependen de US1 (comparten endpoint y handler); T033 también depende del endpoint GET (T039)
- **US2 (Phase 6)**: depende de Foundational; puede ir en paralelo con US1 (otros archivos), aunque sus pruebas de integración siembran filas por SQL directo o por el POST
- **Frontend (Phase 7)**: T041–T043 dependen solo del contrato HTTP ya diseñado; la validación visual requiere el backend
- **Polish (Phase 8)**: depende de todo lo anterior

### Within Each User Story

- Pruebas primero y en rojo; después comandos/consultas → handler → endpoint
- Las tareas que tocan el mismo archivo de pruebas (T018, T026, T032) se ejecutan en secuencia

### Parallel Opportunities

- Fundación: T003, T005, T006, T007 en paralelo; luego T012 y T016; T014 y T015 al final
- US1: T018 y T019 en paralelo; T020 y T021 en paralelo
- US3: T025 y T027 en paralelo
- US2 (T034–T037) puede avanzar en paralelo con US1
- Frontend: T041, T044 y T046 en paralelo

---

## Parallel Example: User Story 1

```text
# Pruebas de US1 juntas:
Task: "Pruebas unitarias del handler en app/backend/tests/Unit/Sprints/AssignItemToSprintCommandHandlerTests.cs"
Task: "Pruebas de integración en app/backend/tests/Integration/Sprints/AssignItemToSprintTests.cs"

# Tipos de US1 juntos:
Task: "AssignedItemResponse en app/backend/src/Modules/Sprints/Features/SprintItems/AssignedItemResponse.cs"
Task: "AssignItemToSprintCommand en app/backend/src/Modules/Sprints/Features/SprintItems/AssignItemToSprint/AssignItemToSprintCommand.cs"
```

---

## Implementation Strategy

### MVP First (US1)

1. Phase 1 y Phase 2 (excepción 409, contrato, dominio, migración)
2. Phase 3: US1 completa
3. **DETENER y VALIDAR**: escenarios 1, 3, 8 y 9 del quickstart
4. Añadir US3 y US4 (misma superficie), después US2 y el frontend

### Incremental Delivery

1. Fundación → US1 (asignar + 409) → US3 (400/404) → US4 (401/500) → US2 (consulta) → Frontend → Polish
2. Cada historia se prueba de forma independiente sin romper las anteriores

---

## Notes

- [P] = archivos distintos, sin dependencias
- La etiqueta [Story] mapea cada tarea a su historia para trazabilidad
- Verificar que las pruebas fallan antes de implementar
- Hacer commit tras cada tarea o grupo lógico
- Evitar: tareas vagas, conflictos en el mismo archivo y dependencias entre historias que rompan su independencia

---

## Phase 9: Convergence (retrabajo iteración 1/2 — DEF-01 y DEF-02 del QA Automation)

**Propósito**: cerrar los defectos del informe `documents/qa-auto/qa-report.md`. Reabiertas por no cumplirse: T005, T015, T036 y T041 (tipo `int` en lugar de `decimal?`). T051 y T052 siguen abiertas (bloqueo de entorno: Node v22.20.0 frente a Angular CLI ≥ 22.22.3; no es defecto de código). `spec.md`, `plan.md`, `data-model.md` y los contratos ya fueron reconciliados (FR-017, FR-018, retiro de FR-015, `decimal?`).

- [X] T055 [fix:TASKS:DEF-01] [servidor] Cambiar `BacklogItemSummary` en `app/backend/src/Modules/Sprints/Contracts/IBacklogModuleApi.cs` a `decimal? DevPoints, decimal? QAPoints` per FR-018 (partial)
- [X] T056 [fix:TASKS:DEF-01] [servidor] Eliminar `ToWholePoints` de `app/backend/src/Modules/Backlog/BacklogModuleApi.cs` y proyectar `DevPoints`/`QAPoints` como `decimal?` sin redondeo ni conversión de `null` a 0 per FR-018, W-01 (contradicts)
- [X] T057 [fix:TASKS:DEF-01] [servidor] Cambiar `SprintItemResponse` a `decimal? DevPoints, decimal? QAPoints`, ajustar el mapeo del handler de consulta y las pruebas que asumen `int`, y revalidar `SprintItemsEstimationFidelityTests` (2 pruebas rojas), la suite Sprints y la regresión Backlog per FR-008, FR-018 (partial)
- [X] T058 [fix:TASKS:DEF-01] [servidor] Ampliar `app/backend/tests/Integration/Sprints/BacklogModuleApiTests.cs` con un elemento de estimación 2.5 y otro con QA nulo, verificando que `GetSummariesAsync` devuelve 2.5 y `null` per FR-018 (partial)
- [X] T059 [fix:TASKS:DEF-01] [interfaz] Declarar `devPoints: number | null` y `qaPoints: number | null` en `SprintItem` de `app/frontend/src/app/features/sprints/models/sprint.models.ts` y ajustar `sprint-api.service.ts` y sus specs per FR-018 (partial)
- [X] T060 [fix:TASKS:DEF-01] [interfaz] Mostrar un guion (`—`) para `devPoints`/`qaPoints` nulos en `sprint-detail.component.html` y cubrirlo en `sprint-detail.component.spec.ts` (Jest) per FR-018 (partial)
- [X] T061 [fix:SPEC:DEF-02] [servidor] Alinear las referencias de trazabilidad de las pruebas del 409 y la concurrencia (`AssignItemToSprint*Tests`, `MigrationsPostgresTests`) con FR-017 y los escenarios 4 y 5 de US3, retirando citas a FR-015 o a "no documentado" per FR-017 (partial)
- [X] T062 [fix:SPEC:DEF-02] [servidor] Actualizar `quickstart.md` y la matriz de cobertura para mapear el 409 a FR-017 y la fidelidad de estimaciones a FR-018, y volver a ejecutar `/speckit-analyze` para confirmar 0 contradicciones per FR-015 reemplazado (partial)
