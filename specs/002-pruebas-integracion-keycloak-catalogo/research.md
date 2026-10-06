# Investigación (Fase 0): Pruebas de Integración Keycloak + Catálogo

Todas las incógnitas del Contexto Técnico quedan resueltas; no hay `NEEDS CLARIFICATION` pendientes. Los hechos sobre el código se verificaron leyendo `Program.cs`, `appsettings*.json`, `ApplicationModule*.cs`, `BacklogApiFactory.cs` y `PostgresFixture.cs`.

## R1. Cómo aprovisionar Keycloak en pruebas
- **Decisión**: `Testcontainers.Keycloak` 4.1.0 con imagen `quay.io/keycloak/keycloak:24.0` y realm importado desde fichero versionado.
- **Justificación**: reproducible, sin estado manual (FR-014, SC-005), un solo comando (SC-006). Es el proveedor que fija la Constitución (Keycloak v24+) y la misma línea 4.x de Testcontainers que ya usa `Testcontainers.PostgreSql` 4.1.0.
- **Alternativas**: Keycloak de `docker-compose` (estado compartido, viola FR-014); servidor OIDC falso o JWT con clave local (reintroduce simulación, viola FR-001/FR-012); aprovisionar por Admin API (más código imperativo y más puntos de fallo).

## R2. Cómo hacer pasar la verificación de audiencia sin relajarla
- **Hallazgo**: Keycloak emite por defecto `aud=account`. El host exige `aud=techworkhub-api` (`resource` + `verify-token-audience: true`).
- **Decisión**: el realm importado define un *Audience mapper* en el cliente de pruebas que añade `techworkhub-api` al claim `aud`. Un segundo cliente sin ese mapper produce el token de "otra audiencia".
- **Justificación**: la prueba valida la configuración de producción, no una versión relajada (FR-003).

## R3. Cómo obtener un token de "otro emisor"
- **Decisión**: segundo realm importado (`techworkhub-other`) en el mismo contenedor; su `iss` es `…/realms/techworkhub-other`, distinto del configurado.
- **Alternativa descartada**: segundo contenedor (más lento, sin ganancia).

## R4. Emisor (`iss`) y URL base
- **Hallazgo**: en modo `start-dev` Keycloak deriva el `iss` del host de la solicitud. Los tokens deben pedirse con la misma URL base que se inyecta en `Keycloak:auth-server-url`.
- **Decisión**: la fixture expone una única `BaseAddress` (obtenida del contenedor), usada tanto para pedir tokens como para configurar el host. Sin puertos fijos.

## R5. `ssl-required` frente a HTTP
- **Hecho**: `appsettings.json` base trae `ssl-required: external`; `appsettings.Development.json` ya relaja el valor solo por entorno y `KeycloakConfigurationTests` (HU-001) protege que la base no se relaje.
- **Decisión**: la fábrica de esta suite sobrescribe por `UseSetting` únicamente `Keycloak:auth-server-url` y `Keycloak:ssl-required=none`. Una prueba de guardia (`ProductionConfigGuardTests`) lee la configuración efectiva del host y exige `verify-token-audience=true`, `realm=techworkhub` y `resource=techworkhub-api`.
- **Riesgo a validar en implementación** (spike de la primera tarea): confirmar si la librería 2.5.2 realmente rechaza metadata HTTP con `external`. No pude verificarlo con la documentación del paquete (solo dice "Require HTTPS"). Si `external` funciona con `localhost`, se elimina la sobrescritura y con ella la excepción.

## R6. Credencial expirada
- **Decisión**: cliente `techworkhub-tests-shortlived` con `access.token.lifespan=1` y espera activa acotada hasta que el claim `exp` del propio token quede en el pasado; no se manipula `TimeProvider` ni el reloj.
- **Justificación**: la expiración la decide el servidor real y el rechazo lo hace el host real.

## R7. Firma alterada y cabecera ausente
- **Decisión**: se parte de un token válido y se muta un carácter del segmento de firma manteniendo base64url válido. Cabecera ausente: solicitud sin `Authorization`.

## R8. Aislamiento de datos e idempotencia
- **Decisión**: un contenedor PostgreSQL por suite, BD nueva por prueba (patrón `PostgresFixture` de HU-001, replicado en el proyecto nuevo, ADR-003). Los contenedores se destruyen al terminar. Una prueba de idempotencia ejecuta el mismo escenario sobre dos fábricas distintas y compara resultados.
- **Verificación de "sin efectos" (FR-010/011)**: conteo de filas antes y después mediante `ApplicationDbContext` y `BacklogDbContext` (sin SQL cross-schema).

## R9. Acceso a tipos del módulo Application
- **Hecho**: `ApplicationDbContext`, `RegisteredApplication.Create(Guid, string)` y `ApplicationModuleApi` son `public`; no se necesita `InternalsVisibleTo`.
- **Decisión**: la suite referencia `Api.csproj` (que arrastra Backlog y Application), como ya hace `Backlog.IntegrationTests`.
- **Prueba de "catálogo real"** (US1, escenario 2): resolver `IApplicationModuleApi` del host y afirmar que su tipo concreto es `Application.ApplicationModuleApi`.

## R10. Fallo explícito ante infraestructura ausente
- **Decisión**: las fixtures no capturan excepciones de `StartAsync`; se envuelven con un `CancellationTokenSource` de timeout configurable y un mensaje que nombra el componente (Docker, Keycloak o PostgreSQL). Sin `Skip`/`SkippableFact`.

## R11. Reintento acotado del primer token
- **Decisión**: tras `StartAsync`, el primer token se pide con reintento acotado (p. ej. 10 intentos × 1 s) para absorber el final de la importación del realm. Fuera de ese punto no hay reintentos.

## R12. Qué no se hace
- No hay semilla reproducible del catálogo como capacidad (fuera de alcance, derivada al PM).
- No se prueban roles ni se modifican contratos HTTP de HU-001.
