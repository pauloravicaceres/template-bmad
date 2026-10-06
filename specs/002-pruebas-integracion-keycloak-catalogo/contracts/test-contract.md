# Contrato de Pruebas (Fase 1): Pruebas de Integración Keycloak + Catálogo

La historia **no expone interfaces nuevas**. Este contrato fija (a) los contratos HTTP de HU-001 que la suite verifica sin modificarlos y (b) el contrato interno de las fixtures. Los contratos de origen están en `specs/001-registro-backlog-multitipo/contracts/api.md`.

## 1. Contratos HTTP verificados

### `GET /api/applications` (autenticada)
| Credencial | Respuesta | Cuerpo |
|---|---|---|
| Válida | `200` | Lista JSON de `{ "id": Guid, "name": string }`, solo las aplicaciones creadas por la suite, ordenada por `name`. |
| Ausente / firma alterada / expirada / otro emisor / otra audiencia | `401` | Sin cuerpo de negocio. No se consulta el catálogo. |

### `POST /api/backlog/items` (autenticada)
| Escenario | Respuesta | Verificación adicional |
|---|---|---|
| Credencial válida + `applicationId` existente + payload válido de HU-001 | `201`, `Location: /api/backlog/items/{id}`, `{ "id": Guid }` | Ítem persistido con `Status=Backlog`, `ApplicationId` correcto y `CreatedBy == sub` del token. |
| Credencial válida + `applicationId` inexistente | `400` `ProblemDetails` con clave `ApplicationId` en `errors` | Cero ítems persistidos. |
| Credencial ausente / firma alterada / expirada / otro emisor / otra audiencia | `401` | Cero ítems persistidos; catálogo no consultado. |

Payload válido de referencia (HU-001): `{"title":"…","type":"UserStory","priority":"High","devPoints":5.0,"qaPoints":3.0,"applicationId":"<guid>"}`.

## 2. Contrato de fixtures

| Componente | Responsabilidad | Garantías |
|---|---|---|
| `KeycloakFixture` (`IAsyncLifetime`) | Arranca Keycloak 24 con los dos realms importados; expone `BaseAddress` y `GetTokenAsync(variante)`. | Un contenedor por suite; falla explícitamente si no arranca en el timeout; reintento acotado solo en el primer token. |
| `PostgresFixture` (`IAsyncLifetime`) | Arranca PostgreSQL 16; `CreateDatabaseAsync()` devuelve una BD nueva y vacía. | Un contenedor por suite; una BD por prueba. |
| `RealApiFactory` (`WebApplicationFactory<Program>`) | Hospeda el `Program` real; inyecta solo `ConnectionStrings:Database`, `Database:MigrateOnStartup=true`, `Keycloak:auth-server-url` y `Keycloak:ssl-required=none`. | No usa `ConfigureTestServices` para autenticación ni catálogo. Expone `StoredItemsAsync()`, `ApplicationCountAsync()` y `SeedApplicationsAsync(...)`. |
| `IdentityCollection` | `[CollectionDefinition]` con ambas fixtures. | Ejecución secuencial contra el mismo Keycloak. |

## 3. Invariantes comprobables por revisión (SC-002, FR-012)
Búsqueda sin resultados en `tests/Integration/Identity/` de: `TestAuthHandler`, `FakeApplicationCatalog`, `RemoveAll<`, `Skip =`, `SkippableFact`, `Backlog.IntegrationTests`.
