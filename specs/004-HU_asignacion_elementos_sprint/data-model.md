# Data Model: Asignación de Elementos del Backlog a un Sprint

Schema PostgreSQL `sprints`, `SprintsDbContext` existente. La migración `AddSprintItems` **solo crea** la tabla nueva; no toca `backlog`, `application` ni la tabla `sprints."Sprints"`.

## Entidad nueva: SprintItem (`sprints."SprintItems"`)

`SprintItem : Aggregate<Guid>`, `IAuditableEntity`. Sin eventos de dominio (ADR-006).

| Campo | Tipo C# | Columna | Reglas |
|---|---|---|---|
| `Id` | `Guid` | `uuid` PK | Generado en `SprintItem.Create` |
| `SprintId` | `Guid` | `uuid NOT NULL` | **FK** a `sprints."Sprints"("Id")`, `ON DELETE RESTRICT` |
| `ItemId` | `Guid` | `uuid NOT NULL` | **Sin FK** (el elemento vive en el schema `backlog`); existencia verificada por `IBacklogModuleApi` |
| `CreatedAt` | `DateTime` | `timestamptz NOT NULL` | `AuditableEntityInterceptor` (FR-003) |
| `CreatedBy` | `string` | `varchar NOT NULL` | `sub` del token vía interceptor; nunca del cuerpo |
| `LastModified` / `LastModifiedBy` | `DateTime?` / `string?` | `timestamptz` / `varchar` NULL | Gestionadas por el interceptor |

Sin columnas de estado ni de orden.

### Índices
- `UX_SprintItems_ItemId` — **único** sobre `ItemId` (invariante "un elemento, un Sprint"; ADR-004). El nombre es constante pública `SprintItemRules.ItemIdUniqueIndexName`.
- `IX_SprintItems_SprintId` — no único, para la consulta por Sprint.

### Factoría y reglas de dominio
- `SprintItem.Create(Guid sprintId, Guid itemId)`: rechaza `Guid.Empty` en cualquiera de los dos (`BadRequestException`) como defensa en profundidad; el validador ya lo cubre en el borde.
- `SprintItemRules`: nombres de campo (`sprintId`, `itemId`), mensajes (Sprint no encontrado, elemento no encontrado, conflicto, formato inválido) y `ItemIdUniqueIndexName`.

## Entidades preexistentes (no se modifican)
- **Sprint** (HU-003, `sprints."Sprints"`): sin columnas ni navegaciones nuevas.
- **BacklogItem** (HU-001, `backlog`): sin columnas nuevas; se lee solo vía contrato.

## Proyección de lectura (no persistida)
`BacklogItemSummary(Guid Id, string Title, string Type, decimal? DevPoints, decimal? QAPoints)` (sin redondeo ni `null` a 0; FR-018) — definida en `Sprints.Contracts`; ver [contracts/backlog-module-api.md](./contracts/backlog-module-api.md). Los datos del elemento no se duplican ni se proyectan localmente (ADR-003).

## Relaciones y cardinalidad
- `Sprint 1 — N SprintItem` (FK real, `RESTRICT`).
- `BacklogItem 1 — 0..1 SprintItem` (relación lógica; un elemento en un solo Sprint por el índice único).

## Transiciones de estado
Ninguna: la asignación no define ni cambia el estado del elemento ni del Sprint (FR-014). No existe desasignar ni mover (fuera de alcance).

## Escritura: secuencia y atomicidad
Una asignación es **una fila** con un único `SaveChangesAsync`; no existe estado parcial (SC-007, FR-012). Orden: validador → identidad → Sprint existe → elemento existe (contrato) → `AnyAsync` opcional por `ItemId` → `Add` + `SaveChangesAsync`. La violación `23505` de `UX_SprintItems_ItemId` se traduce a `ConflictException` (409); cualquier otro `DbUpdateException` se propaga (500).
