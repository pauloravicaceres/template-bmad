# Implementation Plan: Relación entre Personas, Roles y Elementos de Trabajo

**Branch**: `feat/015-HU_relacion_personas_roles_elementos` | **Date**: 2026-10-04 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/015-HU_relacion_personas_roles_elementos/spec.md`

## Summary

Se añade al módulo existente `Teams` (schema `teams`, sin módulo nuevo) la relación Persona–Elemento: asignar un miembro como responsable de un elemento del backlog (`POST /api/backlog-items/{itemId}/assignees`, un miembro por solicitud) y consultarla en ambos sentidos (`GET /api/backlog-items/{itemId}/assignees` y `GET /api/team-members/{memberId}/items`). La tabla `teams."ItemAssignments"` tiene FK local a `TeamMembers` y referencia **solo lógica** al elemento; la existencia y los datos del elemento se obtienen por el contrato in-process de solo lectura `Teams.Contracts.IBacklogItemLookup`, que implementa `Backlog`. El rol no se almacena: se lee del rol técnico vigente del miembro (FR-005). La unicidad del par (elemento, miembro) la garantiza el índice único `UX_ItemAssignments_ItemId_MemberId`; la asignación duplicada es **idempotente** (200 con la relación existente; 201 al crear), según la resolución humana B recogida en el diseño del SA. Orden determinista del caso de uso Asignar: validador 400 → identidad 401 → miembro 404 → elemento 404 → par existente ⇒ 200 → único `SaveChangesAsync` ⇒ 201. Se añade además la consulta aditiva `GET /api/backlog-items` en `Backlog` para el selector del UX (ADR-006). Sin eventos, Outbox, caché ni paquetes nuevos. Las decisiones provienen de `documents/solutions-architect/015-HU_relacion_personas_roles_elementos.md` (ADR-001..008) y el UX de `documents/designer-ux/ux_015_relacion_personas_roles_elementos.md`.

## Technical Context

**Language/Version**: C# 12 / .NET 8 (`net8.0`) en backend; TypeScript con Angular 22.2 Zoneless + Signals en frontend

**Primary Dependencies**: Carter 8.1.0, MediatR 12.4.1, FluentValidation 11.9.2, Mapster 7.4.0, EF Core Npgsql 8.0.11, Keycloak.AuthServices.Authentication 2.5.2, Serilog; PrimeNG ^22.1.2 (tema neutral). Sin paquetes nuevos.

**Storage**: PostgreSQL, schema existente `teams`, tabla nueva `teams."ItemAssignments"`, Code-First con migración `AddItemAssignments` (solo crea objetos en `teams`)

**Testing**: xUnit + FluentAssertions + Testcontainers PostgreSQL (backend); Jest (frontend). TDD, sin pruebas tautológicas; doble escrito a mano para `IBacklogItemLookup` en unitarias

**Target Platform**: Docker Linux (API) + navegador (SPA)

**Project Type**: web-service (Modulith) + web-app (SPA)

**Performance Goals**: sin objetivo cuantitativo en la spec (SC-007 exige exactitud, no volumen); consultas con `AsNoTracking()`, proyección a DTO y una única llamada de lote al contrato (sin N+1)

**Constraints**: sin RabbitMQ/MassTransit/Redis/Outbox (ADR-007); sin FKs ni consultas hacia el schema `backlog` ni referencia a `BacklogDbContext` desde `Teams`; `CancellationToken` propagado hasta EF Core y el contrato; 500 sin trazas; `BacklogItem` y `TeamMember` no se modifican (FR-013); no se imponen quitar/reemplazar, máximo de responsables, coherencia rol/estimaciones ni restricciones por estado o Sprint (FR-015 restante)

**Scale/Scope**: 4 endpoints (3 de la HU + 1 aditivo de Backlog), 1 entidad nueva, 1 contrato in-process, 3 componentes de UI, 2 rutas

No quedan elementos `NEEDS CLARIFICATION`: los vacíos de la spec se resuelven en [research.md](./research.md) con las decisiones del SA y la resolución humana B.

## Constitution Check

*GATE: pasa antes de Phase 0 y se re-evalúa tras Phase 1.*

| Regla de la constitución | Cumplimiento | Estado |
|---|---|---|
| Idioma español en todos los artefactos | Todos los artefactos en español | ✅ |
| Vertical Slice + co-locación Endpoint/Command/Validator/Handler | `Features/ItemAssignments/{AssignMemberToItem,ListItemAssignees,ListMemberItems}/` y `Backlog/Features/BacklogItems/ListBacklogItems/` | ✅ |
| Carter (`ICarterModule`), sin `[ApiController]` | Un endpoint Carter por caso de uso | ✅ |
| MediatR + `ValidationBehavior` + FluentValidation | `AssignMemberToItemCommand` + `AbstractValidator` | ✅ |
| Mapster, sin AutoMapper | Proyección a DTO / `Adapt<T>()` | ✅ |
| Schema propio por módulo y `DbContext` independiente | Se reutiliza `teams` / `TeamsDbContext` | ✅ |
| Sin joins ni queries cross-schema | JOIN solo local (`ItemAssignments`↔`TeamMembers`↔`TechnicalRoles`); el elemento se lee por contrato in-process, sin FK al schema `backlog` | ✅ |
| Comunicación síncrona entre módulos por interfaz pública | `IBacklogItemLookup` (Teams) implementado por `BacklogItemLookup` (Backlog) | ✅ |
| Jerarquía `Aggregate<TId>` e interceptores de `Shared` | `ItemAssignment : Aggregate<Guid>, IAuditableEntity`; `AuditableEntityInterceptor` rellena `CreatedAt`/`CreatedBy` desde el `sub` | ✅ |
| Outbox solo para eventos críticos | Sin eventos (ADR-007) | ✅ (N/A) |
| `.RequireAuthorization()` en todos los endpoints | Los cuatro endpoints | ✅ |
| `CustomExceptionHandler` centralizado | Se reutiliza 400/401/404/500; sin cambios en `Shared` (el 409 no se usa: el duplicado es idempotente) | ✅ |
| `CancellationToken` en toda E/S de producción | Endpoints, handlers, consultas y contrato | ✅ |
| Rutas físicas con prefijo `app/backend/` o `app/frontend/` | Ver Project Structure | ✅ |
| Frontend: Angular 22 Zoneless + Signals + i18n + PrimeNG tema neutral | Componentes standalone OnPush | ✅ |
| Vertical Slicing estricto | Solo HU-015 | ✅ |

**Resultado**: sin violaciones. Re-evaluación posterior al diseño (Phase 1): sin cambios; el modelo no añade columnas ni navegaciones a `TeamMember` ni a `BacklogItem`, no requiere cambios en `Shared` y la única referencia de proyecto nueva (`Backlog` → `Teams`) va en el sentido contrato→implementador, igual que `Backlog` → `Sprints` en HU-004.

## Project Structure

### Documentation (this feature)

```text
specs/015-HU_relacion_personas_roles_elementos/
├── plan.md              # Este archivo
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/
│   └── item-assignments-api.openapi.yaml   # Phase 1 (HTTP)
├── checklists/requirements.md
└── tasks.md             # Phase 2 (/speckit-tasks, no lo crea este comando)
```

### Source Code (repository root)

```text
app/backend/
├── src/
│   └── Modules/
│       ├── Teams/
│       │   ├── Contracts/IBacklogItemLookup.cs                 # ExistsAsync, GetItemsAsync, BacklogItemRef(Id, Title, Type)
│       │   ├── Domain/ItemAssignments/
│       │   │   ├── ItemAssignment.cs                           # Aggregate<Guid>, IAuditableEntity, Create(itemId, memberId)
│       │   │   └── ItemAssignmentRules.cs                      # campos, mensajes, nombre del índice único
│       │   ├── Data/
│       │   │   ├── ITeamsDbContext.cs                          # + DbSet<ItemAssignment> ItemAssignments
│       │   │   ├── TeamsDbContext.cs                           # + DbSet
│       │   │   ├── Configurations/ItemAssignmentConfiguration.cs   # FK local + UX_ItemAssignments_ItemId_MemberId + IX_ItemAssignments_MemberId
│       │   │   └── Migrations/                                 # AddItemAssignments
│       │   └── Features/ItemAssignments/
│       │       ├── AssignMemberToItem/    AssignMemberToItemCommand.cs · AssignMemberToItemValidator.cs · AssignMemberToItemCommandHandler.cs · AssignMemberToItemEndpoint.cs
│       │       ├── ListItemAssignees/     ListItemAssigneesQuery.cs · ListItemAssigneesQueryHandler.cs · ListItemAssigneesEndpoint.cs
│       │       ├── ListMemberItems/       ListMemberItemsQuery.cs · ListMemberItemsQueryHandler.cs · ListMemberItemsEndpoint.cs
│       │       ├── ItemAssigneeResponse.cs                     # { itemId, memberId, memberName, role }
│       │       ├── AssigneeResponse.cs                         # { id, name, role }
│       │       └── MemberItemResponse.cs                       # { id, title, type }
│       └── Backlog/
│           ├── Backlog.csproj                                  # + ProjectReference a Teams
│           ├── BacklogModule.cs                                # + AddScoped<IBacklogItemLookup, BacklogItemLookup>
│           ├── BacklogItemLookup.cs                            # solo lee el schema backlog
│           └── Features/BacklogItems/ListBacklogItems/         # ListBacklogItemsQuery.cs · ...QueryHandler.cs · ...Endpoint.cs · BacklogItemSummaryResponse.cs
└── tests/
    ├── Unit/Teams/          # validador, handlers (con doble de IBacklogItemLookup), ItemAssignment.Create
    ├── Unit/Backlog/        # ListBacklogItemsQueryHandler
    ├── Integration/Teams/   # Testcontainers: 201/200/400/401/404/500, concurrencia, migración, FR-013
    └── Integration/Backlog/ # GET /api/backlog-items y no regresión de POST

app/frontend/src/app/
├── app.routes.ts                                  # + equipos/responsables y equipos/responsables/miembro (hijas del bloque equipos)
└── features/teams/
    ├── components/
    │   ├── team-page/                             # + pestaña Responsables
    │   ├── item-assignees-view/                   # Estados 1, 2, 5, 6, 7
    │   ├── member-items-view/                     # Estado 3
    │   └── assign-assignee-dialog/                # Estados 4, 8, 9, 10, 12
    ├── services/team-api.service.ts               # + assignMember, listItemAssignees, listMemberItems, listBacklogItems
    └── models/team.models.ts
```

**Structure Decision**: Web application (backend Modulith + frontend SPA). Se extienden el módulo `Teams` y la feature `features/teams` existentes. Cambios permitidos fuera de ellos, y solo estos: `Backlog.csproj`, `BacklogModule.cs`, `BacklogItemLookup.cs`, la feature aditiva `ListBacklogItems` y `app.routes.ts`. No se tocan `Modules/Application`, `Modules/Sprints`, `BuildingBlocks/Shared`, `core/auth`, `features/backlog`, `features/sprints`, ni `BacklogItem`, `BacklogDbContext`, configuraciones y migraciones de Backlog, ni `TeamMember`/`TechnicalRole` y la migración `InitialTeamsSchema`.

## Complexity Tracking

Sin violaciones de la constitución que justificar. Costos aceptados y registrados en los ADR del SA: acoplamiento de compilación `Backlog` → `Teams` y dependencia en ejecución del registro de `BacklogItemLookup` (ADR-003); integridad del `ItemId` por verificación vía contrato y no por FK (ADR-002); dependencia del nombre del constraint de Npgsql para distinguir la carrera de un 500 (ADR-004); cliente que lee el código HTTP 201/200 (ADR-005); nueva superficie pública `GET /api/backlog-items` sin paginación en HU-001 (ADR-006); parseo manual de identificadores en el POST (ADR-008).
