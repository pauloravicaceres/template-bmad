# Research: Gestión de Sprint de Dos Semanas

Todas las decisiones provienen de `documents/solutions-architect/003-HU_gestion_sprint_dos_semanas.md` y de la constitución; aquí se consolidan. No quedaban `NEEDS CLARIFICATION`.

## R-01: Ubicación del Sprint (módulo propio)
- **Decisión**: Nuevo módulo `Sprints` con schema `sprints` y `SprintsDbContext` (ADR-003).
- **Rationale**: Ciclo de vida propio; la constitución exige schema por módulo. El plural evita colisión del namespace con el tipo `Sprint`.
- **Alternativas**: dentro de `Backlog` (mezcla agregados, FK cómoda pero estorba la extracción); dentro de `Application` (dominio ajeno); servicio físico aparte (prohibido por la constitución).

## R-02: Tipo y formato de fechas
- **Decisión**: `DateOnly` mapeado a `date`; el command recibe `string?` y el validador exige `yyyy-MM-dd` con `DateOnly.TryParseExact` (`InvariantCulture`) (ADR-004).
- **Rationale**: Sin zona horaria los límites de ±1 día son deterministas; el error de formato se reporta por campo (SC-05), cosa que un fallo de binding JSON no permite.
- **Alternativas**: `DateOnly?` con binder (error sin nombre de campo); `DateTime`/`timestamptz` (huso y hora no definidos por el negocio).

## R-03: Invariante de ventana de 2 semanas
- **Decisión**: Fuente única `SprintRules.WindowDays = 14` (fin = inicio + 13). Tres capas: validador (400 por campo en `EndDate`), `Sprint.Create` (`BadRequestException`) y `CHECK` `CK_Sprints_Window` (`"EndDate" - "StartDate" = 13`) (ADR-005).
- **Rationale**: FR-015/SC-003 exigen el 100 % de Sprints válidos aunque una futura ruta omita el validador. El supuesto (14 días inclusivos) está pendiente de confirmación de negocio (punto abierto 3).
- **Alternativas**: solo validador (garantía débil); solo `CHECK` (error 500 en lugar de 400 con mensaje de negocio).

## R-04: Identificación, unicidad y solapamiento
- **Decisión**: Texto libre obligatorio con máximo técnico 100; sin índice único, sin detección de duplicados ni de solapamiento, sin idempotencia (ADR-006).
- **Rationale**: Puntos abiertos 4 y 5 sin documentar; la spec prohíbe inventar escenarios. Riesgo aceptado: doble envío crea dos Sprints (mitigación solo en UI).
- **Alternativas**: índice único sobre `Identification`; validación de solapamiento (reglas de negocio no confirmadas).

## R-05: Eventos, Outbox y caché
- **Decisión**: No se emiten eventos ni se usa Outbox/Redis (ADR-007).
- **Rationale**: Ningún requisito lo pide y 100 Sprints no justifican caché.
- **Alternativas**: `SprintCreatedDomainEvent` anticipado; decorador Redis para el listado.

## R-06: Contrato HTTP
- **Decisión**: `POST /api/sprints` (201 + `Location`), `GET /api/sprints` (200, arreglo), `GET /api/sprints/{id:guid}` (200/404). Respuestas con `id, identification, startDate, endDate` en camelCase; sin `CreatedAt`/`CreatedBy`. Errores 400 como ProblemDetails con `errors` por campo.
- **Rationale**: Alineado con el UX (Estado 5) y el `CustomExceptionHandler` existente.
- **Alternativas**: exponer auditoría en la respuesta (el UX no la muestra).

## R-07: Orden del listado
- **Decisión**: `AsNoTracking()`, proyección a DTO y orden determinista por `StartDate` asc y luego `Id`; sin paginación ni filtros.
- **Rationale**: Resultados estables; el orden de negocio es el punto abierto 9, por lo que no es contrato.

## R-08: Identidad
- **Decisión**: `CreateSprintCommandHandler` resuelve `ICurrentUser.UserId` antes de acceder a datos; sin claim lanza `UnauthorizedAccessException` (401). Las consultas dependen de `.RequireAuthorization()`. Sin roles (punto abierto 7).

## R-09: Frontend
- **Decisión**: Componentes standalone `OnPush` con Signals, formularios reactivos tipados, i18n nativo, fechas enviadas como `yyyy-MM-dd`, sin caché entre navegaciones. Tras un 201 se navega a `/sprints` y se vuelve a consultar al servidor.
- **Nota**: el shell de navegación (topbar/sidebar) aún no existe en el repositorio; la HU entrega páginas y rutas, y el shell se registra como punto abierto informativo.

## Puntos abiertos de negocio que NO se resuelven aquí
1 (ciclo de vida), 3 (interpretación de ventana, supuesto adoptado), 4, 5, 6, 7, 8 y 9: fuera de alcance o supuestos documentados en `spec.md` → Assumptions.
