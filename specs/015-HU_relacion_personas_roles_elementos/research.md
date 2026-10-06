# Research: Relación entre Personas, Roles y Elementos de Trabajo

Fuentes: `spec.md`, `documents/solutions-architect/015-HU_relacion_personas_roles_elementos.md` (ADR-001..008), `documents/designer-ux/ux_015_*.md` y la resolución humana B del tracker. No quedan `NEEDS CLARIFICATION`.

## D1. Ubicación de la relación y acceso al elemento
- **Decisión**: la tabla `ItemAssignments` y sus features viven en `Teams`; el elemento se lee por el contrato in-process `IBacklogItemLookup` (`ExistsAsync`, `GetItemsAsync` → `BacklogItemRef(Id, Title, Type)`), implementado en `Backlog`.
- **Justificación**: FR-013 declara intocable `BacklogItem`; FR-014 y la constitución §3 prohíben consultas cross-schema; reutiliza el patrón de HU-004 (`IBacklogModuleApi`).
- **Alternativas**: relación en `Backlog` (modifica el agregado); módulo `Assignments` con proyecciones por Integration Events (desproporcionado: Outbox y consistencia eventual); rol copiado a la fila (dato duplicado); lectura directa de `BacklogDbContext` (cross-schema prohibido).

## D2. Rol de la relación
- **Decisión**: no se almacena; se obtiene del rol técnico vigente del miembro con JOIN local en cada consulta.
- **Justificación**: FR-005 pide mostrar el rol ya registrado, sin elegir otro por asignación.
- **Alternativas**: columna `Role` en la relación (diverge si HU-012 cambiara el rol).

## D3. Asignación duplicada (resolución humana B)
- **Decisión**: idempotente. Índice único `UX_ItemAssignments_ItemId_MemberId`; lectura previa para responder 200 sin escribir; si el insert falla con `PostgresException` 23505 **de ese índice**, se relee la fila ganadora y se responde 200.
- **Justificación**: la unicidad es una invariante de datos; la lectura previa es solo optimización. Cubre la concurrencia sin bloqueos.
- **Alternativas**: solo validación en handler (carrera); `INSERT … ON CONFLICT` crudo (evade `AuditableEntityInterceptor`); `SERIALIZABLE`/advisory lock (complejidad); 409 (descartado por el humano).
- **Reconciliación**: `spec.md` aún dice "no documentado" para duplicados (Edge Case y FR-015). Para el desarrollo es vinculante `tech_guidelines`/SA; se anota en `tasks.md` la actualización pendiente del BA.

## D4. Códigos de éxito
- **Decisión**: 201 Created con `Location` hacia `GET /api/backlog-items/{itemId}/assignees` si se crea; 200 OK con el mismo cuerpo si ya existía. Cuerpo `{ itemId, memberId, memberName, role }`, sin bandera ni auditoría.
- **Justificación**: FR-003 solo exige "código de éxito"; el UX distingue "asignado" de "ya era responsable" por código HTTP (⚠️ [PROPUESTO]).

## D5. Identificadores y validación por campo
- **Decisión**: en el POST, `itemId` (ruta) y `memberId` (cuerpo) se reciben como `string`; el validador exige presencia, `Guid.TryParse` y no `Guid.Empty`, con errores bajo `itemId` y `memberId`. Las consultas conservan `:guid` (malformado ⇒ 404).
- **Justificación**: FR-010 exige 400 con el detalle de campos inválidos; un `Guid` tipado produciría 404 o un 400 sin campo (mismo caso que HU-003/HU-004).

## D6. Orden de evaluación y prioridad de 404
- **Decisión**: validador 400 → identidad 401 → miembro 404 → elemento 404 → duplicado 200 → `SaveChanges` 201. Si faltan ambos, gana el 404 del miembro.
- **Justificación**: la comprobación del miembro es local y barata y evita invocar el contrato. El `detail` distingue miembro de elemento (FR-009, UX Estados 8–9).

## D7. Consultas sobre identificadores inexistentes
- **Decisión**: un elemento o miembro bien formado pero inexistente devuelve 200 con colección vacía (⚠️ [PROPUESTO]); la spec solo define 200 para consultas y los selectores impiden el caso.
- **Alternativa**: 404 (no definido por la HU).

## D8. `ListMemberItems` y elementos ya inexistentes
- **Decisión**: una sola llamada de lote a `GetItemsAsync`; si no devuelve algún id, se omite y se registra `LogWarning` (sin inventar título).

## D9. Fuente de los selectores del UX
- **Decisión**: miembros desde `GET /api/team-members` (HU-012); elementos desde la nueva consulta aditiva `GET /api/backlog-items` → `[{ id, title, type }]` (sin estimaciones, estado ni Sprint), sin paginación (⚠️ [PROPUESTO], ADR-006).
- **Alternativas**: campo de texto con GUID (induce errores); endpoint en `Teams` que liste elementos (datos ajenos); paginación/filtros (prematuro).
- **Riesgo**: nueva superficie en HU-001; se valida con prueba de no regresión del `POST` existente.

## D10. Sin eventos, Outbox ni caché
- **Decisión**: `ItemAssignment` hereda de `Aggregate<Guid>` pero no emite eventos; sin `OutboxMessage`, MassTransit ni Redis (ADR-007). HU-010/HU-014 añadirán el evento cuando exista consumidor.

## D11. Integridad del `ItemId` sin FK
- **Decisión**: `ItemId uuid NOT NULL` sin FK (el elemento vive en `backlog`); FK real `MemberId → teams."TeamMembers"("Id")` `ON DELETE RESTRICT`. La integridad del elemento depende de verificar por contrato antes de persistir y de que no existe borrado de elementos hoy.

## D12. Frontend
- **Decisión**: pestaña `Responsables` en `team-page`, rutas `equipos/responsables` y `equipos/responsables/miembro` dentro del bloque `equipos` existente (heredan `authGuard`); tras 201/200 se vuelve a consultar al servidor (sin Optimistic UI); el rol del diálogo es de solo lectura derivado del miembro; el shell (topbar/sidebar) sigue fuera de alcance.
