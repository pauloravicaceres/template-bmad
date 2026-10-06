# Research: Miembros del Equipo y Roles Técnicos

Las decisiones provienen de `documents/solutions-architect/012-HU_miembros_equipo_y_roles_tecnicos.md` y de la constitución; aquí se consolidan. No quedaban `NEEDS CLARIFICATION`.

## R-01: Ubicación de miembros y roles
- **Decisión**: Módulo nuevo `Teams` (schema `teams`) que aloja el catálogo de roles y los miembros (ADR-003). Nombrado por dominio para que HU-013 a HU-015 lo extiendan.
- **Rationale**: Ningún módulo existente es dueño natural de personas; no se modifica ningún módulo `ACTIVE` (FR-014).
- **Alternativas**: añadir `TeamMember` a `Backlog` o `Sprints` (modifica módulos ajenos y mezcla dominios); dos módulos `Members` y `Roles` (desproporcionado, exigiría contrato in-process para validar el rol); persona en Keycloak (descartado por FR-010).

## R-02: Relación miembro–rol sin cruzar schemas
- **Decisión**: Ambas tablas en `teams`; FK real `TeamMembers.TechnicalRoleId → TechnicalRoles.Id` con `ON DELETE RESTRICT` y `JOIN` local para listar (ADR-002).
- **Rationale**: La prohibición cross-schema no aplica dentro del mismo schema; integridad garantizada por la BD. No se define `ITeamsModuleApi`: no hay consumidor en esta HU (ADR-004).
- **Alternativas**: contrato in-process o proyecciones por eventos (sin consumidor, sin requisito).

## R-03: Origen del catálogo de roles
- **Decisión**: `InsertData` en la migración `InitialTeamsSchema` con GUID fijos en `TechnicalRoleSeed`; índice único `UX_TechnicalRoles_Name`; sin endpoint de alta, edición ni borrado (ADR-004).
- **Rationale**: Catálogo reproducible y versionado con el esquema; las pruebas pueden fijar los identificadores.
- **Alternativas**: enum de C# (no cumple "identificador y nombre" ni crece sin recompilar); siembra en arranque con `IHostedService` (punto de fallo y carrera con varias instancias); tabla vacía con alta de roles (inventa administración del catálogo, punto abierto 4).

## R-04: Auditoría de `TechnicalRole`
- **Decisión**: `TechnicalRole : Aggregate<Guid>` **sin** `IAuditableEntity`; solo `Id` y `Name`. `TeamMember : Aggregate<Guid>, IAuditableEntity`.
- **Rationale**: `Shared` solo ofrece `Aggregate<TId>` e `IAuditableEntity` (no existe `Entity<TId>`). `AuditableEntityInterceptor` actúa solo sobre `IAuditableEntity`, así que la semilla de la migración no necesita fecha ni usuario "system" y se evita inventar columnas de auditoría de alta para el catálogo. Resuelve la decisión delegada por el SA (§9).
- **Alternativas**: auditar el rol con fecha y usuario `system` en la semilla (columnas sin consumidor).

## R-05: Contrato del rol en el registro
- **Decisión**: `POST /api/team-members` recibe `{ name, role }` donde `role` es el **nombre**; el handler lo resuelve con `TechnicalRoles.FirstOrDefaultAsync(r => r.Name == role)` (sensible a mayúsculas) y lanza `BadRequestException` con `TeamMemberRules.InvalidRoleMessage` si no existe (ADR-005). La respuesta devuelve `{ id, name, role }` con el nombre del rol.
- **Rationale**: Coincide con los escenarios ("Chef" ⇒ 400) y distingue el 400 por rol inválido del 400 por campo ausente por el mensaje.
- **Alternativas**: `roleId` GUID (un "Chef" no es un identificador); aceptar ambos (ambigüedad); 404 para rol inexistente (la spec fija 400).

## R-06: Orden de evaluación y atomicidad del registro
- **Decisión**: validador 400 (nombre y rol presentes, no vacíos ni de solo espacios; errores bajo `name` y `role`) → `ICurrentUser.UserId` (sin claim: `UnauthorizedAccessException`, 401) → rol existe (400) → `Add` + un único `SaveChangesAsync`. El handler guarda `name.Trim()`.
- **Rationale**: Una fila y una transacción: no existe estado parcial (FR-013, SC-008). Con nombre inválido y rol inexistente gana el 400 del validador sin consultar la BD.
- **Alternativas**: sin reintentos automáticos de escritura (no es idempotente: repetir crearía otro miembro).

## R-07: Nombre sin restricciones inventadas
- **Decisión**: `TeamMembers.Name` es `text NOT NULL`, sin índice único ni límite de longitud; solo se valida presencia (ADR-007, FR-015).
- **Rationale**: Unicidad, longitud y caracteres son puntos abiertos 2 y CB-05/CB-06; imponerlos de facto contradiría FR-015. Añadirlos después es una migración y un validador, no un cambio de modelo.
- **Riesgo aceptado**: un token válido puede enviar un nombre muy grande (límite de cuerpo de Kestrel) y se admiten homónimos y doble registro.

## R-08: Código de éxito y ruteo
- **Decisión**: 201 Created con `Location` hacia `GET /api/team-members` (⚠️ [PROPUESTO], la HU solo dice "código de éxito"). Rutas de API `/api/team-members` y `/api/technical-roles`; las rutas `/equipos` del UX son de UI. Orden de las consultas ⚠️ [PROPUESTO]: miembros por `CreatedAt` y `Id`, roles por `Name`; sin paginación, filtros ni `CreatedAt`/`CreatedBy` en respuestas (UX D-09).
- **Rationale**: Patrón de HU-003 y HU-004; el orden estable no es contrato (punto abierto 7).

## R-09: Eventos, Outbox y caché
- **Decisión**: Ninguno (ADR-006). `TeamMember` hereda de `Aggregate<Guid>` pero no emite eventos.
- **Rationale**: Sin consumidor ni cuello de botella medido; si una HU posterior reacciona al registro añadirá evento y Outbox.

## R-10: Identidad y logging
- **Decisión**: Las lecturas dependen solo de `.RequireAuthorization()` (401 sin leer datos, FR-011). `CreatedBy` proviene del `sub` vía interceptor, nunca del cuerpo. El nombre del miembro es dato personal: no se escribe en logs ni se devuelve `CreatedBy`.
- **Rationale**: Mismo patrón que HU-003 y HU-004; riesgo aceptado: sin roles de acceso, cualquier usuario autenticado puede registrar (punto abierto 6).

## R-11: Frontend
- **Decisión**: Feature `teams` con `team-page` (contenedor con `p-tabs`; pestaña derivada de la URL `equipos` o `equipos/roles`) y `register-member-dialog`. Estado en Signals, sin caché entre navegaciones, refresco de la grilla con consulta fresca tras el éxito, botón deshabilitado durante `isSubmitting()`, error de lectura genérico ⚠️ [PROPUESTO] con `Reintentar`. El shell/sidebar sigue sin existir: se entrega página y rutas.
- **Rationale**: Patrón de `features/sprints`; sin validación de negocio duplicada en el cliente (UX D-05).
