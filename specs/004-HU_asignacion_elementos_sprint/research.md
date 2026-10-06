# Research: Asignación de Elementos del Backlog a un Sprint

Las decisiones provienen de `documents/solutions-architect/004-HU_asignacion_elementos_sprint.md` y de la constitución; aquí se consolidan. No quedaban `NEEDS CLARIFICATION`.

## R-01: Ubicación de la asignación
- **Decisión**: Tabla `SprintItems` y features en el módulo existente `Sprints` (schema `sprints`); sin módulo nuevo (ADR-003).
- **Rationale**: El Sprint es el lado "uno" y el consumidor del dato; no se modifica `BacklogItem` (FR-013).
- **Alternativas**: asignación dentro de `Backlog` (modifica el agregado y rompe el aislamiento); módulo `SprintPlanning` con proyecciones por eventos (desproporcionado, exige Outbox y consistencia eventual); leer `BacklogDbContext` desde `Sprints` (consulta cross-schema prohibida).

## R-02: Verificación del elemento sin cruzar schemas
- **Decisión**: Contrato in-process `Sprints.Contracts.IBacklogModuleApi` (`ExistsAsync`, `GetSummariesAsync` → `BacklogItemSummary(Id, Title, Type, DevPoints, QAPoints)`), implementado por `Backlog.BacklogModuleApi`. `Type` viaja como `string`. Ver [contracts/backlog-module-api.md](./contracts/backlog-module-api.md).
- **Rationale**: Mismo patrón que `IApplicationModuleApi`; consistencia fuerte; `ItemId` queda sin FK en la BD.
- **Alternativas**: ver R-01. Riesgo aceptado: la BD no impide un `ItemId` huérfano si otro camino escribe sin pasar por el handler.

## R-03: "Un elemento, un Sprint" y 409
- **Decisión**: Índice único `UX_SprintItems_ItemId` sobre `ItemId` (ADR-004). El handler inserta y traduce `PostgresException` con `SqlState = 23505` **y** `ConstraintName = UX_SprintItems_ItemId` a `ConflictException`; cualquier otro `DbUpdateException` termina en 500. Una lectura previa `AnyAsync` es solo optimización.
- **Rationale**: Resuelve la concurrencia de forma declarativa (exactamente un 201, el resto 409).
- **Alternativas**: solo `AnyAsync` (carrera); índice compuesto `SprintId, ItemId` (permitiría el mismo elemento en otro Sprint); `SERIALIZABLE` o advisory lock (complejidad innecesaria).
- **Impacto en spec**: sustituye FR-015 y los casos borde "no documentado" (ver Summary del plan).

## R-04: Excepción 409 en Shared
- **Decisión**: Añadir `ConflictException` y la rama 409 (ProblemDetails, `Title = "Conflict"`) en `CustomExceptionHandler` (ADR-005). Cambio estrictamente aditivo; el mensaje no revela a qué Sprint pertenece el elemento.
- **Alternativas**: resultado tipado con `Results.Problem(409)` (rompe el modelo de excepciones semánticas); reutilizar `BadRequestException` (contradice la decisión humana).

## R-05: Identificadores como texto
- **Decisión**: `POST` recibe `sprintId` (ruta, `string`) e `itemId` (cuerpo, `string?`); el validador exige presencia, `Guid.TryParse` y distinto de `Guid.Empty`, con errores bajo `sprintId` e `itemId` (ADR-007). `GET` conserva `{sprintId:guid}` (un id malformado responde 404, la HU solo define 404 para Sprint inexistente).
- **Rationale**: FR-007 exige 400 con el detalle del campo; un `Guid` tipado daría 404 o un 400 sin campo.
- **Alternativas**: `Guid`/`Guid?` tipados (reporte por campo defectuoso).

## R-06: Orden de evaluación
- **Decisión**: (1) validador 400 → (2) `ICurrentUser.UserId` (401) → (3) Sprint existe (404 "Sprint") → (4) elemento existe (404 "elemento") → (5) 409 por índice → (6) un único `SaveChangesAsync`. Si faltan ambos, gana el 404 del Sprint.
- **Rationale**: Identidad antes que datos (constitución, patrón de HU-003); el contrato no se invoca si el Sprint no existe.

## R-07: Contrato HTTP
- **Decisión**: `POST /api/sprints/{sprintId}/items` → 201 Created (⚠️ [PROPUESTO]; la HU solo dice "código de éxito") con `Location` hacia el `GET` y cuerpo `{ sprintId, itemId }`; `GET /api/sprints/{sprintId}/items` → 200 con `[{ id, title, type, devPoints, qaPoints }]`. Sin estado ni auditoría en las respuestas (FR-008, FR-014). Ver [contracts/sprint-items-api.openapi.yaml](./contracts/sprint-items-api.openapi.yaml).
- **Rationale**: Alineado con el UX (reconciliado: ruta de UI `/sprints/:id/elementos`, ruta API `/api/sprints/{sprintId}/items`).

## R-08: Consulta
- **Decisión**: `AnyAsync` del Sprint → `SprintItems.AsNoTracking()` por `SprintId` ordenado por `CreatedAt` y luego `Id` (⚠️ [PROPUESTO], estabilidad, no es contrato de orden) → una sola llamada `GetSummariesAsync`. Si el contrato no devuelve un id, se omite y se registra `LogWarning`; no se inventa título.
- **Rationale**: Sin N+1; cumple SC-006 sin caché ni paginación (punto abierto 7).

## R-09: Eventos, Outbox y caché
- **Decisión**: Ninguno (ADR-006). `SprintItem : Aggregate<Guid>` sin eventos.
- **Rationale**: No hay consumidor hoy; HU-006/HU-031 lo añadirán si lo necesitan (con Outbox por ser crítico).

## R-10: Frontend
- **Decisión**: Componentes standalone OnPush con Signals: `sprint-assigned-items` y `assign-item-dialog`; tras el éxito se cierra el diálogo y se vuelve a consultar al servidor (sin UI optimista). Sin validación de negocio duplicada en cliente; el botón se deshabilita con `isSubmitting()`. Ruta `sprints/:id/elementos` dentro del bloque `sprints` (hereda `authGuard`), declarada antes de `:id`.
- **Rationale**: UX D-05, D-07 y SC-004.
