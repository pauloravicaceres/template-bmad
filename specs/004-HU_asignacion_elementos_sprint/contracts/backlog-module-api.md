# Contrato in-process: `Sprints.Contracts.IBacklogModuleApi`

Interfaz de solo lectura definida en `app/backend/src/Modules/Sprints/Contracts/IBacklogModuleApi.cs` e implementada por `app/backend/src/Modules/Backlog/BacklogModuleApi.cs`. No se expone por HTTP. Mismo patrón que `IApplicationModuleApi` (el implementador referencia al módulo que define el contrato). Registro: `services.AddScoped<IBacklogModuleApi, BacklogModuleApi>()` en `BacklogModule.cs`.

## Operaciones

| Operación | Firma | Semántica |
|---|---|---|
| `ExistsAsync` | `Task<bool> ExistsAsync(Guid itemId, CancellationToken cancellationToken)` | `true` si existe un elemento con ese id en el schema `backlog` |
| `GetSummariesAsync` | `Task<IReadOnlyList<BacklogItemSummary>> GetSummariesAsync(IReadOnlyCollection<Guid> itemIds, CancellationToken cancellationToken)` | Una sola consulta de lote (`WHERE Id = ANY(...)`); omite los ids inexistentes; sin orden garantizado |

## Tipo de transferencia

```text
BacklogItemSummary(Guid Id, string Title, string Type, decimal? DevPoints, decimal? QAPoints)
```

- `DevPoints` y `QAPoints` conservan el tipo de `BacklogItem` (`decimal?`): sin redondeo y sin convertir `null` a 0 (FR-018, W-01 del Tech Design).

- `Type` es el nombre del enum de `Backlog` como `string`, para que `Sprints` no referencie tipos de `Backlog`.
- No incluye descripción, criterios de aceptación ni estado (la consulta no los necesita; FR-008, FR-014).

## Reglas
- Solo lectura: ninguna operación modifica el schema `backlog`.
- `Backlog` consulta únicamente su propio schema; `Sprints` nunca referencia `BacklogDbContext`.
- Propaga `CancellationToken` hasta EF Core.
- Un fallo lanza excepción (resultado 500); no hay fallback que dé por existente un elemento no verificado.
- Pruebas: doble escrito a mano en unitarias de `Sprints`; implementación real en integración.
