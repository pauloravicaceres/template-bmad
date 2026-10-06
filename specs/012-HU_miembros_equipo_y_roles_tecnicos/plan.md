# Implementation Plan: Miembros del Equipo y Roles Técnicos

**Branch**: `feat/012-HU_miembros_equipo_y_roles_tecnicos` | **Date**: 2026-10-04 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/012-HU_miembros_equipo_y_roles_tecnicos/spec.md`

## Summary

Se crea el módulo nuevo `Teams` (schema PostgreSQL `teams`, `TeamsDbContext` propio) con los datos maestros de personas y roles: registrar un miembro del equipo con un rol técnico (`POST /api/team-members`), consultar los miembros (`GET /api/team-members`) y consultar el catálogo de roles técnicos (`GET /api/technical-roles`). El catálogo (`Desarrollo`, `QA`) se siembra en la migración `InitialTeamsSchema` con identificadores fijos, sin alta ni edición de roles. El rol se envía por **nombre** y el servidor lo resuelve contra el catálogo (400 si no existe). Miembros y roles viven en el mismo schema, por lo que la FK `TeamMembers.TechnicalRoleId → TechnicalRoles.Id` es real y no hay contrato in-process ni consultas cross-schema. Orden de evaluación determinista del registro: validador 400 → identidad 401 → rol existe 400 → un único `SaveChangesAsync`. Sin eventos, Outbox, caché ni paquetes nuevos. Las decisiones provienen de `documents/solutions-architect/012-HU_miembros_equipo_y_roles_tecnicos.md` (ADR-001..007) y el diseño de pantallas de `documents/designer-ux/ux_012_miembros_equipo_y_roles_tecnicos.md`.

## Technical Context

**Language/Version**: C# 12 / .NET 8 (`net8.0`) en backend; TypeScript con Angular 22.2 Zoneless + Signals en frontend

**Primary Dependencies**: Carter 8.1.0, MediatR 12.4.1, FluentValidation 11.9.2, Mapster 7.4.0, EF Core Npgsql 8.0.11, Keycloak.AuthServices.Authentication 2.5.2, Serilog; PrimeNG ^22.1.2 (tema neutral). Sin paquetes nuevos.

**Storage**: PostgreSQL, schema nuevo `teams`, tablas `teams."TechnicalRoles"` y `teams."TeamMembers"`, Code-First con migración `InitialTeamsSchema` (incluye semilla de dos roles)

**Testing**: xUnit + FluentAssertions + Testcontainers PostgreSQL (backend); Jest (frontend). TDD, sin pruebas tautológicas; la BD en memoria solo en unitarias

**Target Platform**: Docker Linux (API) + navegador (SPA)

**Project Type**: web-service (Modulith) + web-app (SPA)

**Performance Goals**: consultas de miembros y de roles < 2 s con hasta 100 miembros (SC-007): una consulta con `JOIN` local, `AsNoTracking()` y proyección a DTO

**Constraints**: sin RabbitMQ/MassTransit/Redis/Outbox (ADR-006); sin FKs ni consultas hacia otros schemas; `CancellationToken` propagado hasta EF Core; 500 sin trazas; no modificar Backlog, Sprints ni Application (FR-014); no imponer cardinalidad, unicidad ni ciclo de vida (FR-015); el nombre del miembro no se escribe en logs

**Scale/Scope**: 3 endpoints, 2 entidades, 1 módulo nuevo, 2 componentes de UI, 2 rutas

No quedan elementos `NEEDS CLARIFICATION`: los puntos abiertos 1–8 de la HU quedan fuera de alcance (ver [research.md](./research.md)).

## Constitution Check

*GATE: pasa antes de Phase 0 y se re-evalúa tras Phase 1.*

| Regla de la constitución | Cumplimiento | Estado |
|---|---|---|
| Idioma español en todos los artefactos | Todos los artefactos en español | ✅ |
| Vertical Slice + co-locación Endpoint/Command/Validator/Handler | `Features/TeamMembers/{RegisterTeamMember,ListTeamMembers}/` y `Features/TechnicalRoles/ListTechnicalRoles/` | ✅ |
| Carter (`ICarterModule`), sin `[ApiController]` | Un endpoint Carter por caso de uso | ✅ |
| MediatR + `ValidationBehavior` + FluentValidation | `RegisterTeamMemberCommand` + `AbstractValidator` | ✅ |
| Mapster, sin AutoMapper | Proyección a DTO / `Adapt<T>()` | ✅ |
| Schema propio por módulo y `DbContext` independiente | `teams` / `TeamsDbContext` | ✅ |
| Sin joins ni queries cross-schema | Solo tablas de `teams`; FK local | ✅ |
| Jerarquía `Aggregate<TId>` e interceptores de `Shared` | `TeamMember : Aggregate<Guid>, IAuditableEntity`; `AuditableEntityInterceptor` rellena `CreatedAt`/`CreatedBy` | ✅ |
| Outbox solo para eventos críticos | Sin eventos (ADR-006) | ✅ (N/A) |
| `.RequireAuthorization()` en todos los endpoints | Los tres endpoints | ✅ |
| `CustomExceptionHandler` centralizado | Se reutiliza 400/401/500; sin cambios en `Shared` | ✅ |
| `CancellationToken` en toda E/S de producción | Endpoints, handlers y consultas | ✅ |
| Rutas físicas con prefijo `app/backend/` o `app/frontend/` | Ver Project Structure | ✅ |
| Frontend: Angular 22 Zoneless + Signals + i18n + PrimeNG tema neutral | Componentes standalone OnPush | ✅ |
| Vertical Slicing estricto | Solo HU-012 | ✅ |

**Resultado**: sin violaciones. Re-evaluación posterior al diseño (Phase 1): sin cambios; el modelo no añade columnas ni FKs a entidades existentes y no requiere cambios en `Shared`. Nota de implementación: `Shared` no ofrece `Entity<TId>`; `TechnicalRole` hereda de `Aggregate<Guid>` sin `IAuditableEntity`, de modo que no tiene columnas de auditoría y la semilla no necesita fecha ni usuario (resuelve la reserva del SA §9).

## Project Structure

### Documentation (this feature)

```text
specs/012-HU_miembros_equipo_y_roles_tecnicos/
├── plan.md              # Este archivo
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/
│   └── teams-api.openapi.yaml   # Phase 1 (HTTP)
├── checklists/requirements.md
└── tasks.md             # Phase 2 (/speckit-tasks, no lo crea este comando)
```

### Source Code (repository root)

```text
app/backend/
├── TechWorkHub.sln                                       # + Teams, Teams.UnitTests, Teams.IntegrationTests
├── src/
│   ├── Bootstrapper/Api/
│   │   ├── Api.csproj                                    # + ProjectReference a Teams
│   │   └── Program.cs                                    # + AddTeamsModule y MigrateTeamsModuleAsync
│   └── Modules/Teams/
│       ├── Teams.csproj                                  # mismas referencias que Sprints.csproj
│       ├── TeamsModule.cs                                # AddTeamsModule / MigrateTeamsModuleAsync
│       ├── Domain/
│       │   ├── TeamMembers/TeamMember.cs                 # Aggregate<Guid>, IAuditableEntity, Create(name, technicalRoleId)
│       │   ├── TeamMembers/TeamMemberRules.cs            # campos y mensajes
│       │   └── TechnicalRoles/
│       │       ├── TechnicalRole.cs                      # Aggregate<Guid> (Id, Name), sin factoría de alta
│       │       └── TechnicalRoleSeed.cs                  # GUID fijos y nombres de "Desarrollo" y "QA"
│       ├── Data/
│       │   ├── ITeamsDbContext.cs
│       │   ├── TeamsDbContext.cs                         # schema "teams"
│       │   ├── TeamsDbContextFactory.cs
│       │   ├── Configurations/TeamMemberConfiguration.cs
│       │   ├── Configurations/TechnicalRoleConfiguration.cs   # UX_TechnicalRoles_Name + HasData
│       │   └── Migrations/                               # InitialTeamsSchema
│       └── Features/
│           ├── TeamMembers/
│           │   ├── RegisterTeamMember/   RegisterTeamMemberCommand.cs · RegisterTeamMemberValidator.cs · RegisterTeamMemberCommandHandler.cs · RegisterTeamMemberEndpoint.cs
│           │   ├── ListTeamMembers/      ListTeamMembersQuery.cs · ListTeamMembersQueryHandler.cs · ListTeamMembersEndpoint.cs
│           │   └── TeamMemberResponse.cs                 # { id, name, role }
│           └── TechnicalRoles/
│               ├── ListTechnicalRoles/   ListTechnicalRolesQuery.cs · ListTechnicalRolesQueryHandler.cs · ListTechnicalRolesEndpoint.cs
│               └── TechnicalRoleResponse.cs              # { id, name }
└── tests/
    ├── Unit/Teams/          # Teams.UnitTests: validador, handlers, TeamMember.Create
    └── Integration/Teams/   # Teams.IntegrationTests: Testcontainers (201/400/401/500, migración, no regresión, rendimiento)

app/frontend/src/app/
├── app.routes.ts                                         # + bloque equipos (equipos, equipos/roles)
└── features/teams/
    ├── components/
    │   ├── team-page/                # p-tabs, grilla de miembros y de roles, botón de registro, error de lectura
    │   └── register-member-dialog/   # diálogo del registro (estados 4 a 10 del UX)
    ├── services/team-api.service.ts  # listMembers, listRoles, registerMember
    └── models/team.models.ts
```

**Structure Decision**: Web application (backend Modulith + frontend SPA) con un módulo backend nuevo `Teams` y una feature frontend nueva `features/teams`. Cambios permitidos fuera de `Modules/Teams` y de `features/teams`, y solo estos: `Api.csproj`, `Program.cs`, `TechWorkHub.sln` y `app.routes.ts`. No se tocan `Modules/Backlog`, `Modules/Application`, `Modules/Sprints`, `BuildingBlocks/Shared`, `core/auth`, `features/backlog` ni `features/sprints`.

## Complexity Tracking

Sin violaciones de la constitución que justificar. Costos aceptados y registrados en los ADR del SA: un módulo más que registrar por un modelo pequeño (ADR-003), catálogo que solo cambia con una migración nueva (ADR-004), contrato por nombre de rol que obligaría a versionar la API si se permite renombrar (ADR-005) y nombre sin límite de longitud ni unicidad (ADR-007).
