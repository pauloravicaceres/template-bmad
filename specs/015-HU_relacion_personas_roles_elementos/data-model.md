# Data Model: Relación entre Personas, Roles y Elementos de Trabajo

Módulo `Teams`, schema `teams`, `TeamsDbContext` existente. La migración `AddItemAssignments` solo **crea** la tabla nueva; no toca `backlog`, `sprints` ni `application`, ni las tablas `TeamMembers` y `TechnicalRoles`.

## Entidad nueva: `ItemAssignment` (Relación de responsabilidad)

`ItemAssignment : Aggregate<Guid>, IAuditableEntity`. Se crea con `ItemAssignment.Create(itemId, memberId)`; no emite eventos de dominio (ADR-007).

| Campo | Tipo (PostgreSQL) | Restricciones | Origen |
|---|---|---|---|
| `Id` | `uuid` | PK | generado en `Create` |
| `ItemId` | `uuid` | NOT NULL, **sin FK** (el elemento está en el schema `backlog`) | solicitud, verificado por `IBacklogItemLookup` |
| `MemberId` | `uuid` | NOT NULL, **FK** → `teams."TeamMembers"("Id")` `ON DELETE RESTRICT` | solicitud, verificado en `teams` |
| `CreatedAt` | `timestamptz` | NOT NULL | `AuditableEntityInterceptor` (FR-004) |
| `CreatedBy` | `varchar` | NOT NULL | `sub` del token vía interceptor, nunca del cuerpo (FR-004) |
| `LastModified` | `timestamptz` | NULL | interceptor |
| `LastModifiedBy` | `varchar` | NULL | interceptor |

Sin columnas de rol, estado ni orden (el rol se deriva del miembro, FR-005).

### Índices
| Nombre | Columnas | Tipo | Propósito |
|---|---|---|---|
| `UX_ItemAssignments_ItemId_MemberId` | `(ItemId, MemberId)` | único | invariante de unicidad del par (ADR-004); sirve también la consulta por `ItemId` (prefijo) |
| `IX_ItemAssignments_MemberId` | `(MemberId)` | no único | consulta de elementos de un miembro |

El nombre del índice único es la constante `ItemAssignmentRules.PairUniqueIndexName`; el handler lo usa para distinguir la carrera (`PostgresException` `SqlState=23505` **y** `ConstraintName` igual) de cualquier otro fallo, que termina en 500.

## Entidades existentes (solo lectura, sin cambios)

- **`TeamMember`** (HU-012): `Id`, `Name`, `TechnicalRoleId` → rol técnico. Aporta `memberName` y `role` mediante JOIN local con `TechnicalRoles`.
- **`TechnicalRole`** (HU-012): `Id`, `Name` (`Desarrollo`, `QA`).
- **`BacklogItem`** (HU-001, schema `backlog`): no accesible desde `Teams`; solo se ve a través de `BacklogItemRef`.

## Contrato in-process

```text
Teams.Contracts.IBacklogItemLookup
  Task<bool> ExistsAsync(Guid itemId, CancellationToken ct)
  Task<IReadOnlyCollection<BacklogItemRef>> GetItemsAsync(IReadOnlyCollection<Guid> itemIds, CancellationToken ct)

BacklogItemRef(Guid Id, string Title, string Type)   // Type = nombre del enum, como string
```
Implementado por `Backlog.BacklogItemLookup` (consulta solo el schema `backlog`, `AsNoTracking`, solo lectura). No devuelve estimaciones, estado, Sprint, descripción ni criterios de aceptación.

## Reglas de validación (del comando Asignar)

| Campo | Regla | Error (clave) |
|---|---|---|
| `itemId` (ruta, `string`) | presente, `Guid.TryParse`, ≠ `Guid.Empty` | `itemId` (FR-010) |
| `memberId` (cuerpo, `string?`) | presente, `Guid.TryParse`, ≠ `Guid.Empty` | `memberId` (FR-010) |

Reglas del handler (tras el validador): identidad presente (si no, 401) → miembro existe (si no, 404 "miembro") → elemento existe (si no, 404 "elemento") → par ya existe (200, sin escribir) → insertar y un único `SaveChangesAsync` (201).

## Transiciones y consistencia

No hay ciclo de vida: la relación solo se **crea** (no se quita ni reemplaza; fuera de alcance). La asignación es una sola fila y un único `SaveChangesAsync`: no existe estado parcial (SC-006). La concurrencia del mismo par se resuelve por el índice único: exactamente una solicitud inserta (201) y las demás releen y responden 200.

## Invariantes (FR-013)
`BacklogItem` (`devPoints`, `qaPoints`, estado, Sprint) y `TeamMember`/`TechnicalRole` no cambian tras ninguna operación de esta HU; no se añaden columnas ni navegaciones a ellos.
