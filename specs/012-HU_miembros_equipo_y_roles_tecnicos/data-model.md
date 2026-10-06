# Data Model: Miembros del Equipo y Roles Técnicos

Schema PostgreSQL nuevo `teams`, `TeamsDbContext` propio. La migración `InitialTeamsSchema` **solo crea** objetos en `teams` (incluida su tabla `__EFMigrationsHistory`, como los otros módulos); no toca `backlog`, `application` ni `sprints`.

## Entidad nueva: TechnicalRole (`teams."TechnicalRoles"`)

`TechnicalRole : Aggregate<Guid>`. Sin `IAuditableEntity` (sin columnas de auditoría; ver R-04) y sin eventos de dominio (ADR-006). Sin factoría pública de alta: los roles se crean solo por la semilla de la migración.

| Campo | Tipo C# | Columna | Reglas |
|---|---|---|---|
| `Id` | `Guid` | `uuid` PK | GUID fijo de la semilla (`TechnicalRoleSeed`) |
| `Name` | `string` | `text NOT NULL` | Único: `UX_TechnicalRoles_Name` |

### Semilla (`HasData` → `InsertData` en `InitialTeamsSchema`)
| Rol | Id | Fuente |
|---|---|---|
| Desarrollo | GUID constante `TechnicalRoleSeed.DevelopmentId` | FR-004 |
| QA | GUID constante `TechnicalRoleSeed.QaId` | FR-004 |

Los GUID quedan en el historial de migraciones y no pueden cambiarse sin migrar datos. Añadir un rol exige una migración nueva (ADR-004).

## Entidad nueva: TeamMember (`teams."TeamMembers"`)

`TeamMember : Aggregate<Guid>`, `IAuditableEntity`. Sin eventos de dominio (ADR-006).

| Campo | Tipo C# | Columna | Reglas |
|---|---|---|---|
| `Id` | `Guid` | `uuid` PK | Generado en `TeamMember.Create` |
| `Name` | `string` | `text NOT NULL` | Recortado (`Trim`); sin límite de longitud ni unicidad (ADR-007) |
| `TechnicalRoleId` | `Guid` | `uuid NOT NULL` | **FK** a `teams."TechnicalRoles"("Id")`, `ON DELETE RESTRICT` |
| `CreatedAt` | `DateTime` | `timestamptz NOT NULL` | `AuditableEntityInterceptor` (FR-003) |
| `CreatedBy` | `string` | `text NOT NULL` | `sub` del token vía interceptor; nunca del cuerpo |
| `LastModified` / `LastModifiedBy` | `DateTime?` / `string?` | `timestamptz` / `text` NULL | Gestionadas por el interceptor |

Sin columnas de estado, correo, usuario de acceso ni más de un rol (FR-010, FR-015).

### Índices
- `IX_TeamMembers_TechnicalRoleId` — no único, para la FK y el `JOIN` de la consulta.
- Sin índice único sobre `Name` (ADR-007).

### Factoría y reglas de dominio
- `TeamMember.Create(string name, Guid technicalRoleId)`: rechaza nombre vacío o de solo espacios y `Guid.Empty` (`BadRequestException`) como defensa en profundidad; el validador ya lo cubre en el borde. Guarda `name.Trim()`.
- `TeamMemberRules`: nombres de campo (`name`, `role`), mensajes (nombre requerido, rol requerido, `InvalidRoleMessage` = "El rol indicado no es válido.").

## Entidades preexistentes (no se modifican)
- **BacklogItem** (HU-001), **Sprint** (HU-003) y **SprintItem** (HU-004): sin columnas, FKs ni navegaciones nuevas. Las estimaciones por rol Dev y QA del backlog permanecen independientes del catálogo (FR-014).

## Proyecciones de lectura (no persistidas)
- `TeamMemberResponse(Guid Id, string Name, string Role)`: `Role` es el nombre del rol (JOIN local).
- `TechnicalRoleResponse(Guid Id, string Name)`.
- Ninguna incluye `CreatedAt`/`CreatedBy` ni estado (UX D-09).

## Relaciones y cardinalidad
- `TechnicalRole 1 — N TeamMember` (FK real, `RESTRICT`). Cada miembro referencia exactamente un rol en esta HU; la cardinalidad futura no se impone en el modelo (FR-015).

## Transiciones de estado
Ninguna: el miembro no define estado ni ciclo de vida. No existe modificar, desactivar ni eliminar.

## Escritura: secuencia y atomicidad
Un registro es **una fila** con un único `SaveChangesAsync`; no existe estado parcial (SC-008, FR-013). Orden: validador → identidad → rol por nombre (si no existe, 400) → `Add` + `SaveChangesAsync`. Cualquier fallo de persistencia se propaga (500) sin fila.
