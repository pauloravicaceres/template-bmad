# Implementation Plan: Gestión de Sprint de Dos Semanas (Crear y Consultar)

**Branch**: `feat/003-HU_gestion_sprint_dos_semanas` | **Date**: 2026-10-04 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-HU_gestion_sprint_dos_semanas/spec.md`

## Summary

Se añade el módulo `Sprints` al Modulith .NET 8 (schema PostgreSQL `sprints`, `SprintsDbContext` propio) con tres casos de uso en Vertical Slice: crear Sprint (`POST /api/sprints`), listar (`GET /api/sprints`) y detalle (`GET /api/sprints/{id}`). La regla de negocio central es la ventana de 2 semanas (14 días calendario inclusivos, `fin = inicio + 13`), con fuente única `SprintRules.WindowDays` y aplicada en tres capas: validador FluentValidation (400 por campo), dominio (`Sprint.Create`) y restricción `CHECK` en BD. El frontend Angular 22 Zoneless entrega tres páginas (`sprint-form`, `sprint-list`, `sprint-detail`). El Sprint no tiene estado, ni relación con tarjetas, ni unicidad, ni paginación (FR-013, FR-014). Las decisiones técnicas provienen de `documents/solutions-architect/003-HU_gestion_sprint_dos_semanas.md` (ADR-001..007).

## Technical Context

**Language/Version**: C# 12 / .NET 8 (`net8.0`) en backend; TypeScript con Angular 22.2 Zoneless + Signals en frontend

**Primary Dependencies**: Carter 8.1.0, MediatR 12.4.1, FluentValidation 11.9.2, Mapster 7.4.0, EF Core Npgsql 8.0.11, Keycloak.AuthServices.Authentication 2.5.2, Serilog; PrimeNG ^22.1.2 (tema neutral)

**Storage**: PostgreSQL, schema `sprints`, tabla `sprints."Sprints"`, Code-First con migración `InitialSprintsSchema`

**Testing**: xUnit + FluentAssertions + Testcontainers PostgreSQL (backend); Jest (frontend). TDD, sin pruebas tautológicas

**Target Platform**: Docker Linux (API) + navegador (SPA)

**Project Type**: web-service (Modulith) + web-app (SPA)

**Performance Goals**: listado y detalle < 2 s con hasta 100 Sprints (SC-005)

**Constraints**: sin RabbitMQ/MassTransit/Redis/Outbox (ADR-007); sin consultas cross-schema; `CancellationToken` propagado hasta EF Core; 500 sin trazas internas

**Scale/Scope**: 3 endpoints, 1 entidad, 3 pantallas, ~100 Sprints

No quedan elementos `NEEDS CLARIFICATION`: los puntos abiertos 1, 3–9 de la HU se resuelven como supuestos documentados o quedan fuera de alcance (ver [research.md](./research.md)).

## Constitution Check

*GATE: pasa antes de Phase 0 y se re-evalúa tras Phase 1.*

| Regla de la constitución | Cumplimiento | Estado |
|---|---|---|
| Idioma español en todos los artefactos | Todos los artefactos en español | ✅ |
| Vertical Slice + co-locación Endpoint/Command/Validator/Handler | Carpetas `Features/Sprints/{CreateSprint,ListSprints,GetSprintById}/` | ✅ |
| Carter (`ICarterModule`), sin `[ApiController]` | Un endpoint Carter por caso de uso | ✅ |
| MediatR + `ValidationBehavior` + FluentValidation | Command/Query + `AbstractValidator<CreateSprintCommand>` | ✅ |
| Mapster, sin AutoMapper | `Adapt<T>()` y proyección a DTO | ✅ |
| Schema PostgreSQL propio por módulo y `DbContext` independiente | `sprints` / `SprintsDbContext` | ✅ |
| Sin joins ni queries cross-schema | Sin FK ni navegación hacia `backlog`/`application` | ✅ |
| Entidades de la jerarquía `Aggregate<TId>`, interceptores de `Shared` | `Sprint : Aggregate<Guid>`, `AuditableEntityInterceptor` rellena `CreatedAt`/`CreatedBy` | ✅ |
| Outbox solo para eventos críticos | No se publican eventos (ADR-007) | ✅ (N/A) |
| `.RequireAuthorization()` en todos los endpoints | Los tres endpoints | ✅ |
| `CustomExceptionHandler` centralizado (400/404/500) | `ValidationException`, `BadRequestException`, `NotFoundException` | ✅ |
| `CancellationToken` en toda E/S de producción | Endpoints, handlers y consultas | ✅ |
| Rutas físicas con prefijo `app/backend/` o `app/frontend/` | Ver Project Structure | ✅ |
| Frontend: Angular 22 Zoneless + Signals + i18n + PrimeNG tema neutral | Componentes standalone OnPush | ✅ |
| Vertical Slicing estricto (no abrir otra HU en paralelo) | Solo HU-003 | ✅ |

**Resultado**: sin violaciones; la sección Complexity Tracking queda vacía. Re-evaluación posterior al diseño (Phase 1): sin cambios, el modelo y los contratos no introducen estado, relaciones cross-schema ni infraestructura nueva.

## Project Structure

### Documentation (this feature)

```text
specs/003-HU_gestion_sprint_dos_semanas/
├── plan.md              # Este archivo
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/
│   └── sprints-api.openapi.yaml   # Phase 1
├── checklists/requirements.md
└── tasks.md             # Phase 2 (/speckit-tasks, no lo crea este comando)
```

### Source Code (repository root)

```text
app/backend/
├── TechWorkHub.sln                                   # añade Sprints, Sprints.UnitTests, Sprints.IntegrationTests
├── src/
│   ├── Bootstrapper/Api/
│   │   ├── Api.csproj                                # + ProjectReference a Sprints
│   │   └── Program.cs                                # + AddSprintsModule / MigrateSprintsModuleAsync
│   └── Modules/Sprints/
│       ├── Sprints.csproj
│       ├── SprintsModule.cs                          # AddSprintsModule() y MigrateSprintsModuleAsync()
│       ├── Domain/Sprints/
│       │   ├── Sprint.cs                             # Aggregate<Guid>, IAuditableEntity, Sprint.Create(...)
│       │   └── SprintRules.cs                        # WindowDays=14, IdentificationMaxLength=100, DateFormat, mensajes
│       ├── Data/
│       │   ├── ISprintsDbContext.cs
│       │   ├── SprintsDbContext.cs                   # HasDefaultSchema("sprints")
│       │   ├── SprintsDbContextFactory.cs            # design-time
│       │   ├── Configurations/SprintConfiguration.cs # CK_Sprints_Window
│       │   └── Migrations/                           # InitialSprintsSchema
│       └── Features/Sprints/
│           ├── CreateSprint/   CreateSprintCommand.cs · CreateSprintValidator.cs · CreateSprintCommandHandler.cs · CreateSprintEndpoint.cs
│           ├── ListSprints/    ListSprintsQuery.cs · ListSprintsQueryHandler.cs · ListSprintsEndpoint.cs
│           └── GetSprintById/  GetSprintByIdQuery.cs · GetSprintByIdQueryHandler.cs · GetSprintByIdEndpoint.cs
└── tests/
    ├── Unit/Sprints/          # Sprints.UnitTests (Sprint.Create, SprintRules, validador, handler)
    └── Integration/Sprints/   # Sprints.IntegrationTests (Testcontainers, CHECK, 401/404/500, rendimiento)

app/frontend/src/app/
├── app.routes.ts                                     # + rutas lazy /sprints, /sprints/nuevo, /sprints/:id
└── features/sprints/
    ├── components/            # sprint-form · sprint-list · sprint-detail (+ *.spec.ts)
    ├── services/sprint-api.service.ts
    └── models/sprint.models.ts
```

**Structure Decision**: Web application (backend Modulith + frontend SPA) con módulo nuevo `Sprints` en el patrón de `Modules/Backlog`. Cambios permitidos fuera del módulo: `Api.csproj`, `Program.cs`, `TechWorkHub.sln` y `app.routes.ts`. No se tocan `Modules/Backlog`, `Modules/Application`, `BuildingBlocks/Shared`, `core/auth` ni `features/backlog`.

## Complexity Tracking

Sin violaciones de la constitución que justificar.
