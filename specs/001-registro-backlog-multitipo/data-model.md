# Modelo de Datos: Backlog Multitipo

Este documento define las entidades y reglas de validación según las especificaciones funcionales (FR-002 a FR-013) y los lineamientos de la arquitectura (Lex Superior de la Constitución). Codificación del archivo: UTF-8.

## Entidades (Domain Driven Design)

### `BacklogItem` (Aggregate Root)

Hereda de `Aggregate<Guid>` (definido en `BuildingBlocks/Shared`) e implementa `IAuditableEntity` para que `AuditableEntityInterceptor` asigne los metadatos de auditoría.

Tabla física: `backlog."BacklogItems"` (schema `backlog`, minúscula).

| Campo | Tipo C# | Columna PostgreSQL | Restricciones / Reglas |
|-------|---------|--------------------|------------------------|
| `Id` | `Guid` | `uuid` (PK) | Identificador único principal. |
| `Title` | `string` | `varchar(200)` NOT NULL | Requerido. No vacío. Máximo 200 caracteres (FR-004). |
| `Description` | `string?` | `varchar(4000)` | Opcional. Máximo 4000 caracteres (FR-012). |
| `Type` | `BacklogItemType` | `varchar(50)` NOT NULL | Enum persistido como texto (UserStory, Bug, TechEvolution, TechRequirement, TechDebt, Research, Spike) (FR-005). |
| `Priority` | `BacklogItemPriority` | `varchar(50)` NOT NULL | Enum persistido como texto (Low, Medium, High, Critical) (FR-011). |
| `AcceptanceCriteria` | `string?` | `varchar(4000)` | Opcional. Máximo 4000 caracteres (FR-012). |
| `Status` | `BacklogItemStatus` | `varchar(50)` NOT NULL | Inmutable en creación a `Backlog` (FR-003). |
| `DevPoints` | `decimal?` | `numeric(18,2)` | Opcional. Debe ser `>= 0` si existe (FR-006). |
| `QAPoints` | `decimal?` | `numeric(18,2)` | Opcional. Debe ser `>= 0` si existe. Debe ser nulo para ítems técnicos (FR-008). |
| `ApplicationId` | `Guid?` | `uuid` | Opcional. Clave foránea lógica hacia el módulo de Aplicaciones (FR-007); sin FK ni joins cross-schema. |
| `CreatedAt` | `DateTime` | `timestamp with time zone` NOT NULL | Gestionado vía `AuditableEntityInterceptor` (FR-009). |
| `CreatedBy` | `string` | `varchar(255)` NOT NULL | Gestionado vía `AuditableEntityInterceptor` a través del claim `sub` del JWT (FR-009). |
| `LastModified` | `DateTime?` | `timestamp with time zone` | Gestionado vía `AuditableEntityInterceptor`. |
| `LastModifiedBy` | `string?` | `varchar(255)` | Gestionado vía `AuditableEntityInterceptor`. |

Tipo único de puntos: `decimal?` en comando, entidad y columna (`numeric(18,2)`); la HU usa valores como `5.0`.

### Invariantes del agregado

- **FR-008:** `BacklogItem.Create` rechaza (`BadRequestException`, HTTP 400, clave `QAPoints`) un `qaPoints` con valor cuando el tipo es técnico. La lista de tipos técnicos (`TechEvolution`, `TechRequirement`, `TechDebt`, `Research`, `Spike`) se define una sola vez en `BacklogItemTypeExtensions.IsTechnical`.
- **FR-003:** el estado inicial es siempre `Backlog`.

### Reglas de Validación Asociadas (FluentValidation)

- **Creación de Command (`CreateBacklogItemCommand`)**:
  - `Title`: `NotEmpty().MaximumLength(200)`
  - `Description`: `MaximumLength(4000)`
  - `AcceptanceCriteria`: `MaximumLength(4000)`
  - `Type`: `NotEmpty()` e `IsEnumName(typeof(BacklogItemType), caseSensitive: false)`
  - `Priority`: `IsInEnum()`
  - `DevPoints`: `GreaterThanOrEqualTo(0).When(x => x.DevPoints.HasValue)`
  - `QAPoints`: `GreaterThanOrEqualTo(0).When(x => x.QAPoints.HasValue)`
  - `ApplicationId`: si tiene valor, el handler verifica asincrónicamente su existencia consultando el módulo Application (`IApplicationModuleApi.ExistsAsync(applicationId, cancellationToken)`). Si no existe, lanza `ValidationException` con la clave `ApplicationId`, mapeada a HTTP 400 `ProblemDetails` con `errors`.
- El pipeline de MediatR ejecuta `ValidationBehavior<,>` (de `Shared`) antes del handler.

### Eventos de Dominio

- `BacklogItemCreatedDomainEvent` (`IDomainEvent`)
  - Atributos: `BacklogItemId`, `Type`, `ApplicationId`, `OccurredOnUtc`
  - Comportamiento: registrado en la entidad vía `AddDomainEvent()` al crearla, y publicado por `DispatchDomainEventsInterceptor` antes de confirmar la transacción en base de datos.

### `RegisteredApplication` (módulo Application)

Tabla `application."Applications"` (`Id` uuid PK, `Name` varchar(200) NOT NULL). Solo la consulta `IApplicationModuleApi.ExistsAsync`; el módulo Backlog nunca la lee directamente.
