# Plan de Implementación: Registro de Elementos en Backlog Multitipo

**Branch**: `001-registro-backlog-multitipo` | **Date**: 2026-10-03 | **Spec**: [001-HU_registro_elementos_backlog_multitipo.md](./spec.md)

**Input**: Especificación de feature desde `specs/001-registro-backlog-multitipo/spec.md`

## Resumen

Desarrollo de un endpoint `POST /api/backlog/items` para permitir a usuarios autenticados (con JWT en Keycloak) registrar nuevos elementos de backlog (UserStory, Bug, Spike, etc.). Se aplicar Vertical Slice Architecture con Carter, CQRS (MediatR), validación FluentValidation y un mapeador (Mapster) en .NET 8/10 Modulith con PostgreSQL. Se persisten distintos tipos de ítems, controlando independientemente los puntos de estimación de Dev y QA. Se incluye la publicación del evento de dominio `BacklogItemCreatedDomainEvent` internamente en el módulo tras completar la transacción exitosamente.

## Contexto Técnico

**Lenguaje/Versión**: C# 12 / .NET 8 o 10 (Modulith).

**Dependencias Principales**: Carter (Minimal APIs), MediatR, Mapster, FluentValidation, EF Core (PostgreSQL). Seguridad con `Keycloak.AuthServices.Authentication`.

**Almacenamiento**: PostgreSQL con aislamiento multi-schema (Schema propio para el módulo Backlog).

**Pruebas**: xUnit o nUnit para Test-Driven Development (TDD) en el módulo correspondiente.

**Target Platform**: Contenedores Docker (Linux) en Arquitectura Modular Monolítica.

**Tipo de Proyecto**: Módulo de servicio web REST dentro de un Modulith.

**Objetivos de Rendimiento**: Tiempos de respuesta para creación menores a 500ms en condiciones normales (SC-004) y fallos de validación en menos de 200ms (SC-003).

**Restricciones**: El dominio y la capa de acceso a datos (EF Core) no pueden hacer JOIN ni consultas cross-schema a otros módulos. Las validaciones como existencia de `ApplicationId` deben realizarse por llamadas a interfaces intra-proceso (Comunicación síncrona según la matriz de arquitectura) o cachés.

**Escala/Alcance**: 100% de éxito de persistencia y encolamiento de Domain Events (CQRS/Event-Driven para dominio local).

## Chequeo de Constitución

*GATE: Superado satisfactoriamente (Phase 0 -> Phase 1).*

- **CQRS & VSA (@API)**: Endpoints se ubicarán en `Feature Folders` usando Carter e inyectando MediatR para las validaciones/comandos en lugar de Controladores MVC estándar.
- **Identidad (@API)**: Requiere políticas JWT (`.RequireAuthorization()`).
- **Domain Events (@DA)**: Se usarán agregados `Aggregate<TId>` con `IDomainEvent` despachado en la misma transacción mediante `DispatchDomainEventsInterceptor`. **No se aplicará Transactional Outbox** debido a que este no es un evento de integración (no es consumido por otro módulo).
- **Aislamiento Multi-schema (@DA)**: La estructura usará un schema `Backlog` dedicado, aislado del módulo de `Applications` o cualquier otro módulo.

## Estructura del Proyecto

### Documentación (Esta feature)

```text
specs/001-registro-backlog-multitipo/
 plan.md              # Este archivo (/speckit-plan command output)
 research.md          # Output de Fase 0 (investigación y clarificación)
 data-model.md        # Output de Fase 1 (modelo DDD)
 quickstart.md        # Output de Fase 1 (guía de prueba)
 contracts/           # Output de Fase 1
   api.md             # Contrato de API JSON
 tasks.md             # Generado en Fase 2 (por /speckit-tasks)
```

### Código Fuente (Raíz del Repositorio)

Por la constitución (Estructura de carpetas del workspace), todo archivo de producción vive bajo `app/backend/` o `app/frontend/`.

```text
app/backend/
 src/
  Bootstrapper/Api/
    Program.cs                       # Host único: AddBacklogModule/UseBacklogModule, CustomExceptionHandler, JsonStringEnumConverter, auth Keycloak
    Api.csproj
  BuildingBlocks/Shared/             # Reutilizar: ValidationBehavior, LoggingBehavior, AuditableEntityInterceptor, DispatchDomainEventsInterceptor, Aggregate<T>, excepciones base
  Modules/
   Backlog/
     BacklogModule.cs                # AddBacklogModule(): DbContext, interceptores de Shared, validadores, IApplicationModuleApi
     Backlog.csproj
     Contracts/
       IApplicationModuleApi.cs      # Interfaz cross-module (la implementa el módulo Application; no se define en el handler)
     Features/
       BacklogItems/
         CreateBacklogItem/
           CreateBacklogItemEndpoint.cs
           CreateBacklogItemCommand.cs
           CreateBacklogItemCommandHandler.cs
           CreateBacklogItemValidator.cs
     Domain/
       BacklogItems/
         BacklogItem.cs
         BacklogItemType.cs
         BacklogItemStatus.cs
         BacklogItemPriority.cs
         Events/
           BacklogItemCreatedDomainEvent.cs
     Data/
       BacklogDbContext.cs           # Schema propio `backlog`
       Configurations/
         BacklogItemConfiguration.cs
       Migrations/                   # Migración alineada con data-model.md
 tests/
  Unit/Backlog/
  Integration/Backlog/               # WebApplicationFactory<Program> + Testcontainers (PostgreSQL)
app/frontend/
 package.json, angular.json, jest.config.*, tsconfig*.json
 src/app/backlog/create-backlog-item/
   create-backlog-item.component.ts / .html / .scss / .spec.ts
```

**Decisión Estructural**: Implementación de Vertical Slice Architecture en un sub-módulo `Backlog` dentro de la arquitectura modular monolítica general. Se respeta la directiva inmutable de agrupar el Endpoint (Carter), Comando, Handler (MediatR) y Validador (FluentValidation) dentro de la carpeta descriptiva de la feature `CreateBacklogItem`.

## Decisiones Técnicas Complementarias (retrabajo iteración 1/2)

- **Host e infraestructura (DEF-06)**: el slice requiere `Program.cs`, `.csproj`, `BacklogDbContext` (schema `backlog`), registro DI en `BacklogModule.cs` e implementación de `IApplicationModuleApi`. Las interfaces `IBacklogDbContext` e `IApplicationModuleApi` se definen fuera del archivo del handler.
- **Pipeline (DEF-01/03)**: se registra `ValidationBehavior<,>` de `Shared` y los validadores del ensamblado; `CustomExceptionHandler` mapea `ValidationException` a HTTP 400 `ProblemDetails` con `errors` (FR-013) y `NotFoundException` de `applicationId` a 400 con la clave `ApplicationId`.
- **Interceptores (DEF-04/05)**: se registran los interceptores de `Shared` (`AuditableEntityInterceptor` asigna `CreatedAt`/`CreatedBy` desde el claim; `DispatchDomainEventsInterceptor` publica los eventos). No se reimplementan stubs locales (constitución §3).
- **Cancelación**: el endpoint recibe `CancellationToken` y lo pasa a `mediator.Send`.
- **Serialización**: `JsonStringEnumConverter` global; `priority` y `type` viajan como texto. El handler usa `Enum.TryParse`, no `Enum.Parse`.
- **Invariante QAPoints (FR-008)**: la regla "tipo técnico ⇒ `qaPoints` nulo, si llega con valor se rechaza" vive en `BacklogItem.Create`; la lista de tipos técnicos se define una sola vez en el dominio y el frontend la consume de una constante única. El tipo de `DevPoints`/`QAPoints` es el de `data-model.md` y el mismo en comando, entidad y columna.
- **Límites de longitud (FR-012)**: `Description` ≤ 4000 y `AcceptanceCriteria` ≤ 4000 caracteres, en validador y en la configuración EF.
- **Persistencia**: el schema se llama `backlog` (minúscula, constitución §3) y el tipo de columna `Type` coincide con `data-model.md`; se entrega migración Code-First.
- **Frontend (DEF-07/08)**: componente standalone con `@if`/`@for`, `Signals`/`toSignal`/`takeUntilDestroyed` en lugar de `subscribe()` manual, lista de aplicaciones cargada desde la API del módulo Application (valores `Guid`), `qaPoints: null` por defecto, lectura de `errors` del `ProblemDetails`, handler del botón Cancelar, estilos `.scss` y configuración `package.json`/`angular.json`/`jest.config`.
- **Pruebas**: integración con `WebApplicationFactory<Program>` y Testcontainers (INT-01..INT-10) sobre el host real; Jest para el componente.

## Decisiones Técnicas Complementarias (retrabajo iteración 2/2)

- **Catálogo de aplicaciones (#16)**: el host expone `GET /api/applications` (Carter, `.RequireAuthorization()`, recibe `CancellationToken`) que devuelve `[{ "id": Guid, "name": string }]` leyendo vía `IApplicationModuleApi` (sin consulta cross-schema). Se documenta en `contracts/api.md`. El frontend consume solo este endpoint.
- **Autenticación del cliente (#17, FR-001, FR-009)**: el frontend obtiene el token de Keycloak (Authorization Code + PKCE), registra un `HttpInterceptorFn` que añade `Authorization: Bearer` a las llamadas a `/api/**`, un guard de ruta que redirige al login y la reautenticación ante HTTP 401. El componente no se renderiza sin sesión.
- **Configuración Keycloak por entorno (#18)**: `appsettings.json` base queda seguro (`ssl-required: external`, `verify-token-audience: true`, audiencia configurada). Solo `appsettings.Development.json` puede relajar `ssl-required`; los valores sensibles se inyectan por variables de entorno.
- **Migraciones (#18)**: la migración Code-First se aplica en el despliegue (bundle de migraciones o `dotnet ef database update` en el pipeline, nunca `Migrate()` implícito en producción) y se prueba contra PostgreSQL con Testcontainers.
- **Orden del handler (#19, FR-009)**: la identidad (`sub`) se resuelve y valida al inicio del handler, antes de consultar el catálogo de aplicaciones o cualquier acceso a datos; sin claim se responde 401 sin tocar la base de datos. El interceptor de auditoría solo lee la identidad ya resuelta.
- **Pruebas**: INT-01..INT-10 más casos para #16..#19 (catálogo autenticado, 401 sin acceso a datos, configuración Keycloak no insegura fuera de Development, migración sobre PostgreSQL).

## Seguimiento de Complejidad

> No existen violaciones a la constitución, por lo tanto, no se requieren alternativas rechazadas documentadas.
