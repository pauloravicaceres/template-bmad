# Plan de Implementación: Pruebas de Integración contra Keycloak Real y Catálogo Real del Módulo Application

**Branch**: `feat/002-HU_pruebas_integracion_keycloak_y_catalogo_application` | **Date**: 2026-10-03 | **Spec**: [spec.md](./spec.md)

**Input**: Especificación de feature desde `specs/002-pruebas-integracion-keycloak-catalogo/spec.md` y guía técnica `documents/solutions-architect/002-HU_pruebas_integracion_keycloak_y_catalogo_application.md` (ADR-001..005).

## Resumen

La historia no añade funcionalidad de producto: añade un proyecto de pruebas de integración nuevo (`Identity.IntegrationTests`) que levanta el `Program` real del Bootstrapper con la configuración de producción (audiencia verificada), un **Keycloak 24 real y efímero** (Testcontainers, realm importado) y **PostgreSQL 16 real** con migraciones aplicadas. Verifica de extremo a extremo `GET /api/applications` y `POST /api/backlog/items` con JWT reales, el origen de `CreatedBy` (`sub`) y las 10 combinaciones ruta × credencial inválida (HTTP 401). El código de producción (`src/**`) no se modifica (FR-013).

## Contexto Técnico

**Lenguaje/Versión**: C# 12 / .NET 8 (`net8.0`), igual que el resto de la solución.

**Dependencias Principales**: `Microsoft.AspNetCore.Mvc.Testing` 8.0.11 (`WebApplicationFactory<Program>`), `Testcontainers.PostgreSql` 4.1.0, `Testcontainers.Keycloak` 4.1.0 (misma línea 4.x), `Microsoft.IdentityModel.JsonWebTokens` (leer y alterar tokens), xUnit 2.9.2, FluentAssertions 6.12.2. Host bajo prueba: Carter, MediatR, `Keycloak.AuthServices.Authentication` 2.5.2.

**Storage**: PostgreSQL 16 (`postgres:16-alpine`) por Testcontainers; una base de datos nueva por prueba; schemas `application` y `backlog` aislados; migraciones existentes por `Database:MigrateOnStartup=true`. Sin migraciones nuevas.

**Testing**: xUnit; clases de prueba por escenario más fixtures. Un solo comando: `dotnet test app/backend/TechWorkHub.sln`.

**Target Platform**: Windows/Linux con demonio Docker activo (único requisito de entorno).

**Project Type**: Proyecto de pruebas de integración dentro de un Modular Monolith (web-service); sin frontend.

**Performance Goals**: N/A (no se mide rendimiento de producción). Presupuesto operativo: arranque de contenedores ≤ 120 s (configurable por variable de entorno `IDENTITY_TESTS_STARTUP_TIMEOUT_SECONDS`).

**Constraints**: FR-012 (sin `TestAuthHandler`, `FakeApplicationCatalog`, `RemoveAll<`); FR-003 (`verify-token-audience: true` y validación de emisor intactas); sin consultas cross-schema ni siquiera para verificar; fallo explícito si falta Docker/Keycloak (CB-05, sin `Skip`).

**Scale/Scope**: 3 historias, 14 requisitos funcionales, ~16 casos de prueba (2 + 3 + 10 combinaciones, más guardias e idempotencia).

## Constitution Check

*GATE: pasa antes de Fase 0; re-evaluado tras Fase 1.*

| Regla de la Constitución | Estado | Evidencia |
|---|---|---|
| Idioma español en entregables | ✅ | Todo el contenido en español; nombres de pruebas `Metodo_Condicion_Resultado`. |
| Rutas físicas bajo `app/backend/` | ✅ | Proyecto en `app/backend/tests/Integration/Identity/`. |
| Keycloak v24+ y `Keycloak.AuthServices.Authentication` 2.5.2 | ✅ | Imagen `quay.io/keycloak/keycloak:24.0`; host sin cambios (ADR-001). |
| PostgreSQL con schemas aislados, sin queries cross-schema | ✅ | Datos de catálogo por `ApplicationDbContext`; verificación de ítems por `BacklogDbContext` (ADR-002). |
| Carter, MediatR, FluentValidation, Mapster en producción | ✅ N/A | Producción solo lectura; sin código nuevo de producción. |
| Vertical Slicing / un solo HU activo | ✅ | HU-001 fusionada; HU-002 es la única activa. |
| Prohibido AutoMapper y `[ApiController]` | ✅ | No se introduce ninguno. |
| Relajación de seguridad solo con excepción explícita | ⚠️ Excepción acotada | `ssl-required: none` solo en el host de prueba, por el Keycloak HTTP de Testcontainers (Decisión D4). No relaja audiencia ni emisor. Requiere revisión de QA-Tech (ya exigida en la guía del SA §8). |

**Resultado del gate**: PASA. La única desviación es la excepción acotada de `ssl-required`, registrada en *Complexity Tracking*.

**Re-evaluación post-diseño**: PASA sin cambios; el diseño de Fase 1 no introduce nuevas desviaciones.

## Decisiones de planificación (puntos que la guía del SA delegó al plan)

| # | Punto | Decisión |
|---|---|---|
| D1 | Nombres de realm, clientes y usuario | Realm `techworkhub` (mismo del host). Clientes: `techworkhub-api` (recurso del host), `techworkhub-tests` (público, *direct access grants*, con audience mapper), `techworkhub-tests-noaud` (sin audience mapper → otra audiencia), `techworkhub-tests-shortlived` (`access.token.lifespan=1` s → expirado). Usuario `qa.user` con contraseña de prueba solo en el realm versionado. Segundo realm `techworkhub-other` con cliente y usuario equivalentes (otro emisor). Detalle en [data-model.md](./data-model.md). |
| D2 | Credencial expirada | Se emite con el cliente de vida corta y se espera a que `exp` quede en el pasado (comprobado leyendo el claim); no se manipula el reloj del host. |
| D3 | Firma alterada y cabecera ausente | Se derivan en la prueba a partir de un token válido (firma mutada) o sin cabecera. |
| D4 | `ssl-required` con Keycloak HTTP | La fábrica sobrescribe por `UseSetting` solo `Keycloak:auth-server-url` y `Keycloak:ssl-required=none`; **no** se toca `verify-token-audience`, `realm` ni `resource`. Una prueba de guardia lee la configuración efectiva del host y falla si `verify-token-audience` ≠ `true`. Se valida en el spike de la primera tarea si la sobrescritura es realmente necesaria (ver research R5). |
| D5 | Acceso a `ApplicationDbContext` | Es `public` en `Application.Data`; no hace falta `InternalsVisibleTo`. Se resuelve desde `Services.CreateScope()` del host de prueba. |
| D6 | Roles | HU-001 solo exige `sub`; no se verifican roles (spec, Assumptions). |
| D7 | Servidor de identidad no disponible | Fallo explícito en `InitializeAsync` de las fixtures; sin `Skip` ni traits de exclusión (CB-05, ADR-005). |
| D8 | Aislamiento | Un contenedor Keycloak y uno PostgreSQL por suite (`ICollectionFixture`), base de datos nueva por prueba, una única `[Collection]` para no paralelizar contra el mismo Keycloak. |

## Project Structure

### Documentación (esta feature)

```text
specs/002-pruebas-integracion-keycloak-catalogo/
├── plan.md              # Este archivo (/speckit-plan)
├── research.md          # Fase 0
├── data-model.md        # Fase 1 (entidades de prueba y realm)
├── quickstart.md        # Fase 1 (guía de validación)
├── contracts/
│   └── test-contract.md # Fase 1 (contratos HTTP verificados + contrato de fixtures)
├── checklists/
│   └── requirements.md
└── tasks.md             # Fase 2 (/speckit-tasks; NO lo crea este comando)
```

### Código Fuente (raíz del repositorio)

```text
app/backend/
├── TechWorkHub.sln                              # se añade Identity.IntegrationTests
├── src/                                         # SOLO LECTURA (FR-013)
└── tests/
    └── Integration/
        ├── Backlog/                             # HU-001, intacto
        └── Identity/                            # NUEVO
            ├── Identity.IntegrationTests.csproj
            ├── Realm/
            │   ├── techworkhub-test-realm.json        # realm principal importado
            │   └── techworkhub-other-realm.json       # realm de "otro emisor"
            ├── Fixtures/
            │   ├── KeycloakFixture.cs                 # contenedor + emisión de tokens
            │   ├── PostgresFixture.cs                 # contenedor + BD por prueba
            │   ├── RealApiFactory.cs                  # Program real, config de producción
            │   └── IdentityCollection.cs              # ICollectionFixture
            ├── Support/
            │   ├── TokenTamperer.cs                   # firma alterada
            │   └── CatalogSeeder.cs                   # crea aplicaciones vía ApplicationDbContext
            ├── ListApplicationsRealTests.cs           # US1
            ├── CreateBacklogItemRealTests.cs          # US2
            ├── InvalidCredentialsTests.cs             # US3 (matriz 5 × 2)
            ├── ProductionConfigGuardTests.cs          # FR-003 / FR-012 (guardias)
            └── IdempotencyTests.cs                    # FR-014 / SC-005
```

**Structure Decision**: proyecto de pruebas separado de `Backlog.IntegrationTests` (ADR-005) para que FR-012 sea verificable por búsqueda en un solo proyecto y para no arrancar contenedores de Keycloak con la suite rápida de HU-001. Se agrupa por escenario, no por capa. La duplicación de `PostgresFixture` (~30 líneas) es deliberada (ADR-003).

## Complexity Tracking

| Violación | Por qué es necesaria | Alternativa más simple descartada porque |
|---|---|---|
| `ssl-required: none` en el host de prueba | El Keycloak de Testcontainers sirve HTTP; con `external` el host podría rechazar la metadata por HTTP. | Configurar TLS en el contenedor añade certificados y puntos de fallo sin aportar evidencia sobre audiencia, emisor ni firma. La excepción queda acotada al proyecto de pruebas y protegida por una prueba de guardia. |
| Segundo realm (`techworkhub-other`) | Única forma de obtener un token de "otro emisor" firmado por un Keycloak real. | Firmar con clave local reintroduciría la simulación que la HU elimina (FR-001, FR-012). |
