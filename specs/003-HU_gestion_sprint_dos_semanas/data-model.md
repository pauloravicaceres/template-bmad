# Data Model: Gestión de Sprint de Dos Semanas

## Entidad: Sprint

Agregado `Sprint : Aggregate<Guid>` que implementa `IAuditableEntity` (módulo `Sprints`, schema `sprints`, tabla `sprints."Sprints"`).

| Campo | Tipo .NET | Columna PostgreSQL | Reglas |
|---|---|---|---|
| `Id` | `Guid` | `uuid` PK | Generado por el servidor (FR-002) |
| `Identification` | `string` | `varchar(100)` NOT NULL | Obligatoria, no vacía; máximo `SprintRules.IdentificationMaxLength` (⚠️ técnico); texto libre (FR-005) |
| `StartDate` | `DateOnly` | `date` NOT NULL | Obligatoria; formato `yyyy-MM-dd` en la entrada (FR-005) |
| `EndDate` | `DateOnly` | `date` NOT NULL | Obligatoria; `EndDate = StartDate + 13 días` (FR-003, FR-004) |
| `CreatedAt` | `DateTime` | `timestamptz` NOT NULL | Lo asigna `AuditableEntityInterceptor` (FR-006) |
| `CreatedBy` | `string` | `varchar` NOT NULL | `sub` del token vía `ICurrentUser`; nunca del cuerpo (FR-006) |
| `LastModified` | `DateTime?` | `timestamptz` NULL | Interceptor; sin uso en esta HU |
| `LastModifiedBy` | `string?` | `varchar` NULL | Interceptor; sin uso en esta HU |

### Restricciones
- `CK_Sprints_Window`: `("EndDate" - "StartDate") = 13` (FR-015, SC-003). El valor sale de `SprintRules.WindowDays - 1`.
- Sin índice único sobre `Identification` (ADR-006).
- Sin FK ni navegación hacia `backlog` o `application` (FR-013, constitución §3).
- Sin columnas de estado, apertura o cierre (FR-014).

### Validación (por capa)
1. **`CreateSprintValidator`** (400 por campo): identificación vacía o > 100; `StartDate`/`EndDate` ausentes o con formato distinto de `yyyy-MM-dd`; fin ≤ inicio (mensaje FR-004); ventana ≠ 14 días (mensaje "el Sprint debe abarcar exactamente una ventana de 2 semanas"). Los errores de ventana caen sobre `EndDate`.
2. **`Sprint.Create(identification, startDate, endDate)`**: repite la invariante y lanza `BadRequestException`.
3. **BD**: `CK_Sprints_Window`.

### Transiciones de estado
No aplica: el Sprint es inmutable tras su creación en esta HU (sin modificación, cancelación ni eliminación; FR-014).

### Relaciones
Ninguna. La asignación de tarjetas es alcance de la HU-004, que resolverá la referencia lógica mediante contrato in-process (`ISprintModuleApi`, no creado aquí).

## Migración
`InitialSprintsSchema` en `app/backend/src/Modules/Sprints/Data/Migrations/`; historial en `sprints.__EFMigrationsHistory`. Solo toca el schema `sprints`.

## DTOs

| DTO | Campos |
|---|---|
| `CreateSprintRequest` / `CreateSprintCommand` | `identification: string?`, `startDate: string?`, `endDate: string?` |
| `SprintResponse` | `id: Guid`, `identification: string`, `startDate: DateOnly (yyyy-MM-dd)`, `endDate: DateOnly (yyyy-MM-dd)` |
| `ListSprintsResponse` | arreglo de `SprintResponse` |
