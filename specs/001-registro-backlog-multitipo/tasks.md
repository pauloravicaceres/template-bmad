---
description: "Lista de tareas para la implementación de la funcionalidad de Registro de Elementos en Backlog Multitipo"
---

# Tareas: Registro de Elementos en Backlog Multitipo

**Input**: Documentos de diseño desde `/specs/001-registro-backlog-multitipo/`

**Prerrequisitos**: plan.md (requerido), spec.md (requerido para historias de usuario), research.md, data-model.md, contracts/

**Organización**: Las tareas están agrupadas por historia de usuario para permitir la implementación y prueba independiente de cada historia.

## Formato: `[ID] [P?] [Story] Descripción`

- **[P]**: Puede ejecutarse en paralelo (diferentes archivos, sin dependencias)
- **[Story]**: A qué historia de usuario pertenece esta tarea (ej. US1, US2)

---

## Fase 1: Configuración (Setup)

**Propósito**: Inicialización de la estructura y carpetas del módulo

- [X] T001 Crear estructura de carpetas para la feature `CreateBacklogItem` en `src/Modules/Backlog/Features/BacklogItems/CreateBacklogItem/`
- [X] T002 [P] Crear estructura de carpetas de dominio en `src/Modules/Backlog/Domain/BacklogItems/Events/`
- [X] T003 [P] Crear estructura de carpetas de datos en `src/Modules/Backlog/Data/Configurations/`

---

## Fase 2: Fundacional (Prerrequisitos Bloqueantes)

**Propósito**: Infraestructura core y entidades de dominio que DEBEN estar completas antes de iniciar las historias de usuario.

**⚠️ CRÍTICO**: Ningún trabajo de historia de usuario puede comenzar hasta que esta fase esté completa.

- [X] T004 [P] Crear enumeración `BacklogItemType` en `src/Modules/Backlog/Domain/BacklogItems/BacklogItemType.cs` con los valores: UserStory, Bug, TechEvolution, TechRequirement, TechDebt, Research, Spike.
- [X] T005 [P] Crear enumeración `BacklogItemStatus` en `src/Modules/Backlog/Domain/BacklogItems/BacklogItemStatus.cs` con el valor inmutable inicial `Backlog`.
- [X] T006 [P] Crear evento de dominio `BacklogItemCreatedDomainEvent` en `src/Modules/Backlog/Domain/BacklogItems/Events/BacklogItemCreatedDomainEvent.cs` con propiedades `BacklogItemId`, `Type`, `ApplicationId`, y `OccurredOnUtc`.
- [X] T007 Crear entidad raíz de agregado `BacklogItem` en `src/Modules/Backlog/Domain/BacklogItems/BacklogItem.cs` heredando de `Aggregate<Guid>`.
- [X] T008 Configurar EF Core Entity Type Builder para `BacklogItem` en `src/Modules/Backlog/Data/Configurations/BacklogItemConfiguration.cs` aislando en el schema `Backlog`.

**Punto de control**: Base fundacional lista - la implementación de historias de usuario puede comenzar.

---

## Fase 3: Historia de Usuario 1 - Registro completo de Historia de Usuario (Prioridad: P1) 🎯 MVP

**Objetivo**: Permitir a usuarios autenticados registrar un elemento de tipo Historia de Usuario con estimaciones independientes para desarrollo y QA.

**Prueba Independiente**: Probar enviando un payload completo a `/api/backlog/items` verificando HTTP 201 y creación exitosa de `devPoints` y `qaPoints`.

### Pruebas para Historia de Usuario 1 (Opcional)

- [X] T009 [P] [US1] Prueba de integración para endpoints verificando el caso exitoso (HTTP 201) y rechazo sin token (HTTP 401 Unauthorized) en `tests/Integration/Backlog/CreateBacklogItemTests.cs`.
- [X] T010 [P] [US1] Pruebas unitarias para las validaciones del comando en `tests/Unit/Backlog/CreateBacklogItemValidatorTests.cs`.

### Implementación para Historia de Usuario 1

- [X] T011 [P] [US1] Crear registro `CreateBacklogItemCommand` en `src/Modules/Backlog/Features/BacklogItems/CreateBacklogItem/CreateBacklogItemCommand.cs`.
- [X] T012 [P] [US1] Crear validador `CreateBacklogItemValidator` en `src/Modules/Backlog/Features/BacklogItems/CreateBacklogItem/CreateBacklogItemValidator.cs`. Incluir las siguientes reglas exactas: Title "NotEmpty().MaximumLength(200)", Type "IsInEnum() o validación contra el catálogo estático.", DevPoints "GreaterThanOrEqualTo(0).When(x => x.DevPoints.HasValue)", y QAPoints "GreaterThanOrEqualTo(0).When(x => x.QAPoints.HasValue)".
- [X] T013 [US1] Implementar `CreateBacklogItemCommandHandler` en `src/Modules/Backlog/Features/BacklogItems/CreateBacklogItem/CreateBacklogItemCommandHandler.cs`. Incluir validación asíncrona exacta: "Si tiene valor, el handler verificará asincrónamente su existencia consultando el módulo Application (IApplicationModuleApi.ExistsAsync(applicationId)). Si no existe, lanzará ValidationException mapeada a HTTP 400." y publicar evento de dominio.
- [X] T014 [US1] Implementar Minimal API endpoint usando Carter en `src/Modules/Backlog/Features/BacklogItems/CreateBacklogItem/CreateBacklogItemEndpoint.cs` para manejar `POST /api/backlog/items` requiriendo autorización JWT.

**Punto de control**: La Historia de Usuario 1 debe ser completamente funcional y testeable.

---

## Fase 4: Historia de Usuario 2 - Registro de elemento técnico sin estimación de QA (Prioridad: P2)

**Objetivo**: Permitir a usuarios autenticados registrar una investigación técnica preliminar (Spike) que no requiere puntos de QA.

**Prueba Independiente**: Probar enviando un elemento tipo `Spike` con `qaPoints` igual a nulo y verificando que se almacena correctamente.

### Pruebas para Historia de Usuario 2 (Opcional)

- [X] T015 [P] [US2] Prueba de integración para crear tipo Spike con `qaPoints` igual a nulo en `tests/Integration/Backlog/CreateBacklogItemTests.cs`.

### Implementación para Historia de Usuario 2

- [X] T016 [US2] Ajustar o verificar el manejo de nulos en `src/Modules/Backlog/Features/BacklogItems/CreateBacklogItem/CreateBacklogItemCommandHandler.cs` para asegurar que `qaPoints` en elementos técnicos se guarde y retorne como nulo correctamente.

**Punto de control**: Ambas historias de usuario deben funcionar independientemente.

---

## Fase 5: Pulido y Aspectos Transversales

**Propósito**: Mejoras finales, validaciones de extremos y aseguramiento de la calidad.

- [ ] T017 [P] Ejecutar todos los escenarios de prueba descritos en `quickstart.md` localmente mediante cURL o postman. _Diferida como ejecución manual por decisión humana (03-10-2026)._
- [X] T018 Confirmar la inyección correcta de `CreatedAt` y `CreatedBy` a través de interceptores (`AuditableEntityInterceptor`). _Evidencia: `qa-report.md`, INT-07 sobre PostgreSQL (cuarta ejecución)._
- [X] T019 Validar rechazo de peticiones vacías (HTTP 400) o campos excesivamente largos según FR-004.

---

## Dependencias y Orden de Ejecución

### Dependencias de Fase

- **Configuración (Fase 1)**: Sin dependencias.
- **Fundacional (Fase 2)**: Depende de Configuración - BLOQUEA todas las historias de usuario.
- **Historias de Usuario (Fase 3+)**: Dependen de la Fase Fundacional. Pueden desarrollarse en paralelo.
- **Pulido (Fase 5)**: Depende de completar todas las historias de usuario.

### Oportunidades de Paralelismo

- Las tareas marcadas con `[P]` en la Fase 1 y Fase 2 pueden avanzar en paralelo.
- La creación de enumeraciones y el evento de dominio (T004, T005, T006) pueden ser trabajadas simultáneamente antes de T007.
- La creación de pruebas (T009, T010, T015), el comando (T011) y el validador (T012) de la US1 pueden hacerse en paralelo.

## Estrategia de Implementación

### Entrega Incremental

1. Completar Configuración + Fundacional → La base está lista.
2. Añadir Historia de Usuario 1 → Probar de manera independiente → Entregar MVP.
3. Añadir Historia de Usuario 2 → Probar de manera independiente → Desplegar MVP mejorado.

---

## Fase 6: Convergencia (Retrabajo iteración 1/2)

**Origen**: rechazo de Code Review (`code-review/impact-analysis-report.md`, 3.ª iteración). Etiqueta `[fix:<CAPA>:<hallazgo>]`; entre corchetes finales, el responsable: **servidor** (@DEV-BACK) o **interfaz** (@DEV-FRONT). La spec y el plan ya se corrigieron; estas tareas llevan el código a ese estado. T013, T014, T017, T018 y T019 se desmarcaron arriba por estar cerradas sin cumplirse.

### Capa SPEC y PLAN (artefactos de diseño)

- [X] T020 [fix:SPEC:13] Alinear `specs/001-registro-backlog-multitipo/contracts/api.md` con FR-008: documentar que `qaPoints` con valor en un tipo técnico devuelve HTTP 400 (no se descarta). El archivo tiene codificación no UTF-8 (acentos corruptos): reescribirlo completo en UTF-8 [servidor]
- [X] T021 [fix:SPEC:14] Completar `contracts/api.md` y `data-model.md` con `priority` (texto: Low, Medium, High, Critical), `acceptanceCriteria`, límites de `description`/`acceptanceCriteria`, formato `ProblemDetails` con `errors{}` (FR-011, FR-012, FR-013) y el tipo único de `DevPoints`/`QAPoints` [servidor]
- [X] T022 [fix:PLAN:DEF-06] Crear bajo `app/backend/src/` el host `Bootstrapper/Api/Program.cs` y `.csproj`, `BacklogModule.cs`, `BacklogDbContext` (schema `backlog`) que aplique `BacklogItemConfiguration`, y la implementación de `IApplicationModuleApi`; mover `IBacklogDbContext` e `IApplicationModuleApi` fuera del handler y trasladar el código de `src/Modules/Backlog` a `app/backend/` según la constitución [servidor]

### Capa CODE — servidor

- [X] T023 [fix:CODE:DEF-01] Registrar `ValidationBehavior<,>` de `Shared` y los validadores del ensamblado en `BacklogModule.cs`, para que `CreateBacklogItemValidator` se ejecute antes del handler (T013) [servidor]
- [X] T024 [fix:CODE:DEF-03] Mapear `ValidationException` y la `NotFoundException` de `applicationId` a HTTP 400 `ProblemDetails` con `errors` mediante `CustomExceptionHandler` en `Program.cs` (FR-007, FR-013) [servidor]
- [X] T025 [fix:CODE:DEF-04] Sustituir el `AuditableEntityInterceptor` vacío por el de `Shared`, registrado en el `DbContext`, que asigne `CreatedAt` y `CreatedBy` desde el claim; sin claim, HTTP 401 (FR-009, T018) [servidor] _Evidencia: `qa-report.md`, DEF-04 corregido, INT-07 y caso #19 (401 sin claim)._
- [X] T026 [fix:CODE:DEF-05] Registrar `DispatchDomainEventsInterceptor` de `Shared` para publicar `BacklogItemCreatedDomainEvent` antes del commit (FR-010) [servidor]
- [X] T027 [fix:CODE:1] Recibir `CancellationToken` en la lambda de `CreateBacklogItemEndpoint.cs` y pasarlo a `mediator.Send` (T014) [servidor]
- [X] T028 [fix:CODE:DEF-07] Registrar `JsonStringEnumConverter` global para que `priority` y `type` se acepten como texto (FR-011) [servidor]
- [X] T029 [fix:CODE:11] Mover la regla "tipo técnico ⇒ `qaPoints` nulo, con valor se rechaza" al agregado `BacklogItem.Create`, definir la lista de tipos técnicos una sola vez y quitar la duplicación del handler (FR-008) [servidor]
- [X] T030 [fix:CODE:menores-servidor] Añadir `MaximumLength` a `Description` y `AcceptanceCriteria` en validador y `BacklogItemConfiguration`; cambiar `Enum.Parse` por `Enum.TryParse`; generar la migración Code-First y alinear el schema `backlog` y el tipo de `Type` con `data-model.md`; quitar el `using` sin uso de `Aggregate.cs` [servidor]
- [X] T031 [fix:CODE:DEF-02] Commitear `.NotEmpty()` en `Type` de `CreateBacklogItemValidator.cs:14-17` y confirmar que `Validate_ConTipoNulo_DebeFallarEnType` pasa (T012) [servidor]

### Capa CODE — interfaz

- [X] T032 [fix:CODE:DEF-07] Cargar la lista de aplicaciones desde la API del módulo Application con `Guid` reales, sin el valor `app-id-101` [interfaz] _Evidencia: `qa-report.md`, DEF-07 corregido, Jest 31/31._
- [X] T033 [fix:CODE:DEF-08] Crear `create-backlog-item.component.scss` y la configuración `package.json`, `angular.json` y `jest.config` para que el build y Jest funcionen [interfaz]
- [X] T034 [fix:CODE:12] Enviar `qaPoints: null` por defecto para UserStory/Bug en lugar de `0` [interfaz]
- [X] T035 [fix:CODE:14] Leer `errors` del `ProblemDetails` en lugar de `err.error?.message?.includes('aplicación')` y mostrar el error por campo [interfaz]
- [X] T036 [fix:CODE:5] Reemplazar los `subscribe()` manuales por `Signals`/`toSignal`/`takeUntilDestroyed`, usar `@if`/`@for` en lugar de `*ngIf`, añadir el handler de Cancelar y centralizar la lista de tipos técnicos en una constante [interfaz]

### Capa TASKS y verificación

- [ ] T037 [fix:TASKS:15] Tras T022–T036, ejecutar INT-01..INT-10 con `WebApplicationFactory<Program>` y Testcontainers (sustituir `FakeBacklogDb`), añadir pruebas del endpoint con token cancelado y del interceptor, ejecutar la suite Jest (14 pruebas y `.spec.ts` del componente), actualizar `documents/qa-auto/qa-report.md` y volver a marcar `[X]` T013, T014, T017, T018 y T019 solo con evidencia [servidor + interfaz, QA]

## Fase 7: Convergencia (Retrabajo iteración 2/2)

**Origen**: rechazo de Code Review (`documents/code-review/impact-analysis-report.md`, hallazgos #16..#19). `plan.md` y `contracts/api.md` ya se corrigieron; estas tareas llevan el código a ese estado. T018, T025 y T032 se desmarcaron por estar cerradas sin cumplirse. Responsable entre corchetes: **servidor** o **interfaz**.

- [X] T038 [fix:PLAN:16] Crear el endpoint Carter `GET /api/applications` con `.RequireAuthorization()` y `CancellationToken`, que devuelva `{id, name}` vía `IApplicationModuleApi` según `contracts/api.md`; cubrirlo con prueba de integración (200 con token, 401 sin token) [servidor]
- [X] T039 [fix:PLAN:17] Implementar la autenticación del cliente: login Keycloak (Code + PKCE), `HttpInterceptorFn` que añade el Bearer a `/api/**`, guard de ruta y reautenticación ante 401; añadir pruebas Jest del interceptor y del guard (FR-001, FR-009) [interfaz]
- [X] T040 [fix:PLAN:18] Asegurar `appsettings.json` base (`ssl-required: external`, `verify-token-audience: true`), relajar solo en `appsettings.Development.json`, inyectar secretos por entorno y añadir una prueba que falle si la base queda insegura [servidor]
- [X] T041 [fix:PLAN:18] Añadir el paso de migraciones al despliegue (bundle o `dotnet ef database update`) y validar la migración Code-First contra PostgreSQL con Testcontainers [servidor]
- [X] T042 [fix:CODE:19] Resolver y validar la identidad (`sub`) al inicio de `CreateBacklogItemCommandHandler`, antes de consultar `IApplicationModuleApi`; sin claim, HTTP 401 sin acceso a datos; añadir prueba que verifique que no se consulta el catálogo (FR-009) [servidor]
- [X] T043 [fix:TASKS:16-19] Tras T038–T042, ejecutar INT-01..INT-10 y los casos #16..#19 contra PostgreSQL (Testcontainers) y la suite Jest, actualizar `documents/qa-auto/qa-report.md` y marcar `[X]` T018, T025 y T032 solo con evidencia [servidor + interfaz, QA] _Evidencia: `qa-report.md` cuarta ejecución (62/62, 31/31, Jest 31/31), reverificada por Code Review._
