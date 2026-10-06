---

description: "Lista de tareas para la feature 002: Pruebas de integración contra Keycloak real y catálogo real del módulo Application"
---

# Tareas: Pruebas de Integración contra Keycloak Real y Catálogo Real del Módulo Application

**Input**: Documentos de diseño en `specs/002-pruebas-integracion-keycloak-catalogo/`

**Prerrequisitos**: plan.md, spec.md, research.md, data-model.md, contracts/test-contract.md, quickstart.md

**Tests**: Esta feature **es** un proyecto de pruebas (`Identity.IntegrationTests`); cada historia entrega casos de prueba como producto principal. No hay código de producción nuevo: `app/backend/src/**` es solo lectura (FR-013).

**Organización**: Tareas agrupadas por historia de usuario para implementación y validación independientes.

## Formato: `[ID] [P?] [Story] Descripción`

- **[P]**: Paralelizable (archivos distintos, sin dependencias pendientes)
- **[Story]**: Historia a la que pertenece (US1, US2, US3)
- Todas las rutas son relativas a la raíz del repositorio

## Convenciones de ruta

- Proyecto nuevo: `app/backend/tests/Integration/Identity/` (en adelante `<Identity>/`)
- Namespace raíz: `Integration.Identity`
- Nombres de pruebas: `Metodo_Condicion_Resultado`
- Prohibido en `<Identity>/` (FR-012, SC-002): `TestAuthHandler`, `FakeApplicationCatalog`, `RemoveAll<`, `Skip =`, `SkippableFact`, `Backlog.IntegrationTests`, `ConfigureTestServices` para autenticación o catálogo

---

## Fase 1: Setup (Infraestructura compartida)

**Propósito**: Crear el proyecto de pruebas y los artefactos estáticos (realms).

- [X] T001 Crear `<Identity>/Identity.IntegrationTests.csproj` (`net8.0`, `Nullable` y `ImplicitUsings` enable, `IsPackable=false`, `RootNamespace=Integration.Identity`) con `Microsoft.NET.Test.Sdk` 17.11.1, `xunit` 2.9.2, `xunit.runner.visualstudio` 2.8.2, `FluentAssertions` 6.12.2, `Microsoft.AspNetCore.Mvc.Testing` 8.0.11, `Testcontainers.PostgreSql` 4.1.0, `Testcontainers.Keycloak` 4.1.0, `Microsoft.IdentityModel.JsonWebTokens`, y `ProjectReference` a `..\..\..\src\Bootstrapper\Api\Api.csproj`; copiar la estructura de `app/backend/tests/Integration/Backlog/Backlog.IntegrationTests.csproj`
- [X] T002 Añadir `Identity.IntegrationTests.csproj` a `app/backend/TechWorkHub.sln` (`dotnet sln app/backend/TechWorkHub.sln add ...`) y comprobar que `dotnet build app/backend/TechWorkHub.sln` compila
- [X] T003 [P] Crear `<Identity>/Realm/techworkhub-test-realm.json` (realm `techworkhub`): cliente `techworkhub-api` (recurso destino); clientes públicos con *direct access grants* `techworkhub-tests` (con *Audience mapper* que añade `techworkhub-api` al claim `aud`), `techworkhub-tests-noaud` (sin audience mapper) y `techworkhub-tests-shortlived` (como `techworkhub-tests` con atributo `access.token.lifespan=1`); usuario `qa.user` habilitado, con contraseña de prueba, sin roles, sin acciones requeridas
- [X] T004 [P] Crear `<Identity>/Realm/techworkhub-other-realm.json` (realm `techworkhub-other`): cliente público `techworkhub-tests` con *direct access grants* y *Audience mapper* → `techworkhub-api`, y usuario `qa.user` equivalente
- [X] T005 Configurar en `Identity.IntegrationTests.csproj` que `Realm\*.json` se copie al directorio de salida (`<Content Include="Realm\*.json" CopyToOutputDirectory="PreserveNewest" />`)

---

## Fase 2: Fundacional (Prerrequisitos bloqueantes)

**Propósito**: Fixtures, fábrica del host real y utilidades que TODAS las historias necesitan.

**⚠️ CRÍTICO**: Ninguna historia puede empezar hasta completar esta fase.

- [X] T006 [P] Implementar `<Identity>/Fixtures/PostgresFixture.cs` (`IAsyncLifetime`): contenedor `postgres:16-alpine` con `Testcontainers.PostgreSql`, `CreateDatabaseAsync()` que devuelve la cadena de conexión de una BD nueva y vacía por prueba; arranque envuelto en `CancellationTokenSource` con timeout leído de `IDENTITY_TESTS_STARTUP_TIMEOUT_SECONDS` (defecto 120) y excepción cuyo mensaje nombra "PostgreSQL/Docker"; sin capturar excepciones de `StartAsync` (R10). Replicar el patrón de `app/backend/tests/Integration/Backlog/PostgresFixture.cs` sin referenciar ese proyecto (ADR-003)
- [X] T007 [P] Implementar `<Identity>/Fixtures/KeycloakFixture.cs` (`IAsyncLifetime`): contenedor `quay.io/keycloak/keycloak:24.0` con `Testcontainers.Keycloak`, importando ambos realms de `Realm/`; expone `BaseAddress` única (misma URL para pedir tokens y para configurar el host, R4, sin puertos fijos) y `GetTokenAsync(variante)` por *password grant* para las variantes Válida, Expirada (cliente `techworkhub-tests-shortlived`), OtroEmisor (`techworkhub-other`) y OtraAudiencia (`techworkhub-tests-noaud`); primer token con reintento acotado (10 intentos × 1 s, R11); timeout configurable y fallo explícito que nombra "Keycloak" (D7, CB-05)
- [X] T008 Spike de `ssl-required` (R5/D4): con `KeycloakFixture` arrancado, verificar si `Keycloak.AuthServices.Authentication` 2.5.2 con `ssl-required=external` acepta el Keycloak HTTP de `localhost`; documentar el resultado en un comentario de `<Identity>/Fixtures/RealApiFactory.cs` y decidir si la sobrescritura `Keycloak:ssl-required=none` es necesaria (depende de T007)
- [X] T009 Implementar `<Identity>/Fixtures/RealApiFactory.cs` (`WebApplicationFactory<Program>`): hospeda el `Program` real; inyecta por `UseSetting` solo `ConnectionStrings:Database`, `Database:MigrateOnStartup=true`, `Keycloak:auth-server-url` (= `KeycloakFixture.BaseAddress`) y, solo si T008 lo exige, `Keycloak:ssl-required=none`; NO toca `verify-token-audience`, `realm` ni `resource`; sin `ConfigureTestServices` ni `RemoveAll<`. Expone `StoredItemsAsync()` (lee `BacklogDbContext` desde `Services.CreateScope()` con `AsNoTracking()`), `ApplicationCountAsync()` (lee `ApplicationDbContext`) y `SeedApplicationsAsync(...)` (depende de T006, T008)
- [X] T010 [P] Implementar `<Identity>/Support/CatalogSeeder.cs`: crea aplicaciones con `RegisteredApplication.Create(Guid id, string name)` (`Name` máx. 200) y las guarda con `ApplicationDbContext` resuelto desde un scope del host; devuelve los `Guid` generados (FR-004). Sin SQL cross-schema
- [X] T011 [P] Implementar `<Identity>/Support/TokenTamperer.cs`: toma un JWT válido y devuelve otro con un carácter del segmento de firma mutado manteniendo base64url válido (R7); incluir comprobación interna de que el token sigue teniendo tres segmentos
- [X] T012 Implementar `<Identity>/Fixtures/IdentityCollection.cs`: `[CollectionDefinition("Identity")]` con `ICollectionFixture<KeycloakFixture>` e `ICollectionFixture<PostgresFixture>`; ejecución secuencial contra el mismo Keycloak (D8)

**Checkpoint**: Infraestructura lista; las historias pueden comenzar.

---

## Fase 3: Historia de Usuario 1 — Consulta del catálogo con identidad real (Prioridad: P1) 🎯 MVP

**Objetivo**: Listar aplicaciones con un JWT real de Keycloak contra el catálogo real y PostgreSQL migrado.

**Prueba independiente**: Crear aplicaciones con `CatalogSeeder`, pedir un token válido y llamar `GET /api/applications`: 200 con exactamente las aplicaciones creadas, ordenadas por `name`.

### Pruebas de la Historia 1

- [X] T013 [US1] Crear `<Identity>/ListApplicationsRealTests.cs` (`[Collection("Identity")]`) con `ListarAplicaciones_ConCredencialValida_Devuelve200ConAplicacionesOrdenadas`: siembra al menos 3 aplicaciones con nombres desordenados, `GET /api/applications` con `Authorization: Bearer <token válido>`, afirma HTTP 200, que la lista contiene exactamente las creadas (cada una con `id` y `name`) y que está ordenada ascendentemente por `name` (FR-005, SC-001)
- [X] T014 [US1] En `<Identity>/ListApplicationsRealTests.cs` añadir `Catalogo_EnHostReal_EsImplementacionRealDelModuloApplication`: resuelve `IApplicationModuleApi` desde `Services` del host y afirma que su tipo concreto es `Application.ApplicationModuleApi` (R9, US1 escenario 2, FR-002)
- [X] T015 [US1] En `<Identity>/ListApplicationsRealTests.cs` añadir `ListarAplicaciones_SinAplicacionesCreadas_Devuelve200ConListaVacia` sobre una BD nueva (comprueba aislamiento por prueba, FR-014)

**Checkpoint**: US1 funcional y verificable por sí sola (MVP).

---

## Fase 4: Historia de Usuario 2 — Registro de ítem con aplicación real (Prioridad: P1)

**Objetivo**: Verificar que `POST /api/backlog/items` resuelve `applicationId` contra el catálogo real y registra `CreatedBy == sub` del token real.

**Prueba independiente**: Con aplicación sembrada y token válido, `POST /api/backlog/items` devuelve 201 y el ítem persistido tiene `Status=Backlog`, `ApplicationId` correcto y `CreatedBy` igual al `sub` del token.

### Pruebas de la Historia 2

- [X] T016 [US2] Crear `<Identity>/CreateBacklogItemRealTests.cs` (`[Collection("Identity")]`) con `RegistrarItem_ConCredencialRealYAplicacionExistente_Devuelve201`: payload válido de HU-001 `{"title":"…","type":"UserStory","priority":"High","devPoints":5.0,"qaPoints":3.0,"applicationId":"<guid sembrado>"}`; afirma HTTP 201, cabecera `Location` = `/api/backlog/items/{id}` y cuerpo `{ "id": Guid }` (FR-006)
- [X] T017 [US2] En `<Identity>/CreateBacklogItemRealTests.cs` añadir `RegistrarItem_ConCredencialReal_PersisteCreatedByIgualAlSub`: lee `sub` del token con `Microsoft.IdentityModel.JsonWebTokens.JsonWebToken` y afirma, vía `StoredItemsAsync()`, un único ítem con `Status=Backlog`, `ApplicationId` sembrado y `CreatedBy == sub` (FR-007, FR-011, SC-004)
- [X] T018 [US2] En `<Identity>/CreateBacklogItemRealTests.cs` añadir `RegistrarItem_ConApplicationIdInexistente_Devuelve400SinPersistir`: credencial válida y `Guid` no sembrado; afirma HTTP 400 `ProblemDetails` con la clave `ApplicationId` en `errors` y cero ítems persistidos (FR-008)

**Checkpoint**: US1 y US2 funcionan de forma independiente.

---

## Fase 5: Historia de Usuario 3 — Rechazo de credenciales inválidas (Prioridad: P2)

**Objetivo**: Verificar 401 en ambas rutas para las 5 credenciales inválidas (10 combinaciones) sin efectos en catálogo ni persistencia.

**Prueba independiente**: Para cada combinación ruta × credencial inválida, la respuesta es 401 y los conteos de filas de catálogo e ítems no cambian.

### Pruebas de la Historia 3

- [X] T019 [US3] Crear `<Identity>/InvalidCredentialsTests.cs` (`[Collection("Identity")]`) con `[Theory]` y `[MemberData]`/`[InlineData]` sobre las 5 variantes (`Ausente`, `FirmaAlterada`, `Expirada`, `OtroEmisor`, `OtraAudiencia`) × 2 rutas (`GET /api/applications`, `POST /api/backlog/items` con payload válido de HU-001), produciendo exactamente 10 casos; cada caso afirma HTTP 401 (FR-009, SC-003)
- [X] T020 [US3] En `<Identity>/InvalidCredentialsTests.cs` implementar la construcción de cada credencial: `Ausente` sin cabecera `Authorization`; `FirmaAlterada` con `TokenTamperer` (T011) sobre un token válido; `Expirada` con el cliente `techworkhub-tests-shortlived` esperando con espera activa acotada hasta que el claim `exp` leído del propio token quede en el pasado, sin manipular el reloj del host (R6/D2); `OtroEmisor` con `techworkhub-other`; `OtraAudiencia` con `techworkhub-tests-noaud`
- [X] T021 [US3] En `<Identity>/InvalidCredentialsTests.cs` verificar en cada caso "sin efectos" (FR-010, FR-011): sembrar aplicaciones antes, y comprobar tras la respuesta que `ApplicationCountAsync()` y `StoredItemsAsync().Count` no cambiaron (cero ítems en las rutas POST)

**Checkpoint**: Las tres historias funcionan de forma independiente.

---

## Fase 6: Guardias, idempotencia y pulido

**Propósito**: Invariantes transversales (FR-003, FR-012, FR-013, FR-014, SC-005) y validación final.

- [X] T022 [P] Crear `<Identity>/ProductionConfigGuardTests.cs` (`[Collection("Identity")]`): `ConfiguracionEfectiva_MantieneAudienciaYEmisorDeProduccion` lee `IConfiguration` del host real y falla si `Keycloak:verify-token-audience` ≠ `true`, `Keycloak:realm` ≠ `techworkhub` o `Keycloak:resource` ≠ `techworkhub-api` (FR-003, D4)
- [X] T023 [P] En `<Identity>/ProductionConfigGuardTests.cs` añadir `Suite_NoUsaSimuladosDeAutenticacionNiCatalogo`: recorre los `*.cs` de `<Identity>/` (excluyendo el propio archivo de guardia) y falla si aparece alguno de `TestAuthHandler`, `FakeApplicationCatalog`, `RemoveAll<`, `Skip =`, `SkippableFact`, `Backlog.IntegrationTests` (FR-012, SC-002)
- [X] T024 [P] Crear `<Identity>/IdempotencyTests.cs` (`[Collection("Identity")]`): `EscenarioDeRegistro_EjecutadoEnDosFabricas_ProduceElMismoResultado` ejecuta siembra + `POST` válido sobre dos `RealApiFactory` con BD distintas y compara código de estado y número de ítems persistidos (FR-014, SC-005)
- [X] T025 Ejecutar `dotnet test app/backend/tests/Integration/Identity/Identity.IntegrationTests.csproj` y confirmar que todas las pruebas pasan (≈ 2 + 1 + 3 + 10 + 3 casos) (quickstart escenarios 1-2)
- [X] T026 Ejecutar `dotnet test app/backend/TechWorkHub.sln` y confirmar que el resto de suites (incluida `Backlog.IntegrationTests`) siguen en verde (SC-006)
- [X] T027 [P] Verificar producción intacta: `git diff --stat main -- app/backend/src` sin cambios (FR-013, quickstart escenario 6)
- [ ] T028 [P] Verificar el fallo explícito sin Docker (CB-05, quickstart escenario 4) y que `docker ps -a` no muestra contenedores residuales tras dos ejecuciones consecutivas (quickstart escenario 3)
  - Nota: verificado `docker ps -a` sin residuales (solo el reaper Ryuk de Testcontainers) y el fallo explícito por timeout que nombra "Keycloak"; falta probar con el daemon de Docker detenido.
  - **DIFERIDA (04-10-2026, decisión humana):** queda abierta como ejecución manual, igual que T017 de HU-001.
- [X] T029 Prueba anti-tautología (quickstart escenario 7): quitar temporalmente el *audience mapper* de `techworkhub-tests` en `<Identity>/Realm/techworkhub-test-realm.json`, comprobar que las pruebas de camino feliz fallan con 401, y restaurar el realm
- [X] T030 Registrar en el PR la excepción acotada de `ssl-required=none` (si T008 la confirmó) para revisión de QA-Tech, según Complexity Tracking de `specs/002-pruebas-integracion-keycloak-catalogo/plan.md`
  - Nota: excepción confirmada por el spike T008 (documentada en `backend-architecture.md` y `RealApiFactory.cs`); pendiente de citarla en el PR.

---

## Dependencias y orden de ejecución

### Dependencias entre fases

- **Setup (Fase 1)**: sin dependencias.
- **Fundacional (Fase 2)**: depende de Fase 1; BLOQUEA todas las historias.
- **Historias (Fases 3-5)**: dependen de la Fase 2; son independientes entre sí.
- **Pulido (Fase 6)**: T022-T024 dependen de la Fase 2; T025-T030 dependen de las historias deseadas.

### Dependencias de tareas

- T002 → T001; T005 → T001, T003, T004
- T007 → T003, T004, T005; T008 → T007; T009 → T006, T008
- T012 → T006, T007
- T013-T015, T016-T018 y T019-T021 → T009, T010, T012 (T020 además → T011)
- T014 y T015 → T013 (mismo archivo); T017 y T018 → T016; T020 y T021 → T019

### Orden por historia

- Cada historia: archivo de pruebas con el caso principal primero, luego los casos adicionales del mismo archivo.
- Una historia se valida con su propio filtro: `dotnet test ... --filter "FullyQualifiedName~ListApplicationsRealTests"`.

---

## Oportunidades de paralelismo

- Setup: T003 ∥ T004.
- Fundacional: T006 ∥ T007 ∥ T010 ∥ T011 (archivos distintos); T008/T009/T012 secuenciales.
- Tras la Fase 2, las tres historias pueden trabajarse en paralelo (archivos distintos), aunque en ejecución comparten una única `[Collection]` y corren en serie.
- Pulido: T022 ∥ T023 ∥ T024; T027 ∥ T028.

### Ejemplo paralelo: Fase 2

```text
Tarea: "PostgresFixture en app/backend/tests/Integration/Identity/Fixtures/PostgresFixture.cs"
Tarea: "KeycloakFixture en app/backend/tests/Integration/Identity/Fixtures/KeycloakFixture.cs"
Tarea: "CatalogSeeder en app/backend/tests/Integration/Identity/Support/CatalogSeeder.cs"
Tarea: "TokenTamperer en app/backend/tests/Integration/Identity/Support/TokenTamperer.cs"
```

---

## Estrategia de implementación

### MVP primero (solo Historia 1)

1. Fase 1: Setup. 2. Fase 2: Fundacional (incluye el spike T008). 3. Fase 3: US1. 4. **DETENER y VALIDAR**: `GET /api/applications` con JWT real devuelve 200 sobre el catálogo real.

### Entrega incremental

1. Setup + Fundacional → infraestructura lista.
2. US1 → validar (MVP: cierra el riesgo de catálogo simulado).
3. US2 → validar (cierra identidad real y `CreatedBy`).
4. US3 → validar (matriz 5 × 2 de 401).
5. Fase 6 → guardias, idempotencia y verificación final.

---

## Notas

- [P] = archivos distintos, sin dependencias pendientes.
- No modificar `app/backend/src/**` (FR-013) ni `app/backend/tests/Integration/Backlog/**`.
- Los fallos de infraestructura (Docker, Keycloak, PostgreSQL) deben hacer fallar la suite, nunca omitirla.
- Hacer commit tras cada tarea o grupo lógico.
