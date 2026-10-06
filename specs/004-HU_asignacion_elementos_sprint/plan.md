# Implementation Plan: Asignación de Elementos del Backlog a un Sprint

**Branch**: `feat/004-HU_asignacion_elementos_sprint` | **Date**: 2026-10-04 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/004-HU_asignacion_elementos_sprint/spec.md`

## Summary

Se extiende el módulo existente `Sprints` (schema PostgreSQL `sprints`, `SprintsDbContext`) con la relación Sprint–Elemento: asignar un elemento del backlog a un Sprint (`POST /api/sprints/{sprintId}/items`, un elemento por solicitud) y consultar los elementos asignados (`GET /api/sprints/{sprintId}/items`). No se crea un módulo nuevo. La existencia y los datos del elemento se obtienen por el contrato in-process `Sprints.Contracts.IBacklogModuleApi`, implementado por `Backlog` (sin FK ni consultas cross-schema). El orden de evaluación es determinista: validador 400 → identidad 401 → Sprint 404 → elemento 404 → conflicto 409 → un único `SaveChangesAsync`. Las decisiones provienen de `documents/solutions-architect/004-HU_asignacion_elementos_sprint.md` (ADR-001..007).

**Reconciliación spec ↔ SA (lex humana, opción A, tracker 04-10-2026 10:32)**: la guía del SA fija que un elemento pertenece a **un solo Sprint** y que repetir la asignación (al mismo Sprint o a otro) responde **409 Conflict**, garantizado por el índice único `UX_SprintItems_ItemId`. Esto reemplaza al FR-015 y a los casos borde "no documentado" de `spec.md`; `spec.md` ya fue reconciliado en el retrabajo (FR-017, escenarios 4 y 5 de US3, retiro de FR-015). Las estimaciones por rol del contrato y de la respuesta son `decimal?` (FR-018, W-01), sin redondeo ni `null` a 0. Las tareas cubren el 409 y la concurrencia.

## Technical Context

**Language/Version**: C# 12 / .NET 8 (`net8.0`) en backend; TypeScript con Angular 22.2 Zoneless + Signals en frontend

**Primary Dependencies**: Carter 8.1.0, MediatR 12.4.1, FluentValidation 11.9.2, Mapster 7.4.0, EF Core Npgsql 8.0.11, Keycloak.AuthServices.Authentication 2.5.2, Serilog; PrimeNG ^22.1.2 (tema neutral). Sin paquetes nuevos.

**Storage**: PostgreSQL, schema `sprints`, tabla nueva `sprints."SprintItems"`, Code-First con migración `AddSprintItems`

**Testing**: xUnit + FluentAssertions + Testcontainers PostgreSQL (backend); Jest (frontend). TDD, sin pruebas tautológicas; doble escrito a mano del contrato en unitarias

**Target Platform**: Docker Linux (API) + navegador (SPA)

**Project Type**: web-service (Modulith) + web-app (SPA)

**Performance Goals**: consulta < 2 s con hasta 100 elementos asignados (SC-006): una consulta por clave + una llamada de lote al contrato (`WHERE Id = ANY(...)`)

**Constraints**: sin RabbitMQ/MassTransit/Redis/Outbox (ADR-006); sin FKs ni consultas cross-schema; `CancellationToken` propagado hasta EF Core y el contrato; 500 sin trazas; no modificar `Sprint` ni `BacklogItem` (FR-013, FR-014)

**Scale/Scope**: 2 endpoints, 1 entidad nueva, 1 contrato in-process, 2 componentes de UI, 1 ruta

No quedan elementos `NEEDS CLARIFICATION`: los puntos abiertos 1–7 de la HU quedan fuera de alcance o resueltos por la decisión humana A (ver [research.md](./research.md)).

## Constitution Check

*GATE: pasa antes de Phase 0 y se re-evalúa tras Phase 1.*

| Regla de la constitución | Cumplimiento | Estado |
|---|---|---|
| Idioma español en todos los artefactos | Todos los artefactos en español | ✅ |
| Vertical Slice + co-locación Endpoint/Command/Validator/Handler | `Features/SprintItems/{AssignItemToSprint,ListSprintItems}/` | ✅ |
| Carter (`ICarterModule`), sin `[ApiController]` | Un endpoint Carter por caso de uso | ✅ |
| MediatR + `ValidationBehavior` + FluentValidation | `AssignItemToSprintCommand` + `AbstractValidator` | ✅ |
| Mapster, sin AutoMapper | `Adapt<T>()` / proyección a DTO | ✅ |
| Schema propio por módulo y `DbContext` independiente | Se reutiliza `sprints` / `SprintsDbContext` | ✅ |
| Sin joins ni queries cross-schema | `ItemId` sin FK; datos del elemento por `IBacklogModuleApi` in-process | ✅ |
| Jerarquía `Aggregate<TId>` e interceptores de `Shared` | `SprintItem : Aggregate<Guid>`; `AuditableEntityInterceptor` rellena `CreatedAt`/`CreatedBy` | ✅ |
| Outbox solo para eventos críticos | Sin eventos (ADR-006) | ✅ (N/A) |
| `.RequireAuthorization()` en todos los endpoints | Ambos endpoints | ✅ |
| `CustomExceptionHandler` centralizado | Se añade `ConflictException` → 409 (aditivo, ADR-005) | ✅ |
| `CancellationToken` en toda E/S de producción | Endpoints, handlers, consultas y contrato | ✅ |
| Rutas físicas con prefijo `app/backend/` o `app/frontend/` | Ver Project Structure | ✅ |
| Frontend: Angular 22 Zoneless + Signals + i18n + PrimeNG tema neutral | Componentes standalone OnPush | ✅ |
| Vertical Slicing estricto | Solo HU-004 | ✅ |

**Resultado**: sin violaciones. Se documentan dos cambios fuera del módulo `Sprints` autorizados por el SA (§2): `ConflictException` en `Shared` y la referencia `Backlog → Sprints` para implementar el contrato (mismo sentido que `Application → Backlog`). Re-evaluación posterior al diseño (Phase 1): sin cambios; el modelo no añade columnas a `Sprint` ni `BacklogItem` ni infraestructura nueva.

## Project Structure

### Documentation (this feature)

```text
specs/004-HU_asignacion_elementos_sprint/
├── plan.md              # Este archivo
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/
│   ├── sprint-items-api.openapi.yaml   # Phase 1 (HTTP)
│   └── backlog-module-api.md           # Phase 1 (contrato in-process)
├── checklists/requirements.md
└── tasks.md             # Phase 2 (/speckit-tasks, no lo crea este comando)
```

### Source Code (repository root)

```text
app/backend/
├── src/
│   ├── BuildingBlocks/Shared/Exceptions/
│   │   ├── ConflictException.cs                      # nuevo (aditivo)
│   │   └── CustomExceptionHandler.cs                 # + rama 409
│   └── Modules/
│       ├── Sprints/
│       │   ├── Contracts/IBacklogModuleApi.cs        # ExistsAsync, GetSummariesAsync, BacklogItemSummary
│       │   ├── Domain/SprintItems/
│       │   │   ├── SprintItem.cs                     # Aggregate<Guid>, IAuditableEntity, SprintItem.Create(sprintId, itemId)
│       │   │   └── SprintItemRules.cs                # campos, mensajes, ItemIdUniqueIndexName
│       │   ├── Data/
│       │   │   ├── ISprintsDbContext.cs              # + DbSet<SprintItem> SprintItems
│       │   │   ├── SprintsDbContext.cs               # + DbSet (schema "sprints")
│       │   │   ├── Configurations/SprintItemConfiguration.cs  # FK a Sprints + UX_SprintItems_ItemId + IX_SprintItems_SprintId
│       │   │   └── Migrations/                       # AddSprintItems
│       │   └── Features/SprintItems/
│       │       ├── AssignItemToSprint/   AssignItemToSprintCommand.cs · AssignItemToSprintValidator.cs · AssignItemToSprintCommandHandler.cs · AssignItemToSprintEndpoint.cs
│       │       ├── ListSprintItems/      ListSprintItemsQuery.cs · ListSprintItemsQueryHandler.cs · ListSprintItemsEndpoint.cs
│       │       ├── SprintItemResponse.cs             # { id, title, type, devPoints, qaPoints }
│       │       └── AssignedItemResponse.cs           # { sprintId, itemId }
│       └── Backlog/
│           ├── Backlog.csproj                        # + ProjectReference a Sprints
│           ├── BacklogModule.cs                      # + AddScoped<IBacklogModuleApi, BacklogModuleApi>()
│           └── BacklogModuleApi.cs                   # solo lee el schema backlog
└── tests/
    ├── Unit/Sprints/          # validador, handlers, SprintItem.Create (doble manual del contrato)
    └── Integration/Sprints/   # Testcontainers: 201/400/401/404/409/500, concurrencia, migración, rendimiento

app/frontend/src/app/
├── app.routes.ts                                     # + ruta sprints/:id/elementos (antes de :id)
└── features/sprints/
    ├── components/
    │   ├── sprint-assigned-items/    # grilla y estados 1, 2, 4, 5, 9, 10, variante B del 8
    │   ├── assign-item-dialog/       # estados 3, 6, 7, 8A, 10, 11, 12
    │   └── sprint-detail/            # solo botón "Elementos asignados" (UX D-02)
    ├── services/sprint-api.service.ts    # + assignItem, listItems
    └── models/sprint.models.ts
```

**Structure Decision**: Web application (backend Modulith + frontend SPA) ampliando el módulo existente `Sprints` y la feature `features/sprints`. Cambios permitidos fuera del módulo, y solo estos: `Backlog.csproj` + `BacklogModule.cs` + `BacklogModuleApi.cs`, `Shared/Exceptions` (409), `app.routes.ts` y el botón del detalle de HU-003. No se tocan `Modules/Application`, la entidad `Sprint`, `SprintRules`, la migración `InitialSprintsSchema`, `BacklogItem`/`BacklogDbContext`, `core/auth` ni `features/backlog`.

## Complexity Tracking

Sin violaciones de la constitución que justificar. Costos aceptados y registrados en los ADR del SA: acoplamiento de compilación `Backlog → Sprints` (ADR-003), dependencia del nombre del índice único para distinguir 409 de 500 (ADR-004) y cambio aditivo en un building block compartido (ADR-005).
